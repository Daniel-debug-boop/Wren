"""Hardcoded integration points — the glue between OHOS and the Wren server.

These are the ONLY files in OHOS that know about the server's internal
APIs. Everything else is pure orchestration.

Why separate file? So the core engine has zero dependency on the server's
event system or conversation models. Swap the server → swap this file.
"""

from __future__ import annotations

import logging
from typing import Any

from wren.ohos.engine import process_event, run_pre_start_pipeline
from wren.ohos.orchestrator import Orchestrator

_logger = logging.getLogger(__name__)

# ── Per-conversation orchestrator instances ──────────────────────
# Keyed by conversation_id (str). Created lazily.
_orchestrators: dict[str, Orchestrator] = {}


def get_orchestrator(
    conversation_id: str,
    project_root: str | None = None,
) -> Orchestrator:
    """Get or create the orchestrator for a conversation."""
    if conversation_id not in _orchestrators:
        _orchestrators[conversation_id] = Orchestrator(project_root)
    return _orchestrators[conversation_id]


def remove_orchestrator(conversation_id: str) -> None:
    """Clean up after conversation ends."""
    _orchestrators.pop(conversation_id, None)


# ── Pre-start hook ───────────────────────────────────────────────


def hardcode_pre_start(
    user_message: str,
    conversation_id: str,
    project_root: str | None = None,
) -> str | None:
    """Run pre-start pipeline and return the system-instruction suffix.

    This replaces the old pattern:
        detector = GoalDetector(...)
        instruction = detector.injectable_context(message_text)

    Always runs. Returns None if no instruction needed.
    """
    orch = get_orchestrator(conversation_id, project_root)
    ctx = run_pre_start_pipeline(user_message, project_root)

    # Store in orchestrator for later use
    orch._goal_context = ctx  # noqa: SLF001 — intentional integration

    if ctx.system_instruction:
        _logger.info(
            'OHOS hardcode_pre_start: complex goal detected, instruction injected'
        )
        return ctx.system_instruction

    if ctx.error_solutions_summary:
        return f'\n[OHOS] {ctx.error_solutions_summary}'

    return None


# ── Event hook ───────────────────────────────────────────────────


class OHDOSEventProcessor:
    """EventCallbackProcessor-compatible class for OHOS event processing.

    Register this as a processor in the conversation request:
        request.processors.append(OHDOSEventProcessor())
    """

    def __init__(self) -> None:
        self._conversation_id: str = ''

    def get_event_kind(self) -> str:
        """Return the event kind this processor handles."""
        return 'all'

    async def on_event(
        self,
        event: dict[str, Any],
        conversation_id: str,
        project_root: str | None = None,
    ) -> None:
        """Called for every event. Always runs classification + auto-recovery."""
        self._conversation_id = conversation_id
        clf = process_event(event, project_root)

        if clf.is_error:
            _logger.info(
                'OHOS event processor: error=%s recovery=%s type=%s',
                clf.error_type,
                clf.triggered_auto_recovery,
                clf.event_type,
            )


# ── Cleanup hook ─────────────────────────────────────────────────


async def hardcode_post_completion(
    conversation_id: str,
    summary: dict[str, Any] | None = None,
) -> None:
    """Run post-completion pipeline and clean up orchestrator."""
    orch = _orchestrators.get(conversation_id)
    if orch:
        await orch.post_completion(summary)
        remove_orchestrator(conversation_id)
        _logger.info('OHOS: cleaned up orchestrator for %s', conversation_id)
