"""RAG over working memory.

Retrieves relevant context from the current conversation's working
memory — recent messages, active tasks, error history, and skill
snippets — and formats them as a system-prompt suffix for the
active agent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from wren.harness.knowledge.vector_store import VectorStore

_logger = logging.getLogger(__name__)

MAX_CONTEXT_TOKENS = 4000


@dataclass
class RAGContext:
    snippets: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    total_chars: int = 0

    def to_prompt_suffix(self) -> str:
        if not self.snippets:
            return ''
        lines = ['\n### Relevant context', 'The following may be useful:']
        for i, s in enumerate(self.snippets, 1):
            lines.append(f'{i}. {s}')
        return '\n'.join(lines)


class WorkingMemoryRAG:
    """Retrieves relevant working-memory context for injection into
    the agent prompt.

    Queries the vector store using the current user message or task
    description, then formats the top matches as a context block.
    """

    def __init__(
        self, vector_store: VectorStore, max_tokens: int = MAX_CONTEXT_TOKENS
    ) -> None:
        self._vs = vector_store
        self._max_tokens = max_tokens

    # ── Public API ───────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = 5) -> RAGContext:
        """Retrieve context from working memory relevant to query."""
        results = self._vs.search(query, top_k=top_k, min_score=0.05)
        if not results:
            return RAGContext()

        ctx = RAGContext()
        for entry, score in results:
            snippet = self._format_snippet(entry, score)
            if ctx.total_chars + len(snippet) > self._max_tokens * 4:
                break
            ctx.snippets.append(snippet)
            ctx.sources.append(f'{entry.source}#{entry.id}')
            ctx.total_chars += len(snippet)

        _logger.debug('RAG: %d snippets for "%s"', len(ctx.snippets), query[:50])
        return ctx

    def retrieve_by_tags(
        self,
        tags: list[str],
        query: str = '',
        top_k: int = 3,
    ) -> RAGContext:
        """Retrieve context filtered by specific tags."""
        results = self._vs.search(
            query or ' '.join(tags), top_k=top_k, min_score=0.0, tags=tags
        )
        ctx = RAGContext()
        for entry, score in results:
            snippet = self._format_snippet(entry, score)
            ctx.snippets.append(snippet)
            ctx.sources.append(f'{entry.source}#{entry.id}')
            ctx.total_chars += len(snippet)
        return ctx

    def store(
        self,
        content: str,
        source: str = 'agent',
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store a fact into working memory."""
        self._vs.insert(
            content=content,
            source=source,
            tags=(tags or []) + ['working_memory'],
            metadata=metadata,
        )

    def clear_agent_memory(self, source: str = 'agent') -> None:
        """Clear working memory for a specific agent."""
        self._vs.delete_by_source(source)

    # ── Internal ─────────────────────────────────────────────────

    @staticmethod
    def _format_snippet(entry: Any, score: float) -> str:
        """Format a memory entry as a one-line context snippet."""
        content = entry.content[:300].replace('\n', ' | ')
        tags = ','.join(entry.tags[:3]) if entry.tags else ''
        tag_str = f' [{tags}]' if tags else ''
        return f'({entry.source}{tag_str} rel={score:.2f}) {content}'
