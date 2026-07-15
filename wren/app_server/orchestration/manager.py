"""Manager agent: decomposes massive project goals into sub-tasks and delegates.

When a large goal is given, the manager:
1. Decomposes the goal into independent/ordered sub-tasks
2. Assigns each sub-task to a sub-agent via the execution loop
3. Tracks progress in working memory
4. Reviews and integrates sub-agent results
5. Runs the self-memory loop after completion
"""

import logging
import time
import uuid
from typing import Any

from wren.app_server.orchestration.self_memory_loop import SelfMemoryLoop
from wren.app_server.orchestration.working_memory import WorkingMemory

_logger = logging.getLogger(__name__)


class SubTask:
    """A single unit of work within a larger decomposition."""

    def __init__(
        self,
        name: str,
        description: str,
        depends_on: list[str] | None = None,
        estimated_effort: str = 'medium',
        acceptance_criteria: list[str] | None = None,
    ):
        self.id = f'task_{uuid.uuid4().hex[:8]}'
        self.name = name
        self.description = description
        self.depends_on = depends_on or []
        self.estimated_effort = estimated_effort
        self.acceptance_criteria = acceptance_criteria or []
        self.status = 'pending'  # pending | running | completed | failed
        self.result: str | None = None
        self.error: str | None = None
        self.started_at: float | None = None
        self.completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'depends_on': self.depends_on,
            'estimated_effort': self.estimated_effort,
            'acceptance_criteria': self.acceptance_criteria,
            'status': self.status,
            'result': self.result,
            'error': self.error,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> 'SubTask':
        t = cls(
            name=d['name'],
            description=d['description'],
            depends_on=d.get('depends_on', []),
            estimated_effort=d.get('estimated_effort', 'medium'),
            acceptance_criteria=d.get('acceptance_criteria', []),
        )
        t.id = d.get('id', t.id)
        t.status = d.get('status', 'pending')
        t.result = d.get('result')
        t.error = d.get('error')
        t.started_at = d.get('started_at')
        t.completed_at = d.get('completed_at')
        return t


class ManagerAgent:
    """Decomposes goals, delegates sub-tasks, tracks progress, and learns.

    This is the top-level orchestrator pattern used when a massive project
    goal is given. The main agent acts as a manager that:
    1. Decomposes the goal into ordered sub-tasks
    2. Spawns sub-agents for parallel/sequential execution
    3. Reviews results and integrates them
    4. Runs the self-memory loop for continuous improvement
    """

    def __init__(
        self,
        project_root: str | None = None,
        working_memory: WorkingMemory | None = None,
        self_memory_loop: SelfMemoryLoop | None = None,
    ):
        self._wm = working_memory or WorkingMemory(project_root)
        self._sml = self_memory_loop or SelfMemoryLoop(
            project_root=project_root,
            working_memory=self._wm,
        )
        self._sub_tasks: list[SubTask] = []
        self._goal: str = ''

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def initialize_goal(self, goal: str) -> dict[str, Any]:
        """Start a new project goal. Clears previous sub-tasks."""
        self._goal = goal
        self._sub_tasks = []
        self._wm.clear_session()
        self._wm.add_decision(f'Project goal initialized: {goal[:100]}')
        return {'goal': goal, 'status': 'initialized'}

    def decompose(
        self,
        sub_tasks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Register decomposed sub-tasks from the manager's analysis.

        Each sub-task dict:
            name: str
            description: str
            depends_on: list[str] — names of sub-tasks that must complete first
            estimated_effort: str — small/medium/large
            acceptance_criteria: list[str]
        """
        self._sub_tasks = [SubTask(**t) for t in sub_tasks]
        for t in self._sub_tasks:
            self._wm.add_todo(
                task=t.name,
                depends_on=t.depends_on,
            )

        plan = self.plan()
        _logger.info(
            'ManagerAgent: goal=%s decomposed into %d tasks',
            self._goal[:50],
            len(self._sub_tasks),
        )
        return plan

    def plan(self) -> list[dict[str, Any]]:
        """Return the current sub-task plan with dependency ordering."""
        return [t.to_dict() for t in self._sub_tasks]

    def get_ready_tasks(self) -> list[SubTask]:
        """Return tasks whose dependencies are all completed."""
        completed_names = {t.name for t in self._sub_tasks if t.status == 'completed'}
        return [
            t
            for t in self._sub_tasks
            if t.status == 'pending'
            and all(dep in completed_names for dep in t.depends_on)
        ]

    def start_task(self, task_id: str) -> SubTask | None:
        for t in self._sub_tasks:
            if t.id == task_id:
                t.status = 'running'
                t.started_at = time.time()
                self._wm.add_progress(t.name, 'running')
                return t
        return None

    def complete_task(
        self,
        task_id: str,
        result: str,
        error: str | None = None,
    ) -> SubTask | None:
        for t in self._sub_tasks:
            if t.id == task_id:
                t.status = 'failed' if error else 'completed'
                t.completed_at = time.time()
                t.result = result
                t.error = error
                self._wm.complete_todo(
                    task_id=task_id,
                    result=result[:200] if result else '',
                )
                return t
        return None

    def status(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for t in self._sub_tasks:
            counts[t.status] = counts.get(t.status, 0) + 1
        return {
            'goal': self._goal,
            'total': len(self._sub_tasks),
            'status_counts': counts,
            'ready': [t.to_dict() for t in self.get_ready_tasks()],
            'all': [t.to_dict() for t in self._sub_tasks],
        }

    def summary(self) -> str:
        parts = [f'# Manager Summary: {self._goal}', '']
        status = self.status()
        counts = status['status_counts']
        parts.append(
            f'Total: {status["total"]} | '
            f'Pending: {counts.get("pending", 0)} | '
            f'Running: {counts.get("running", 0)} | '
            f'Completed: {counts.get("completed", 0)} | '
            f'Failed: {counts.get("failed", 0)}'
        )
        parts.append('')
        parts.append(self._wm.summary())
        return '\n'.join(parts)

    async def finalize(self, overall_outcome: str) -> dict[str, Any]:
        """Finalize the project and run the self-memory loop."""
        completed = sum(1 for t in self._sub_tasks if t.status == 'completed')
        failed = sum(1 for t in self._sub_tasks if t.status == 'failed')
        observations = (
            f'{completed} tasks completed, {failed} failed. Goal: {self._goal[:200]}'
        )
        result = await self._sml.reflect(
            task_description=self._goal,
            outcome=overall_outcome,
            observations=observations,
            tags=['manager-agent', 'project'],
        )
        _logger.info('ManagerAgent.finalize: %s', result)
        return result
