"""DAG task scheduler for autonomous sub-task execution.

Drives the manager-agent decomposition DAG: resolves dependencies,
spawns ready tasks in parallel, collects results, and progresses
through the plan until all tasks are done or a critical path fails.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from wren.ohos.config import CONFIG

_logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """A task in the DAG with runtime state."""

    name: str
    description: str
    depends_on: list[str] = field(default_factory=list)
    estimated_effort: str = 'medium'
    acceptance_criteria: list[str] = field(default_factory=list)

    # Runtime state (set by scheduler)
    id: str = ''
    status: str = 'pending'  # pending | running | completed | failed | skipped
    result: Any = None
    error: str = ''
    started_at: float = 0.0
    completed_at: float = 0.0


class DAGScheduler:
    """Drives a DAG of sub-tasks to completion.

    Usage:
        scheduler = DAGScheduler()
        scheduler.load(tasks)       # load task list
        await scheduler.run()       # run to completion
        scheduler.summary()         # get results
    """

    def __init__(self, max_concurrent: int | None = None) -> None:
        self._tasks: dict[str, ScheduledTask] = {}
        self._max_concurrent = max_concurrent or CONFIG.max_concurrent_sub_tasks
        self._name_map: dict[str, str] = {}  # name → id

    def load(self, tasks: list[dict[str, Any]]) -> None:
        """Load a list of task dicts into the scheduler."""
        for t in tasks:
            task = ScheduledTask(
                name=t['name'],
                description=t.get('description', ''),
                depends_on=t.get('depends_on', []),
                estimated_effort=t.get('estimated_effort', 'medium'),
                acceptance_criteria=t.get('acceptance_criteria', []),
            )
            task.id = str(uuid.uuid4())[:8]
            self._tasks[task.id] = task
            self._name_map[task.name] = task.id

        # Resolve dependency names to IDs
        for task in self._tasks.values():
            resolved: list[str] = []
            for dep_name in task.depends_on:
                dep_id = self._name_map.get(dep_name)
                if dep_id:
                    resolved.append(dep_id)
            task.depends_on = resolved

        _logger.info('DAGScheduler: loaded %d tasks', len(self._tasks))

    def get_ready(self) -> list[ScheduledTask]:
        """Return tasks whose dependencies are all completed."""
        ready: list[ScheduledTask] = []
        for task in self._tasks.values():
            if task.status != 'pending':
                continue
            deps_met = all(
                self._tasks[d].status == 'completed' for d in task.depends_on
            )
            if deps_met:
                ready.append(task)
        return ready

    async def run(
        self,
        executor_fn,
        sequential: bool = False,
    ) -> dict[str, Any]:
        """Execute the DAG.

        Args:
            executor_fn: Async callable(task) that runs a single task.
            sequential: If True, run one at a time.

        Returns:
            Summary dict with overall status.
        """
        if not self._tasks:
            _logger.warning('DAGScheduler: no tasks loaded')
            return {'status': 'empty', 'total': 0, 'completed': 0, 'failed': 0}

        overall_status = 'running'

        while overall_status == 'running':
            ready = self.get_ready()
            if not ready:
                # Check if any pending tasks still have unmet deps
                pending = [t for t in self._tasks.values() if t.status == 'pending']
                if not pending:
                    overall_status = 'completed'
                else:
                    # Check for deadlock
                    for t in pending:
                        for d in t.depends_on:
                            if self._tasks[d].status == 'failed':
                                t.status = 'skipped'
                                t.error = f'Dependency {d} failed'
                                _logger.info(
                                    'DAGScheduler: skipped %s (dep %s failed)',
                                    t.name,
                                    d,
                                )
                    # Re-check
                    still_pending = [
                        t for t in self._tasks.values() if t.status == 'pending'
                    ]
                    if still_pending and not self.get_ready():
                        _logger.error(
                            'DAGScheduler: deadlock — %d tasks pending with unmet deps',
                            len(still_pending),
                        )
                        overall_status = 'deadlocked'
                        break
                    if not still_pending:
                        overall_status = 'completed'
                break

            if sequential:
                task = ready[0]
                await self._execute_one(task, executor_fn)
            else:
                # Run up to max_concurrent ready tasks
                batch = ready[: self._max_concurrent]
                await asyncio.gather(
                    *(self._execute_one(t, executor_fn) for t in batch)
                )

        return self.summary()

    async def _execute_one(self, task: ScheduledTask, executor_fn) -> None:
        task.status = 'running'
        task.started_at = time.time()
        _logger.info('DAGScheduler: start %s', task.name)
        try:
            result = await asyncio.wait_for(
                executor_fn(task),
                timeout=CONFIG.sub_task_timeout_s,
            )
            task.result = result
            task.status = 'completed'
            _logger.info('DAGScheduler: completed %s', task.name)
        except asyncio.TimeoutError:
            task.status = 'failed'
            task.error = f'Timeout ({CONFIG.sub_task_timeout_s}s)'
            _logger.warning('DAGScheduler: timeout %s', task.name)
        except Exception as e:
            task.status = 'failed'
            task.error = str(e)[:200]
            _logger.warning('DAGScheduler: failed %s: %s', task.name, e)
        finally:
            task.completed_at = time.time()

    def summary(self) -> dict[str, Any]:
        """Get execution summary."""
        counts = {'pending': 0, 'running': 0, 'completed': 0, 'failed': 0, 'skipped': 0}
        for t in self._tasks.values():
            counts[t.status] = counts.get(t.status, 0) + 1

        return {
            'total': len(self._tasks),
            **counts,
            'tasks': [
                {
                    'name': t.name,
                    'status': t.status,
                    'duration_s': round(t.completed_at - t.started_at, 1)
                    if t.completed_at
                    else None,
                    'error': t.error[:100] if t.error else None,
                }
                for t in self._tasks.values()
            ],
        }
