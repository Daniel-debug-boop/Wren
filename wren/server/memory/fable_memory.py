from __future__ import annotations
import asyncio
import hashlib  # Fixed: Missing import added
import json
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Protocol, runtime_checkable

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

try:
    from pydantic import BaseModel, Field
except ImportError:
    raise ImportError(
        'Pydantic is required for FableMemoryManager. pip install pydantic'
    )

try:
    import tiktoken

    _ENCODER = tiktoken.get_encoding('cl100k_base')

    def count_tokens(text: str) -> int:
        return len(_ENCODER.encode(text))
except ImportError:
    # Fallback heuristic if tiktoken is not installed
    def count_tokens(text: str) -> int:
        return len(text) // 4


# ---------------------------------------------------------------------------
# Domain Models
# ---------------------------------------------------------------------------
class MemoryType(str, Enum):
    PREFERENCE = 'preference'
    STACK_RULE = 'stack_rule'
    LESSON = 'lesson'
    ENTITY_FACT = 'entity_fact'


class MemoryItem(BaseModel):
    id: str = Field(default_factory=lambda: f'mem_{uuid.uuid4().hex[:12]}')
    type: MemoryType
    content: str
    key: str | None = None  # For preferences/rules
    created_at: float = Field(default_factory=time.time)
    last_accessed: float = Field(default_factory=time.time)
    access_count: int = 0
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: List[float] | None = None  # For vector search


# ---------------------------------------------------------------------------
# Embedding Protocol (The RAG component)
# ---------------------------------------------------------------------------
@runtime_checkable
class Embedder(Protocol):
    """Pluggable embedder for semantic search. Falls back to keyword matching."""

    async def embed(self, text: str) -> List[float]: ...
    def similarity(self, vec_a: List[float], vec_b: List[float]) -> float: ...


class HashingEmbedder:
    """Fast, local, dependency-free pseudo-embedder using SHA-256 hashing."""

    def __init__(self, dims: int = 256):
        self.dims = dims

    async def embed(self, text: str) -> List[float]:
        text = text.lower()
        words = set(text.split())
        vec = [0.0] * self.dims
        for word in words:
            h = int(hashlib.sha256(word.encode()).hexdigest(), 16)
            vec[h % self.dims] += 1.0
        # L2 Normalize
        norm = sum(v**2 for v in vec) ** 0.5
        return [v / norm for v in vec] if norm > 0 else vec

    def similarity(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        return dot  # Already normalized


# ---------------------------------------------------------------------------
# Storage Backends
# ---------------------------------------------------------------------------
class MemoryStore(ABC):
    """Abstract base class for memory persistence."""

    @abstractmethod
    async def load_all(self) -> List[MemoryItem]: ...

    @abstractmethod
    async def save_item(self, item: MemoryItem) -> None: ...

    @abstractmethod
    async def delete_item(self, item_id: str) -> None: ...

    @abstractmethod
    async def delete_items(self, item_ids: List[str]) -> None: ...

    @abstractmethod
    async def flush(self) -> None: ...


class LocalJSONStore(MemoryStore):
    """Atomic, async, concurrency-safe local JSON storage."""

    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self._cache: List[MemoryItem] | None = None

    async def load_all(self) -> List[MemoryItem]:
        if self._cache is not None:
            return self._cache

        async with self._lock:
            if not self.storage_path.exists():
                self._cache = []
                return []

            # Run blocking file read in executor
            def _read() -> Any:
                with open(self.storage_path, 'r') as f:
                    raw = json.load(f)
                return [MemoryItem(**item) for item in raw.get('memories', [])]

            loop = asyncio.get_event_loop()
            self._cache = await loop.run_in_executor(None, _read)
            return self._cache

    async def save_item(self, item: MemoryItem) -> None:
        async with self._lock:
            memories = self._cache or []
            # Upsert
            idx = next((i for i, m in enumerate(memories) if m.id == item.id), None)
            if idx is not None:
                memories[idx] = item
            else:
                memories.append(item)
            self._cache = memories
            await self._atomic_flush(memories)

    async def delete_item(self, item_id: str) -> None:
        async with self._lock:
            memories = self._cache or []
            self._cache = [m for m in memories if m.id != item_id]
            await self._atomic_flush(self._cache)

    async def delete_items(self, item_ids: List[str]) -> None:
        """Fixed: Batch delete to prevent O(N) I/O writes during pruning."""
        if not item_ids:
            return

        async with self._lock:
            memories = self._cache or []
            id_set = set(item_ids)
            self._cache = [m for m in memories if m.id not in id_set]
            await self._atomic_flush(self._cache)

    async def _atomic_flush(self, memories: List[MemoryItem]) -> None:
        """Writes to a temp file, then atomically replaces the target file."""

        def _write() -> None:
            data = {'memories': [m.model_dump() for m in memories]}
            tmp_path = self.storage_path.with_suffix('.tmp')
            with open(tmp_path, 'w') as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self.storage_path)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _write)

    async def flush(self) -> None:
        async with self._lock:
            if self._cache:
                await self._atomic_flush(self._cache)


# ---------------------------------------------------------------------------
# The Memory Manager
# ---------------------------------------------------------------------------
class FableMemoryManager:
    """
    Manages agent long-term memory, lesson extraction, and dynamic prompt compilation.
    """

    def __init__(
        self,
        store: MemoryStore | None = None,
        storage_path: str = '~/.wren/fable_memory.json',
        embedder: Embedder | None = None,
        max_items: int = 1000,
        token_budget: int = 2000,
    ):
        self.store = store or LocalJSONStore(storage_path)
        self.embedder = embedder or HashingEmbedder()
        self.max_items = max_items
        self.token_budget = token_budget
        self._cache: List[MemoryItem] = []

    async def initialize(self) -> None:
        """Load memory into cache on startup."""
        self._cache = await self.store.load_all()
        logger.info(f'fable_memory.loaded, count={len(self._cache)}')

    async def update_lesson(
        self, short_summary: str, tags: List[str] | None = None
    ) -> str:
        """Allows the agent loop to self-update its knowledge database."""
        # Prevent exact duplicate lessons
        existing = any(
            m.type == MemoryType.LESSON and m.content == short_summary
            for m in self._cache
        )
        if existing:
            logger.debug(
                f'fable_memory.duplicate_lesson_ignored, summary={short_summary[:50]}'
            )
            return ''

        embedding = await self.embedder.embed(short_summary)
        item = MemoryItem(
            type=MemoryType.LESSON,
            content=short_summary,
            tags=tags or [],
            embedding=embedding,
        )
        self._cache.append(item)
        await self.store.save_item(item)

        await self._prune_if_needed()
        logger.info(
            f'fable_memory.lesson_added, id={item.id}, summary={short_summary[:50]}'
        )
        return item.id

    async def set_preference(self, key: str, value: str) -> None:
        embedding = await self.embedder.embed(f'{key} {value}')
        item = MemoryItem(
            type=MemoryType.PREFERENCE, key=key, content=value, embedding=embedding
        )
        # Upsert preference
        self._cache = [
            m
            for m in self._cache
            if not (m.type == MemoryType.PREFERENCE and m.key == key)
        ]
        self._cache.append(item)
        await self.store.save_item(item)

    async def compile_system_instruction(self, context_query: str = '') -> str:
        """
        Injects dynamically into the underlying model's base system prompt.
        Uses semantic similarity to context_query to inject only relevant memories.
        """
        if not self._cache:
            return ''

        # 1. Retrieve relevant items (RAG)
        query_embedding = (
            await self.embedder.embed(context_query) if context_query else None
        )

        scored_items = []
        for item in self._cache:
            score = 0.0
            if query_embedding and item.embedding:
                score = self.embedder.similarity(query_embedding, item.embedding)

            # Boost score by recency and access frequency
            recency_boost = max(
                0, 1.0 - (time.time() - item.last_accessed) / (86400 * 7)
            )  # decays over 7 days
            freq_boost = min(0.5, item.access_count * 0.1)

            final_score = score + (recency_boost * 0.2) + (freq_boost * 0.1)
            scored_items.append((final_score, item))

        # Sort by score descending
        scored_items.sort(key=lambda x: x[0], reverse=True)

        # 2. Format and enforce token budget
        prefs, rules, lessons = [], [], []
        current_tokens = 50  # base overhead

        for score, item in scored_items:
            # Update access stats for retrieved items
            item.last_accessed = time.time()
            item.access_count += 1

            # Format line
            if item.type == MemoryType.PREFERENCE:
                line = f'- {item.key}: {item.content}'
                target = prefs
            elif item.type == MemoryType.STACK_RULE:
                line = f'- {item.key}: {item.content}'
                target = rules
            else:
                line = f'- {item.content}'
                target = lessons

            line_tokens = count_tokens(line)
            if current_tokens + line_tokens > self.token_budget:
                break

            target.append(line)
            current_tokens += line_tokens

        # Fixed: Flush access stats asynchronously with error handling
        flush_task = asyncio.create_task(self._flush_access_stats())
        flush_task.add_done_callback(
            lambda t: (
                None
                if t.cancelled()
                else (
                    logger.error(f'Background memory flush failed, {t.exception()=}')
                    if t.exception()
                    else None
                )
            )
        )

        # 3. Construct final prompt block
        prefs_str = '\n'.join(prefs) if prefs else 'None'
        rules_str = '\n'.join(rules) if rules else 'None'
        lessons_str = '\n'.join(lessons) if lessons else 'None'

        return f"""
====== CLAUDE FABLE PERSISTENT BASE MEMORY ======
You must adhere to the following historical cross-session user constraints:
Preferred Stack Rules:
{rules_str}

User Preferences:
{prefs_str}

Lessons Learned from Past Errors (Contextually Retrieved):
{lessons_str}
=================================================
"""

    async def _flush_access_stats(self) -> None:
        """Save updated access counts/timestamps back to disk."""
        # In a real high-throughput system, we'd batch this.
        # For simplicity, we just flush the whole cache.
        await self.store.flush()

    async def _prune_if_needed(self) -> None:
        """Fixed: Evict least relevant items efficiently in a single batch."""
        if len(self._cache) <= self.max_items:
            return

        # Sort by least accessed / oldest
        self._cache.sort(key=lambda m: (m.access_count, m.last_accessed))

        split_idx = len(self._cache) - self.max_items
        to_evict = self._cache[:split_idx]
        self._cache = self._cache[split_idx:]

        if to_evict:
            await self.store.delete_items([item.id for item in to_evict])
            logger.warning(f'fable_memory.pruned, evicted_count={len(to_evict)}')
