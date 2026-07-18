"""Dynamic task graph with dependency resolution, priority scheduling,
and parallel execution planning.

Each task has:
  - priority (0-100, higher = more urgent)
  - depends_on (list of task IDs)
  - resource_estimate (estimated token/memory cost)
  - status (pending/ready/running/completed/failed/blocked)
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = 'pending'
    READY = 'ready'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    BLOCKED = 'blocked'
    SKIPPED = 'skipped'


@dataclass
class PrioritizedTask:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ''
    description: str = ''
    priority: int = 50  # 0-100, higher = more urgent
    depends_on: list[str] = field(default_factory=list)
    resource_estimate: float = 1.0  # abstract cost units
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = ''
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class TaskGraph:
    """Directed acyclic graph of prioritized tasks.

    Handles dependency resolution, topological sort, critical-path
    detection, and ready-task selection.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, PrioritizedTask] = {}

    # ── Mutation ─────────────────────────────────────────────────

    def add(self, task: PrioritizedTask) -> PrioritizedTask:
        self._tasks[task.id] = task
        return task

    def add_many(self, tasks: list[PrioritizedTask]) -> None:
        for t in tasks:
            self._tasks[t.id] = t

    def remove(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)

    def update_status(self, task_id: str, status: TaskStatus, **kw: Any) -> None:
        t = self._tasks.get(task_id)
        if not t:
            # fallback: look up by name
            matches = [x for x in self._tasks.values() if x.name == task_id]
            if matches:
                t = matches[0]
            else:
                return
        t.status = status
        for k, v in kw.items():
            setattr(t, k, v)
        if status == TaskStatus.RUNNING:
            t.started_at = time.time()
        elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            t.completed_at = time.time()

    # ── Query ────────────────────────────────────────────────────

    def get(self, task_id: str) -> PrioritizedTask | None:
        t = self._tasks.get(task_id)
        if t:
            return t
        for v in self._tasks.values():
            if v.name == task_id:
                return v
        return None

    def all(self) -> list[PrioritizedTask]:
        return list(self._tasks.values())

    def by_status(self, status: TaskStatus) -> list[PrioritizedTask]:
        return [t for t in self._tasks.values() if t.status == status]

    def _resolve(self, name_or_id: str) -> PrioritizedTask | None:
        """Resolve a dependency reference — try ID first, fallback to name."""
        t = self._tasks.get(name_or_id)
        if t:
            return t
        for v in self._tasks.values():
            if v.name == name_or_id:
                return v
        return None

    def ready(self, max_count: int = 0) -> list[PrioritizedTask]:
        """Return ready tasks sorted by priority (highest first).

        A task is ready when all its deps are completed AND it is
        either PENDING or READY.
        """
        ready: list[PrioritizedTask] = []
        for t in self._tasks.values():
            if t.status not in (TaskStatus.PENDING, TaskStatus.READY):
                continue
            deps_ok = all(
                (dep := self._resolve(d)) and dep.status == TaskStatus.COMPLETED
                for d in t.depends_on
            )
            if deps_ok:
                t.status = TaskStatus.READY
                ready.append(t)

        ready.sort(key=lambda x: x.priority, reverse=True)
        return ready[:max_count] if max_count > 0 else ready

    def is_complete(self) -> bool:
        """All tasks terminal (completed/failed/skipped)?"""
        return all(
            t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED)
            for t in self._tasks.values()
        )

    def has_failures(self) -> bool:
        return any(t.status == TaskStatus.FAILED for t in self._tasks.values())

    def critical_path(self) -> list[PrioritizedTask]:
        """Simple critical-path heuristic: longest chain of deps."""
        # Build depth map
        depths: dict[str, int] = {}

        def _depth(tid: str) -> int:
            if tid in depths:
                return depths[tid]
            t = self._tasks.get(tid)
            if not t or not t.depends_on:
                depths[tid] = 0
                return 0
            max_d = max(_depth(d) for d in t.depends_on) + 1
            depths[tid] = max_d
            return max_d

        for tid in self._tasks:
            _depth(tid)
        max_depth = max(depths.values()) if depths else 0
        deepest = [tid for tid, d in depths.items() if d == max_depth]
        return [self._tasks[tid] for tid in deepest if tid in self._tasks]

    def count_by_status(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for t in self._tasks.values():
            counts[t.status.value] = counts.get(t.status.value, 0) + 1
        return counts

    def summary(self) -> dict[str, Any]:
        return {
            'total': len(self._tasks),
            **self.count_by_status(),
            'critical_path_count': len(self.critical_path()),
            'is_complete': self.is_complete(),
            'has_failures': self.has_failures(),
        }
