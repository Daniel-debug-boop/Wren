"""Event exports."""

from typing import NewType

from wren.event.base import (
    Event,
    EventType,
    MessageEvent,
    ToolCallEvent,
    ToolResultEvent,
    LLMChunkEvent,
    ConversationStartEvent,
    ConversationEndEvent,
)
from wren.event.store import EventLog

# Type aliases
EventID = NewType("EventID", str)


class ConversationStateUpdateEvent(Event):
    """Conversation state update event."""

    event_type: EventType = EventType.CONVERSATION_START
    state: str = ""


class ObservationEvent(Event):
    """Observation event from tool execution."""

    event_type: EventType = EventType.TOOL_RESULT
    observation: str = ""


__all__ = [
    "Event",
    "EventType",
    "MessageEvent",
    "ToolCallEvent",
    "ToolResultEvent",
    "LLMChunkEvent",
    "ConversationStartEvent",
    "ConversationEndEvent",
    "EventLog",
    "EventID",
    "ConversationStateUpdateEvent",
    "ObservationEvent",
]
