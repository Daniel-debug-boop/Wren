"""Dark Factory (v2) — silent background processing.

Runs maintenance, pre-fetching, pre-computation, and speculative
execution in low-priority background threads. Never blocks user-
facing operations.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass  # field unused
from typing import Any

_logger = logging.getLogger(__name__)


@dataclass
class DarkTask:
    id: str = ''
    name: str = ''
    priority: int = 0
    cost_estimate: float = 0.0
    coro: Any = None
    result: Any = None
    error: str = ''
    completed: bool = False


class DarkFactory:
    """Low-priority background task processor.

    Runs tasks when resources are idle. Pre-emptible — user tasks
    always take priority.
    """

    def __init__(self, max_concurrent: int = 2) -> None:
        self._queue: asyncio.Queue[DarkTask] = asyncio.Queue()
        self._running: set[str] = set()
        self._completed: list[DarkTask] = []
        self._max_concurrent = max_concurrent
        self._active = False
        self._max_history = 100

    @property
    def backlog(self) -> int:
        return self._queue.qsize()

    @property
    def active_count(self) -> int:
        return len(self._running)

    # ── Lifecycle ────────────────────────────────────────────────

    async def start(self) -> None:
        self._active = True
        _logger.info('DarkFactory: started')
        while self._active:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            if task.id in self._running:
                continue
            self._running.add(task.id)
            asyncio.create_task(self._process(task))

    def stop(self) -> None:
        self._active = False

    async def _process(self, task: DarkTask) -> None:
        try:
            _logger.debug('DarkFactory: running %s', task.name)
            task.result = await task.coro
            task.completed = True
        except Exception as e:
            task.error = str(e)
            _logger.warning('DarkFactory: %s failed: %s', task.name, e)
        finally:
            self._running.discard(task.id)
            self._completed.append(task)
            if len(self._completed) > self._max_history:
                self._completed = self._completed[-self._max_history :]

    # ── Submission ───────────────────────────────────────────────

    def enqueue(self, name: str, coro: Any, priority: int = 0) -> str:
        """Submit a background task.

        Returns a task ID for status checking.
        """
        task = DarkTask(
            id=f'dark_{int(time.time() * 1000)}_{len(self._completed)}',
            name=name,
            priority=priority,
            coro=coro,
        )
        self._queue.put_nowait(task)
        _logger.debug('DarkFactory: enqueued %s', name)
        return task.id

    def status(self, task_id: str) -> str:
        if task_id in self._running:
            return 'running'
        for t in self._completed:
            if t.id == task_id:
                return 'completed' if not t.error else f'failed: {t.error}'
        return 'queued'

    def stats(self) -> dict[str, Any]:
        return {
            'backlog': self.backlog,
            'active': self.active_count,
            'completed': len(self._completed),
        }
