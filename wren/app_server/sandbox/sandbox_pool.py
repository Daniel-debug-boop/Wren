"""Pre-warmed sandbox pool — reduces conversation start latency.

Maintains a pool of pre-warmed sandboxes so new conversations can
start immediately without waiting for container/process creation.

Usage:
    pool = SandboxPool(sandbox_service, warm_count=2)
    await pool.warm()           # Start N sandboxes in background
    sandbox = await pool.acquire()  # Get a ready sandbox instantly
    await pool.release(sandbox_id)  # Return to pool (or discard)
    await pool.refill()         # Top up to warm_count
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

from wren.app_server.sandbox.sandbox_models import (
    SandboxInfo,
    SandboxPage,
    SandboxRecord,
    SandboxStatus,
)
from wren.app_server.sandbox.sandbox_service import SandboxService

_logger = logging.getLogger(__name__)


@dataclass
class SandboxPool:
    """Pool of pre-warmed sandboxes ready for immediate use.

    The pool maintains ``warm_count`` sandboxes in RUNNING state.
    When a sandbox is acquired, a background task refills the pool.

    If the pool is empty (e.g., during initial warm-up), ``acquire()``
    falls back to creating a fresh sandbox.
    """

    sandbox_service: SandboxService
    warm_count: int = 2
    _pool: list[SandboxInfo] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _warm_started: bool = False
    _last_refill: float = 0.0
    _refill_task: asyncio.Task | None = None

    async def warm(self) -> None:
        """Start warming the pool to ``warm_count`` sandboxes."""
        if self._warm_started:
            return
        self._warm_started = True
        _logger.info(
            "Warming sandbox pool to %d sandboxes...", self.warm_count
        )
        await self._refill()

    async def acquire(self) -> SandboxInfo:
        """Get a ready-to-use sandbox from the pool.

        If the pool has a warm sandbox, returns it immediately and
        triggers a background refill. Otherwise falls back to creating
        a new sandbox synchronously.
        """
        async with self._lock:
            if self._pool:
                sandbox = self._pool.pop(0)
                _logger.info(
                    "Acquired pre-warmed sandbox %s (%d left in pool)",
                    sandbox.id[:8],
                    len(self._pool),
                )
                # Trigger refill in background
                self._schedule_refill()
                return sandbox

        # Pool empty — fall back to synchronous create
        _logger.info("Pool empty, creating sandbox on-demand")
        sandbox = await self.sandbox_service.start_sandbox()
        sandbox = await self.sandbox_service.wait_for_sandbox_running(
            sandbox.id, timeout=120
        )
        return sandbox

    async def release(self, sandbox_id: str, keep: bool = False) -> None:
        """Return a sandbox to the pool or discard it.

        Args:
            sandbox_id: The sandbox to release.
            keep: If True, keep the sandbox in the pool (if under limit).
                  If False, delete it.
        """
        try:
            info = await self.sandbox_service.get_sandbox(sandbox_id)
            if info is None:
                return

            if keep and info.status == SandboxStatus.RUNNING:
                async with self._lock:
                    if len(self._pool) < self.warm_count:
                        self._pool.append(info)
                        _logger.info(
                            "Returned sandbox %s to pool", sandbox_id[:8]
                        )
                        return

            # Discard: delete the sandbox
            await self.sandbox_service.delete_sandbox(sandbox_id)
            _logger.info("Released sandbox %s", sandbox_id[:8])
        except Exception as e:
            _logger.warning("Error releasing sandbox %s: %s", sandbox_id[:8], e)

    async def _refill(self) -> None:
        """Top up the pool to ``warm_count``."""
        async with self._lock:
            current = len(self._pool)
            needed = self.warm_count - current

        if needed <= 0:
            return

        _logger.info("Refilling pool: need %d more sandbox(es)", needed)
        started = []
        try:
            for _ in range(needed):
                sandbox = await self.sandbox_service.start_sandbox()
                started.append(sandbox.id)
                _logger.info("  Started warming sandbox %s...", sandbox.id[:8])

            # Wait for all to become RUNNING
            for sid in started:
                try:
                    ready = await self.sandbox_service.wait_for_sandbox_running(
                        sid, timeout=120
                    )
                    async with self._lock:
                        self._pool.append(ready)
                except Exception as e:
                    _logger.warning(
                        "Failed to warm sandbox %s: %s", sid[:8], e
                    )

            self._last_refill = time.time()
            async with self._lock:
                _logger.info(
                    "Pool refilled: %d sandbox(es) ready",
                    len(self._pool),
                )
        except Exception as e:
            _logger.error("Pool refill failed: %s", e)

    def _schedule_refill(self) -> None:
        """Schedule a background refill if not already running."""
        if self._refill_task and not self._refill_task.done():
            return
        self._refill_task = asyncio.create_task(self._refill())

    async def drain(self) -> None:
        """Drain and delete all sandboxes in the pool."""
        async with self._lock:
            sandboxes = self._pool[:]
            self._pool.clear()

        for sandbox in sandboxes:
            try:
                await self.sandbox_service.delete_sandbox(sandbox.id)
            except Exception as e:
                _logger.warning(
                    "Error draining sandbox %s: %s", sandbox.id[:8], e
                )

    async def stats(self) -> dict:
        """Get pool statistics."""
        async with self._lock:
            return {
                "warm_count": self.warm_count,
                "ready": len(self._pool),
                "last_refill": self._last_refill,
                "warming": self._warm_started,
            }

    async def __aenter__(self) -> "SandboxPool":
        await self.warm()
        return self

    async def __aexit__(self, *args) -> None:
        await self.drain()


class PooledSandboxService(SandboxService):
    """Wraps a ``SandboxService`` with a pre-warmed sandbox pool.

    Delegates every method to the inner service except ``start_sandbox``,
    which first tries the pool. If the pool is empty or a specific
    ``sandbox_spec_id`` was requested, falls back to the inner service.

    Usage:
        service = PooledSandboxService(docker_service, warm_count=2)
        await service.start_sandbox()        # uses pool
        await service.get_sandbox(id)        # delegated
    """

    def __init__(
        self,
        inner: SandboxService,
        warm_count: int = 2,
    ):
        self._inner = inner
        self._pool = SandboxPool(
            sandbox_service=inner,
            warm_count=warm_count,
        )

    # ── Pool-aware start ─────────────────────────────────────────────

    async def start_sandbox(
        self,
        sandbox_spec_id: str | None = None,
        sandbox_id: str | None = None,
    ) -> SandboxInfo:
        """Start a sandbox — try the pool first for default-param starts."""
        if sandbox_spec_id is None and sandbox_id is None:
            return await self._pool.acquire()
        return await self._inner.start_sandbox(sandbox_spec_id, sandbox_id)

    # ── Delegated methods ────────────────────────────────────────────

    async def search_sandboxes(
        self,
        page_id: str | None = None,
        limit: int = 100,
    ) -> SandboxPage:
        return await self._inner.search_sandboxes(page_id, limit)

    async def get_sandbox(self, sandbox_id: str) -> SandboxInfo | None:
        return await self._inner.get_sandbox(sandbox_id)

    async def get_sandbox_by_session_api_key(
        self, session_api_key: str
    ) -> SandboxInfo | None:
        return await self._inner.get_sandbox_by_session_api_key(session_api_key)

    async def get_sandbox_record_by_session_api_key(
        self, session_api_key: str
    ) -> SandboxRecord | None:
        return await self._inner.get_sandbox_record_by_session_api_key(
            session_api_key
        )

    async def batch_get_sandboxes(
        self, sandbox_ids: list[str]
    ) -> list[SandboxInfo | None]:
        return await self._inner.batch_get_sandboxes(sandbox_ids)

    async def resume_sandbox(self, sandbox_id: str) -> bool:
        return await self._inner.resume_sandbox(sandbox_id)

    async def pause_sandbox(self, sandbox_id: str) -> bool:
        return await self._inner.pause_sandbox(sandbox_id)

    async def delete_sandbox(self, sandbox_id: str) -> bool:
        return await self._inner.delete_sandbox(sandbox_id)

    async def archive_conversation_workspace(
        self,
        sandbox_id: str,
        conversation_id: str | None = None,
        workspace_path: str | None = None,
    ) -> bool:
        return await self._inner.archive_conversation_workspace(
            sandbox_id, conversation_id, workspace_path
        )

    async def pause_old_sandboxes(self, max_num_sandboxes: int) -> list[str]:
        return await self._inner.pause_old_sandboxes(max_num_sandboxes)

    # ── Pool management ──────────────────────────────────────────────

    async def warm_pool(self) -> None:
        """Start warming sandboxes in the background."""
        await self._pool.warm()

    async def pool_stats(self) -> dict:
        """Get pool statistics."""
        return await self._pool.stats()

    async def drain_pool(self) -> None:
        """Drain and discard all pooled sandboxes."""
        await self._pool.drain()

    def pool(self) -> SandboxPool:
        """Expose the underlying pool for direct management."""
        return self._pool
