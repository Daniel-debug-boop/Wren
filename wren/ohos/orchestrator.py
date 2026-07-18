"""OHOS Orchestrator — the public SDK entry point.

This is THE class to import when you want to use the autonomous
orchestration system. All other modules are internal.

Usage:
    from wren.ohos import Orchestrator

    orch = Orchestrator(project_root='/workspace')
    await orch.pre_start(user_message)
    await orch.on_event(event)
    await orch.post_completion(summary)
"""

from __future__ import annotations

import logging
from typing import Any

from wren.ohos.auto_wrapper import auto_operation, auto_retry
from wren.ohos.circuit_breaker import BREAKER
from wren.ohos.config import CONFIG, OHOSConfig
from wren.ohos.pipeline import (
    PostEventContext,
    PreActionContext,
    run_post_completion_pipeline,
    run_post_event_pipeline,
    run_pre_action_pipeline,
)
from wren.ohos.scheduler import DAGScheduler

_logger = logging.getLogger(__name__)


class Orchestrator:
    """The autonomous orchestration engine.

    One instance per conversation. Created automatically by the
    conversation service. Agent code can also create one to interact
    with the orchestration system.

    Thread-safe for reads; writes are sequential.
    """

    def __init__(self, project_root: str | None = None) -> None:
        self._project_root = project_root or CONFIG.project_root
        self._goal_context: PreActionContext | None = None
        self._scheduler: DAGScheduler | None = None
        self._completed_tasks: list[dict] = []

    # ── SDK: Pre-start ────────────────────────────────────────────

    async def pre_start(self, user_message: str) -> PreActionContext:
        """Run the pre-start pipeline.

        Always call this before the agent starts. Injects goal context,
        working-memory priming, and error-solution priming into the
        system instruction.

        Returns the PreActionContext with all injected context.
        """
        ctx = run_pre_action_pipeline(user_message, self._project_root)
        self._goal_context = ctx

        # If complex goal, create scheduler
        if ctx.goal_result and ctx.goal_result.is_complex and ctx.goal_result.sub_tasks:
            self._scheduler = DAGScheduler()
            self._scheduler.load(ctx.goal_result.sub_tasks)
            _logger.info(
                'Orchestrator: scheduler loaded with %d tasks',
                len(ctx.goal_result.sub_tasks),
            )

        return ctx

    # ── SDK: Event processing ─────────────────────────────────────

    async def on_event(self, event: dict[str, Any]) -> PostEventContext:
        """Process a single conversation event.

        Called for every event. Classifies, auto-recovers, auto-reflects.
        """
        ctx = run_post_event_pipeline(event, self._project_root)
        return ctx

    # ── SDK: Post-completion ──────────────────────────────────────

    async def post_completion(self, summary: dict[str, Any] | None = None) -> list[str]:
        """Run post-completion pipeline.

        Called when the conversation or a major sub-task finishes.
        """
        actions = run_post_completion_pipeline(summary, self._project_root)
        self._goal_context = None
        self._scheduler = None
        return actions

    # ── SDK: Goal & decomposition ─────────────────────────────────

    def goal_summary(self) -> dict[str, Any] | None:
        """Return the goal-detection result if available."""
        if not self._goal_context or not self._goal_context.goal_result:
            return None
        g = self._goal_context.goal_result
        return {
            'is_complex': g.is_complex,
            'score': g.score,
            'trigger_count': g.trigger_count,
            'tech_count': g.tech_count,
            'sub_task_count': len(g.sub_tasks) if g.sub_tasks else 0,
            'system_instruction_injected': g.system_instruction is not None,
        }

    async def decompose(
        self,
        tasks: list[dict[str, Any]],
        auto_start: bool = False,
    ) -> DAGScheduler | None:
        """Load a decomposition into the scheduler.

        Args:
            tasks: List of task dicts with name, description, depends_on, etc.
            auto_start: If True, immediately begin executing the DAG.

        Returns the scheduler or None if no tasks.
        """
        if not tasks:
            return None
        self._scheduler = DAGScheduler()
        self._scheduler.load(tasks)
        if auto_start and self._scheduler:
            await self._run_scheduler()
        return self._scheduler

    async def _run_scheduler(self) -> dict[str, Any]:
        """Internal: run the scheduler with auto-wrapped executor."""
        if not self._scheduler:
            return {'status': 'no_scheduler'}

        async def executor(task) -> dict[str, Any]:
            wrapped = await auto_operation(
                f'sub_task:{task.name}',
                lambda: self._execute_task(task),
            )
            self._completed_tasks.append(
                {
                    'name': task.name,
                    'result': wrapped.get('result'),
                    'status': wrapped.get('status'),
                }
            )
            return wrapped

        return await self._scheduler.run(executor)

    async def _execute_task(self, task) -> dict:
        """Placeholder for actual sub-task execution.

        Real implementation calls SubAgentService.spawn_sub_task().
        """
        from wren.app_server.orchestration.sub_agent_service import (  # noqa: PLC0415
            SubAgentService,
        )

        svc = SubAgentService()
        result = await svc.spawn_sub_task(
            parent_conversation_id='',
            task_name=task.name,
            task_description=task.description,
            acceptance_criteria=task.acceptance_criteria,
        )
        return result.to_dict()

    # ── SDK: Scheduler access ─────────────────────────────────────

    def scheduler_status(self) -> dict[str, Any] | None:
        """Get DAG scheduler status."""
        if not self._scheduler:
            return None
        return self._scheduler.summary()

    # ── SDK: Auto operations ──────────────────────────────────────

    @staticmethod
    async def run_with_retry(
        name: str,
        fn: Any,
        max_retries: int | None = None,
    ) -> dict[str, Any]:
        """Run any operation with full auto-recovery.

        This is the easiest way to use the auto-wrapper from agent code.
        """
        return await auto_operation(name, fn, max_retries)

    @staticmethod
    def wrap_with_retry(
        fn: Any,
        operation_name: str | None = None,
    ) -> Any:
        """Decorate any function with auto-recovery.

        Usage:
            @Orchestrator.wrap_with_retry
            def deploy(): ...
        """
        return auto_retry(fn, operation_name=operation_name)

    # ── SDK: Circuit breaker ──────────────────────────────────────

    @staticmethod
    def circuit_status(operation_type: str | None = None) -> Any:
        """Get circuit breaker status."""
        if operation_type:
            return BREAKER.status(operation_type)
        return BREAKER.all_status()

    # ── SDK: Config ───────────────────────────────────────────────

    @staticmethod
    def config() -> OHOSConfig:
        """Get the current OHOS configuration."""
        return CONFIG
