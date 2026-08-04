"""Event types for the Wren app server.

Extends ``__path__`` to include the SDK's ``wren-sdk/wren/event/``
directory so that ``from wren.event.base import ...`` resolves to the
SDK's native event implementation.

The app-server-specific event subclasses (ActionEvent, ObservationEvent,
ConversationStateUpdateEvent) are defined here because the vendored SDK
copy is older than the event API the app server consumes.
"""

from __future__ import annotations

import os as _os
from typing import Any

from pydantic import Field

# Extend __path__ to include the SDK's event module directory so submodule
# imports (e.g. ``from wren.event.base import Event``) resolve correctly.
_repo_root = _os.path.dirname(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
)
_sdk_event_dir = _os.path.join(_repo_root, 'wren-sdk', 'wren', 'event')
if _os.path.isdir(_sdk_event_dir) and _sdk_event_dir not in __path__:
    __path__.append(_sdk_event_dir)

# Import from the SDK's event submodule (now resolvable via the extended path).
from wren.event.base import (
    Event as Event,
    EventType as EventType,
    MessageEvent as MessageEvent,
    ToolCallEvent as ToolCallEvent,
    ToolResultEvent as ToolResultEvent,
    LLMChunkEvent as LLMChunkEvent,
    ConversationStartEvent as ConversationStartEvent,
    ConversationEndEvent as ConversationEndEvent,
)

# EventID is a string alias in the Wren SDK
EventID = str


class ActionEvent(Event):
    """An agent action/thought event."""

    event_type: EventType = EventType.AGENT_THINK
    thought: str = ''

    def to_prompt(self) -> str:
        return f"[action]: {self.thought}"


class ObservationEvent(Event):
    """Observation event from tool execution."""

    event_type: EventType = EventType.TOOL_RESULT
    observation: Any = None
    content: str = ''
    error: str = ''

    def to_prompt(self) -> str:
        if self.error:
            return f"[observation:error]: {self.error}"
        return f"[observation]: {self.content or self.observation}"


class ConversationStateUpdateEvent(Event):
    """Conversation state update event (key/value pairs)."""

    event_type: EventType = EventType.CONVERSATION_START
    key: str = ''
    value: Any = ''
    state: str = ''

    def to_prompt(self) -> str:
        rendered = self.state if self.state else self.value
        return f"[state:{self.key}]: {rendered}"


class PauseEvent(Event):
    """Agent paused event."""

    event_type: EventType = EventType.PAUSE
    source: str = ''

    def to_prompt(self) -> str:
        return f"[pause]: {self.source}"


class TokenEvent(Event):
    """Token usage event."""

    event_type: EventType = EventType.TOKEN
    source: str = ''
    prompt_token_ids: list[int] = Field(default_factory=list)
    response_token_ids: list[int] = Field(default_factory=list)

    def to_prompt(self) -> str:
        return (
            f"[tokens:{self.source}]: prompt={len(self.prompt_token_ids)}"
            f" response={len(self.response_token_ids)}"
        )


__all__ = [
    'Event',
    'EventType',
    'MessageEvent',
    'ToolCallEvent',
    'ToolResultEvent',
    'LLMChunkEvent',
    'ConversationStartEvent',
    'ConversationEndEvent',
    'ActionEvent',
    'ObservationEvent',
    'ConversationStateUpdateEvent',
    'PauseEvent',
    'TokenEvent',
    'EventID',
]
