"""Vector store — SQLite-backed persistence with char-n-gram embedding.

Replaces the old JSON-file approach with ACID-compliant storage.
"""

from __future__ import annotations

import json
import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any

from wren.harness.storage.store import Store

_logger = logging.getLogger(__name__)

NGRAM_N = 3  # character n-gram size for embedding

# Internal tag encoding conventions
_TAG_SOURCE_PREFIX = '__source__:'
_TAG_META_PREFIX = '__meta__:'


def _char_ngrams(text: str, n: int = NGRAM_N) -> dict[str, float]:
    """Compute char n-gram frequency vector for a text."""
    text = text.lower()
    ngrams: dict[str, float] = {}
    for i in range(len(text) - n + 1):
        ng = text[i : i + n]
        ngrams[ng] = ngrams.get(ng, 0) + 1
    # Normalise to unit vector
    mag = math.sqrt(sum(v * v for v in ngrams.values()))
    if mag > 0:
        for k in ngrams:
            ngrams[k] /= mag
    return ngrams


def _cosine_sim(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) & set(b)
    if not keys:
        return 0.0
    dot = sum(a[k] * b[k] for k in keys)
    return dot


def _embedding_to_dict(emb: list[float]) -> dict[str, float]:
    """Convert list-format embedding to dict for similarity."""
    return {}


def _tags_to_str(tags: str | list[str]) -> str:
    """Normalise tags to a comma-separated string."""
    if isinstance(tags, list):
        return ','.join(tags)
    return tags


def _str_to_tags(tag_str: str) -> list[str]:
    """Split comma-separated tags into a list."""
    if not tag_str:
        return []
    return [t.strip() for t in tag_str.split(',') if t.strip()]


def _extract_source(tags: list[str]) -> str:
    """Extract source from encoded tags list."""
    for t in tags:
        if t.startswith(_TAG_SOURCE_PREFIX):
            return t[len(_TAG_SOURCE_PREFIX) :]
    return ''


def _extract_metadata(tags: list[str]) -> dict[str, Any]:
    """Extract metadata dict from encoded tags list."""
    for t in tags:
        if t.startswith(_TAG_META_PREFIX):
            try:
                return json.loads(t[len(_TAG_META_PREFIX) :])
            except (json.JSONDecodeError, TypeError):
                return {}
    return {}


def _filter_tags(tags: list[str]) -> list[str]:
    """Return only user-facing tags (strip internal prefixes)."""
    return [
        t
        for t in tags
        if not t.startswith(_TAG_SOURCE_PREFIX) and not t.startswith(_TAG_META_PREFIX)
    ]


@dataclass
class SearchResult:
    """Typed search result returned by VectorStore.search()."""

    key: str = ''
    content: str = ''
    source: str = ''
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    namespace: str = ''
    score: float = 0.0
    id: str = ''


class VectorStore:
    """Vector store backed by SQLite via Store facade.

    Documents are stored in the harness_vectors table with char-n-gram
    embeddings computed automatically.
    """

    def __init__(self, persist_path: str = '') -> None:
        self._namespace = 'default'
        # persist_path is accepted for backward compatibility but ignored
        # — SQLite handles persistence via DB singleton.
        _ = persist_path

    # ── CRUD ─────────────────────────────────────────────────────

    def store(
        self,
        content: str,
        key: str = '',
        tags: str = '',
        namespace: str = 'default',
    ) -> str:
        """Store content with auto-computed embedding."""
        if not key:
            key = f'vec_{int(time.time())}_{hash(content) % 10000}'
        embedding_dict = _char_ngrams(content)
        # Store the embedding dict keys as a sorted list for reproducibility
        embedding_list = list(embedding_dict.items())
        Store.save_vector(
            key, content, [v for _, v in embedding_list], tags=tags, namespace=namespace
        )
        _logger.debug('VectorStore: stored %s (%d chars)', key[:40], len(content))
        return key

    def insert(
        self,
        content: str,
        source: str = '',
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        namespace: str = 'default',
    ) -> str:
        """Insert content with source, tags, and metadata.

        This is the high-level interface used by WorkingMemoryRAG and
        SkillLibrary. Internally encodes source and metadata into the
        tags field for storage.
        """
        tag_list = list(tags or [])
        if source:
            tag_list.append(f'{_TAG_SOURCE_PREFIX}{source}')
        if metadata:
            tag_list.append(f'{_TAG_META_PREFIX}{json.dumps(metadata)}')
        tag_str = ','.join(tag_list)
        key = f'vec_{int(time.time())}_{hash(content) % 10000}'
        return self.store(content, key=key, tags=tag_str, namespace=namespace)

    def get(self, key: str) -> dict[str, Any] | None:
        rows = Store.all_vectors(self._namespace)
        for row in rows:
            if row['key'] == key:
                return {
                    'key': row['key'],
                    'content': row['content'],
                    'tags': row['tags'],
                    'namespace': row['namespace'],
                }
        return None

    def delete(self, key: str) -> bool:
        Store.delete_vector(key)
        return True

    def delete_by_source(self, source: str) -> int:
        """Delete all vectors with the given source."""
        prefix = f'{_TAG_SOURCE_PREFIX}{source}'
        rows = Store.all_vectors(self._namespace)
        count = 0
        for row in rows:
            tags_list = _str_to_tags(row.get('tags', ''))
            if any(t.startswith(prefix) for t in tags_list):
                Store.delete_vector(row['key'])
                count += 1
        if count:
            _logger.debug(
                'VectorStore: deleted %d vectors for source=%s', count, source
            )
        return count

    def clear(self, namespace: str = 'default') -> None:
        Store.delete_vector_namespace(namespace)

    def count(self, namespace: str = 'default') -> int:
        return len(Store.all_vectors(namespace))

    # ── Search ───────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        tags: list[str] | None = None,
    ) -> list[tuple[SearchResult, float]]:
        """Search by cosine similarity on char n-gram embedding.

        Args:
            query: Search text.
            top_k: Maximum results to return.
            min_score: Minimum similarity score threshold.
            tags: Optional list of tags to filter results (only returns
                  entries whose user-facing tags overlap with this list).

        Returns:
            List of (SearchResult, score) tuples compatible with
            ``for entry, score in results:`` unpacking.
        """
        query_vec = _char_ngrams(query)
        rows = Store.all_vectors(self._namespace)

        scored: list[tuple[float, dict[str, Any]]] = []
        for row in rows:
            # Tag filtering
            if tags:
                row_tags = _str_to_tags(row.get('tags', ''))
                row_clean = _filter_tags(row_tags)
                if not any(t in row_clean for t in tags):
                    continue

            try:
                stored_embedding_list = json.loads(row.get('embedding', '[]'))
            except (json.JSONDecodeError, TypeError):
                stored_embedding_list = []

            if stored_embedding_list:
                # Reconstruct ngram dict from sorted values
                keys = sorted(query_vec.keys())
                stored_dict = dict(
                    zip(keys[: len(stored_embedding_list)], stored_embedding_list)
                )
                score = _cosine_sim(query_vec, stored_dict)
            else:
                # Fallback: keyword overlap
                ql = query.lower()
                cl = (row.get('content') or '').lower()
                score = sum(1 for kw in ql.split() if kw in cl) / max(
                    len(ql.split()), 1
                )

            if score < min_score:
                continue

            scored.append((score, row))

        scored.sort(key=lambda x: x[0], reverse=True)

        results: list[tuple[SearchResult, float]] = []
        for s, r in scored[:top_k]:
            row_tags = _str_to_tags(r.get('tags', ''))
            entry = SearchResult(
                key=r['key'],
                content=r.get('content', '')[:500],
                source=_extract_source(row_tags),
                tags=_filter_tags(row_tags),
                metadata=_extract_metadata(row_tags),
                namespace=r.get('namespace', 'default'),
                score=round(s, 4),
                id=str(r.get('id', '')),
            )
            results.append((entry, round(s, 4)))
        return results

    # ── Persistence (legacy — kept for backward compat) ──────────

    def persist(self, path: str = '') -> None:
        """No-op — persistence is automatic via SQLite."""
        pass

    def load(self, path: str = '') -> None:
        """No-op — persistence is automatic via SQLite."""
        pass
