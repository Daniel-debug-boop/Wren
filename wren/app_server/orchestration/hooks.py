"""Event callback processors for auto-working-memory and auto-reflection.

These hook into the event stream via the EventCallbackProcessor system:
- WorkingMemoryProcessor: auto-records agent decisions, progress, and errors
- ReflectionProcessor: triggers self-reflection when conversation reaches terminal state

Registered at conversation start via AppConversationStartRequest.processors.
"""

import logging
import os
import time
from uuid import UUID

from wren.app_server.event_callback.event_callback_models import (
    EventCallback,
    EventCallbackProcessor,
)
from wren.app_server.event_callback.event_callback_result_models import (
    EventCallbackResult,
    EventCallbackResultStatus,
)
from wren.app_server.orchestration.working_memory import WorkingMemory
from wren import Event
from wren.event import (
    ActionEvent,
    ObservationEvent,
    ConversationStateUpdateEvent,
)
from openhands.sdk.conversation import ConversationExecutionStatus

_logger = logging.getLogger(__name__)


class WorkingMemoryProcessor(EventCallbackProcessor):
    """Auto-records agent actions, observations, and errors to working memory.

    Fires on every event. Captures:
    - ActionEvent.thought → decision or progress entry
    - ObservationEvent (error) → error entry
    - Status transitions → progress entry
    """

    event_kind: str = 'Event'

    async def __call__(
        self,
        conversation_id: UUID,
        callback: EventCallback,
        event: Event,
    ) -> EventCallbackResult | None:
        try:
            wm = WorkingMemory()
            event_type = type(event).__name__

            if isinstance(event, ActionEvent) and event.thought:
                thought = event.thought.strip()
                if len(thought) > 30:
                    wm.add_progress(
                        step=f'agent thought',
                        status='running',
                        detail=thought[:200],
                    )
                elif thought:
                    wm.add_decision(thought, context=event_type)

            elif isinstance(event, ObservationEvent):
                content = str(event.content or event.observation or '')[:300]
                if event.error:
                    wm.add(
                        'error',
                        content or 'Unknown error',
                        {'event_type': event_type},
                    )
                elif event.observation and 'result' in str(event.observation).lower():
                    wm.add_progress(
                        step='tool result',
                        status='completed',
                        detail=content,
                    )

            elif isinstance(event, ConversationStateUpdateEvent):
                if event.key == 'execution_status':
                    wm.add_progress(
                        step=f'status: {event.value}',
                        status='running'
                        if not _is_terminal(event.value)
                        else 'completed',
                    )

            return EventCallbackResult(
                status=EventCallbackResultStatus.SUCCESS,
                event_callback_id=callback.id,
                event_id=event.id,
                conversation_id=conversation_id,
            )
        except Exception as e:
            _logger.debug('WorkingMemoryProcessor failed: %s', e)
            return None


class ReflectionProcessor(EventCallbackProcessor):
    """Triggers self-reflection when conversation reaches a terminal state.

    On ERROR/STUCK/CANCELLED/COMPLETED, it:
    1. Reads working memory for the session
    2. Extracts lessons from what happened
    3. Stores lessons in FableMemory (cross-session)
    4. Attaches reflection result as metadata
    """

    event_kind: str = 'ConversationStateUpdateEvent'

    async def __call__(
        self,
        conversation_id: UUID,
        callback: EventCallback,
        event: Event,
    ) -> EventCallbackResult | None:
        if not isinstance(event, ConversationStateUpdateEvent):
            return None
        if event.key != 'execution_status':
            return None
        if not _is_terminal(event.value):
            return None

        try:
            from wren.app_server.orchestration.self_memory_loop import (
                SelfMemoryLoop,
            )

            sml = SelfMemoryLoop()
            wm = WorkingMemory()
            summary = wm.summary()
            outcome = (
                'success' if event.value in ('COMPLETED', 'STOPPED') else 'failure'
            )

            result = await sml.reflect(
                task_description=f'Conversation {conversation_id}',
                outcome=outcome,
                observations=summary[:500],
                tags=['auto-reflection', event.value.lower()],
            )

            _logger.info(
                'ReflectionProcessor: conversation=%s outcome=%s lessons=%d',
                conversation_id,
                outcome,
                len(result.get('lessons', [])),
            )

            return EventCallbackResult(
                status=EventCallbackResultStatus.SUCCESS,
                event_callback_id=callback.id,
                event_id=event.id,
                conversation_id=conversation_id,
                metadata={'reflection': result},
            )
        except Exception as e:
            _logger.warning('ReflectionProcessor failed: %s', e)
            return None


def _is_terminal(status_value: str) -> bool:
    try:
        return ConversationExecutionStatus(status_value).is_terminal()
    except (ValueError, AttributeError):
        return status_value.upper() in (
            'COMPLETED',
            'ERROR',
            'STUCK',
            'CANCELLED',
            'STOPPED',
        )
