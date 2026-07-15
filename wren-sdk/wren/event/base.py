"""Event system for Wren SDK.

Events are the core communication mechanism between agent components.
All agent actions, LLM responses, and tool calls produce events.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import Field

from wren.utils.models import WrenModel, utc_now


class EventType(str, Enum):
    """Core event types."""

    # Message events
    MESSAGE = "message"
    SYSTEM_MESSAGE = "system_message"
    USER_MESSAGE = "user_message"
    ASSISTANT_MESSAGE = "assistant_message"

    # Tool events
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"

    # LLM events
    LLM_START = "llm_start"
    LLM_CHUNK = "llm_chunk"
    LLM_END = "llm_end"
    LLM_ERROR = "llm_error"

    # Conversation events
    CONVERSATION_START = "conversation_start"
    CONVERSATION_END = "conversation_end"
    CONVERSATION_ERROR = "conversation_error"

    # Agent events
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    AGENT_THINK = "agent_think"

    # Hook events
    HOOK_BEFORE = "hook_before"
    HOOK_AFTER = "hook_after"
    HOOK_ERROR = "hook_error"


class Event(WrenModel):
    """Base event class.

    All events in Wren SDK inherit from this.
    Events are immutable and can be serialized.
    """

    event_id: str = Field(default_factory=lambda: uuid4().hex)
    event_type: EventType
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @abstractmethod
    def to_prompt(self) -> str:
        """Convert event to prompt string for LLM context."""
        ...

    def with_metadata(self, **kwargs: Any) -> Event:
        """Create copy with additional metadata."""
        return self.model_copy(update={"metadata": {**self.metadata, **kwargs}})


class MessageEvent(Event):
    """A text message event."""

    event_type: EventType = EventType.MESSAGE
    role: str  # "user", "assistant", "system"
    content: str

    def to_prompt(self) -> str:
        return f"[{self.role}]: {self.content}"


class ToolCallEvent(Event):
    """A tool invocation event."""

    event_type: EventType = EventType.TOOL_CALL
    tool_name: str
    tool_args: dict[str, Any]
    tool_call_id: str = Field(default_factory=lambda: uuid4().hex)

    def to_prompt(self) -> str:
        args_str = ", ".join(f"{k}={v!r}" for k, v in self.tool_args.items())
        return f"[tool_call]: {self.tool_name}({args_str})"


class ToolResultEvent(Event):
    """A tool result event."""

    event_type: EventType = EventType.TOOL_RESULT
    tool_name: str
    tool_call_id: str
    result: str
    success: bool = True
    duration_ms: float | None = None

    def to_prompt(self) -> str:
        status = "ok" if self.success else "error"
        return f"[tool_result:{status}]: {self.result[:500]}"


class LLMChunkEvent(Event):
    """An LLM streaming chunk event."""

    event_type: EventType = EventType.LLM_CHUNK
    delta: str
    model: str | None = None
    finish_reason: str | None = None
    usage: dict[str, int] | None = None

    def to_prompt(self) -> str:
        return self.delta


class ConversationStartEvent(Event):
    """Conversation started event."""

    event_type: EventType = EventType.CONVERSATION_START
    task: str
    agent_name: str | None = None


class ConversationEndEvent(Event):
    """Conversation ended event."""

    event_type: EventType = EventType.CONVERSATION_END
    success: bool = True
    summary: str | None = None
    total_tokens: int | None = None
    total_tool_calls: int | None = None
