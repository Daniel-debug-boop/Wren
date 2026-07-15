"""Execution pipeline — hooks that run before, during, and after every agent action.

Three pipeline stages:
  pre_action(hook_ctx)  → mutate system prompt / working memory / tool config
  post_action(hook_ctx)  → classify event, trigger recovery, update memory
  post_completion(ctx)   → reflect, sync solutions, clean up

All pipelines run automatically. Always enabled.
"""

from __future__ import annotations

import logging
from typing import Any

from wren.ohos.config import CONFIG
from wren.ohos.engine import (
    GoalDetectionResult,
    process_event,
    run_post_completion,
    run_pre_start_pipeline,
)

_logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════
# Pre-action pipeline
# ═════════════════════════════════════════════════════════════════


class PreActionContext:
    """Mutable context passed through the pre-action pipeline.

    Each hook can read and write these fields. The final result is
    applied before the agent executes its next action.
    """

    __slots__ = (
        'user_message',
        'system_instruction_extra',
        'goal_result',
        'working_memory_summary',
        'error_solutions_summary',
        'injected_skills',
    )

    def __init__(self, user_message: str) -> None:
        self.user_message = user_message
        self.system_instruction_extra: str | None = None
        self.goal_result: GoalDetectionResult | None = None
        self.working_memory_summary: str = ''
        self.error_solutions_summary: str = ''
        self.injected_skills: list[str] = []


def run_pre_action_pipeline(
    user_message: str,
    project_root: str | None = None,
) -> PreActionContext:
    """Run all pre-action hooks and return the accumulated context.

    Always runs. These hooks execute:
      1. Goal detection → decompose → system-instruction injection
      2. Working-memory priming → inject past reflections
      3. Error-solution priming → inject known fixes for common error types
    """
    ctx = PreActionContext(user_message)
    pr = project_root or CONFIG.project_root

    # 1. Goal detection
    goal_result = run_pre_start_pipeline(user_message, pr)
    ctx.goal_result = goal_result
    if goal_result.system_instruction:
        ctx.system_instruction_extra = goal_result.system_instruction
        ctx.injected_skills.append('manager_mode')

    # 2. Working-memory priming
    try:
        from wren.app_server.orchestration.working_memory import (  # noqa: PLC0415
            WorkingMemory,
        )

        wm = WorkingMemory(pr)
        summary = wm.summary()
        if len(summary) > 500:
            summary = summary[:500] + '…'
        ctx.working_memory_summary = summary
    except Exception as e:
        _logger.debug('Working-memory priming skipped: %s', e)

    # 3. Error-solution priming
    try:
        from wren.app_server.orchestration.error_recovery import (  # noqa: PLC0415
            SolutionRegistry,
        )

        reg = SolutionRegistry(pr)
        sols = reg.all_solutions()
        if sols:
            summaries = [
                f'{s["error_type"]}: {s["best_strategy"][:40]}' for s in sols[:5]
            ]
            ctx.error_solutions_summary = 'known_fixes=' + ' | '.join(summaries)
            ctx.injected_skills.append('error_solutions')
    except Exception as e:
        _logger.debug('Error-solution priming skipped: %s', e)

    _logger.info(
        'OHOS pre-action: goal_complex=%s skills=%s',
        goal_result.is_complex,
        ctx.injected_skills,
    )
    return ctx


# ═════════════════════════════════════════════════════════════════
# Post-event pipeline
# ═════════════════════════════════════════════════════════════════


class PostEventContext:
    """Output of the post-event pipeline."""

    __slots__ = ('classification', 'triggered_recovery', 'triggered_reflection')

    def __init__(self, classification: Any) -> None:
        self.classification = classification
        self.triggered_recovery: bool = False
        self.triggered_reflection: bool = False


def run_post_event_pipeline(
    event: dict[str, Any],
    project_root: str | None = None,
) -> PostEventContext:
    """Classify and react to a single event.

    Always runs on every event. Never skipped.
    """
    clf = process_event(event, project_root)
    ctx = PostEventContext(clf)

    ctx.triggered_recovery = clf.triggered_auto_recovery
    ctx.triggered_reflection = clf.triggered_auto_reflection

    if clf.is_error:
        _logger.info(
            'OHOS post-event: error=%s recovery=%s reflect=%s',
            clf.error_type,
            clf.triggered_auto_recovery,
            clf.triggered_auto_reflection,
        )

    return ctx


# ═════════════════════════════════════════════════════════════════
# Post-completion pipeline
# ═════════════════════════════════════════════════════════════════


def run_post_completion_pipeline(
    summary: dict[str, Any] | None = None,
    project_root: str | None = None,
) -> list[str]:
    """Run after the entire conversation completes.

    Always runs. Actions:
      1. Final reflection
      2. Sync error solutions
      3. Working-memory cleanup
    """
    actions = run_post_completion(summary, project_root)

    pr = project_root or CONFIG.project_root
    try:
        from wren.app_server.orchestration.working_memory import (  # noqa: PLC0415
            WorkingMemory,
        )

        wm = WorkingMemory(pr)
        wm.clear_session()
        actions.append('memory_cleared')
    except Exception as e:
        _logger.debug('Memory cleanup skipped: %s', e)

    _logger.info('OHOS post-completion: %s', actions)
    return actions
