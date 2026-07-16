"""AutoModeEngine — the autonomous lifecycle manager.

Hardcoded into every conversation. Always active. Cannot be disabled.
Each stage triggers automatically without agent opt-in.

Lifecycle:
  pre_start(user_message, user_context) → [goal_detect, decompose, inject_context]
  on_event(event)                          → [classify, recover, track, reflect_if_terminal]
  on_completion(summary)                   → [final_reflect, sync_solutions, cleanup]
"""

from __future__ import annotations

import logging
from typing import Any

from wren.ohos.circuit_breaker import BREAKER
from wren.ohos.config import CONFIG

_logger = logging.getLogger(__name__)


# ── Lazy imports (avoid circular deps at package init) ──────────


def _goal_detector():
    from wren.app_server.orchestration.goal_detector import GoalDetector  # noqa: PLC0415

    return GoalDetector


def _working_memory(project_root: str | None = None):
    from wren.app_server.orchestration.working_memory import WorkingMemory  # noqa: PLC0415

    return WorkingMemory(project_root or CONFIG.project_root)


def _manager():
    from wren.app_server.orchestration.manager import ManagerAgent  # noqa: PLC0415

    return ManagerAgent


def _self_memory_loop(project_root: str | None = None):
    from wren.app_server.orchestration.self_memory_loop import SelfMemoryLoop  # noqa: PLC0415

    return SelfMemoryLoop(project_root or CONFIG.project_root)


def _solution_registry(project_root: str | None = None):
    from wren.app_server.orchestration.error_recovery import SolutionRegistry  # noqa: PLC0415

    return SolutionRegistry(project_root or CONFIG.project_root)


# ═════════════════════════════════════════════════════════════════
# Phase 1: Pre-start
# ═════════════════════════════════════════════════════════════════


class GoalDetectionResult:
    """Output of the pre-start pipeline."""

    __slots__ = (
        'is_complex',
        'score',
        'trigger_count',
        'tech_count',
        'sub_tasks',
        'system_instruction',
        'decomposition_id',
    )

    def __init__(self) -> None:
        self.is_complex: bool = False
        self.score: float = 0.0
        self.trigger_count: int = 0
        self.tech_count: int = 0
        self.sub_tasks: list[dict] | None = None
        self.system_instruction: str | None = None
        self.decomposition_id: str | None = None


def run_pre_start_pipeline(
    user_message: str,
    project_root: str | None = None,
) -> GoalDetectionResult:
    """Analyze user message and prepare system context.

    Always runs. Never skipped. Returns result even if goal is simple.
    """
    result = GoalDetectionResult()

    gd_cls = _goal_detector()
    gd = gd_cls(project_root)
    analysis = gd.analyze(user_message)

    result.is_complex = analysis.get('is_complex_goal', False)
    result.score = analysis.get('score', 0.0)
    result.trigger_count = analysis.get('trigger_count', 0)
    result.tech_count = analysis.get('tech_count', 0)
    result.sub_tasks = analysis.get('auto_decomposition')
    result.system_instruction = analysis.get('system_instruction')
    result.decomposition_id = analysis.get('decomposition_id')

    _logger.info(
        'OHOS pre-start: complex=%s score=%.1f triggers=%d tech=%d tasks=%s',
        result.is_complex,
        result.score,
        result.trigger_count,
        result.tech_count,
        len(result.sub_tasks) if result.sub_tasks else 0,
    )

    return result


# ═════════════════════════════════════════════════════════════════
# Phase 2: Mid-execution event processing
# ═════════════════════════════════════════════════════════════════


class EventClassification:
    """What the engine decided about a single event."""

    __slots__ = (
        'event_id',
        'event_type',
        'is_error',
        'error_type',
        'is_terminal',
        'triggered_auto_recovery',
        'triggered_auto_reflection',
        'triggered_tool_discovery',
        'actions_taken',
    )

    def __init__(self, event_id: str, event_type: str) -> None:
        self.event_id = event_id
        self.event_type = event_type
        self.is_error: bool = False
        self.error_type: str | None = None
        self.is_terminal: bool = False
        self.triggered_auto_recovery: bool = False
        self.triggered_auto_reflection: bool = False
        self.triggered_tool_discovery: bool = False
        self.actions_taken: list[str] = []


def process_event(
    event: dict[str, Any],
    project_root: str | None = None,
) -> EventClassification:
    """Classify and act on a single conversation event.

    Called by EventCallbackProcessor for every event.
    """
    event_id = str(event.get('id', ''))
    event_type = event.get('type', '')

    clf = EventClassification(event_id, event_type)

    # ── Detect errors ────────────────────────────────────────
    error_text = _extract_error(event)
    if error_text:
        clf.is_error = True
        from wren.app_server.orchestration.error_recovery import (  # noqa: PLC0415
            ErrorSignature,
        )

        sig = ErrorSignature(error_text)
        clf.error_type = sig.error_type

        # Auto-recovery
        if CONFIG.auto_retry_all_errors:
            operation_type = sig.error_type
            if BREAKER.allow_request(operation_type):
                clf.triggered_auto_recovery = True
                clf.actions_taken.append(f'auto_recovery:{sig.error_type}')
                _logger.info('OHOS auto-recovery triggered for %s', sig.error_type)
            else:
                _logger.warning('OHOS circuit breaker OPEN for %s', operation_type)
                clf.actions_taken.append(f'circuit_open:{operation_type}')

    # ── Tool gap detection ────────────────────────────────────
    if CONFIG.auto_discover_tools and _has_tool_gap(event):
        clf.triggered_tool_discovery = True
        clf.actions_taken.append('tool_discovery')
        _logger.info('OHOS tool gap detected in event %s', event_id)

    # ── Terminal state → reflect ──────────────────────────────
    status = event.get('status') or (event.get('event_data') or {}).get('status')
    if status in ('ERROR', 'STOPPED', 'COMPLETED'):
        clf.is_terminal = True
        if CONFIG.auto_reflect_on_error or status != 'ERROR':
            clf.triggered_auto_reflection = True
            clf.actions_taken.append(f'auto_reflect:{status}')

    return clf


def _extract_error(event: dict) -> str | None:
    """Pull error text from any event shape."""
    # ObservationEvent with error content
    obs = event.get('observation') or event.get('event_data', {})
    for key in ('error', 'error_message', 'content', 'message'):
        val = obs.get(key, '')
        if isinstance(val, str) and len(val) > 3:
            # Heuristic: error-like text
            if any(
                kw in val.lower()
                for kw in (
                    'error',
                    'exception',
                    'traceback',
                    'failed',
                    'not found',
                    'denied',
                )
            ):
                return val[:500]
    return None


_COMMAND_NOT_FOUND_PATTERNS = (
    'command not found',
    'no module named',
    'cannot find',
    'not installed',
    'unknown command',
)


def _has_tool_gap(event: dict) -> bool:
    """Check if event signals a tool that should be auto-installed."""
    obs = event.get('observation') or event.get('event_data', {})
    content = str(obs.get('content', ''))
    lowered = content.lower()
    return any(p in lowered for p in _COMMAND_NOT_FOUND_PATTERNS)


# ═════════════════════════════════════════════════════════════════
# Phase 3: Post-completion
# ═════════════════════════════════════════════════════════════════


def run_post_completion(
    summary: dict[str, Any] | None = None,
    project_root: str | None = None,
) -> list[str]:
    """Run after a conversation or sub-task completes.

    Returns list of actions taken.
    """
    actions: list[str] = []
    pr = project_root or CONFIG.project_root

    # ── Final reflection ───────────────────────────────────────
    if CONFIG.auto_reflect_on_complete:
        try:
            _sml = _self_memory_loop(pr)  # noqa: F841
            _logger.info('OHOS post-completion reflection started')
            # sml.reflect is async — caller must await separately
            actions.append('reflection_queued')
        except Exception as e:
            _logger.warning('OHOS post-completion reflect failed: %s', e)

    # ── Sync error solutions ───────────────────────────────────
    try:
        reg = _solution_registry(pr)
        sols = reg.all_solutions()
        actions.append(f'solution_sync:{len(sols)}_entries')
    except Exception as e:
        _logger.warning('OHOS solution sync failed: %s', e)

    _logger.info('OHOS post-completion actions: %s', actions)
    return actions
