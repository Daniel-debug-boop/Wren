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

from pydantic import Field, model_validator

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

    # Token / pause events
    TOKEN = "token"
    PAUSE = "pause"

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
    kind: str = Field(
        default='',
        description=(
            'Concrete event class name. Set automatically from the class name '
            'on construction and persisted so stored events can be filtered '
            '(e.g. ``TokenEvent``) after a JSON round-trip.'
        ),
    )
    event_type: EventType
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def _default_kind_from_class_name(self) -> Event:
        """Default ``kind`` to the concrete class name unless already set."""
        if not self.kind:
            # ``WrenModel`` is frozen; bypass the frozen-instance guard.
            object.__setattr__(self, 'kind', self.__class__.__name__)
        return self

    @property
    def id(self) -> str:
        """Alias for ``event_id`` used by the event services."""
        return self.event_id

    def to_prompt(self) -> str:
        """Convert event to prompt string for LLM context.

        Subclasses override this with a richer representation. The default
        keeps the base ``Event`` instantiable so stored events can be
        rehydrated with ``Event.model_validate_json`` (the event services
        round-trip JSON through the base class).
        """
        return f"[{self.kind or self.__class__.__name__}]"

    def with_metadata(self, **kwargs: Any) -> Event:
        """Create copy with additional metadata."""
        return self.model_copy(update={"metadata": {**self.metadata, **kwargs}})


class MessageEvent(Event):
    """A text message event.

    Supports both the OpenHands-style payload (``source`` + ``llm_message``)
    used by the agent server webhook and the flat SDK style (``role`` +
    ``content``). At least one style must be populated.
    """

    event_type: EventType = EventType.MESSAGE
    source: str | None = None  # "user", "assistant", "system" (OpenHands style)
    llm_message: Any | None = None  # LLM Message with role/content
    role: str | None = None  # "user", "assistant", "system" (flat style)
    content: str | None = None

    def to_prompt(self) -> str:
        role = self.role or (self.source if self.source else 'user')
        content = self.content
        if content is None and self.llm_message is not None:
            content = getattr(self.llm_message, 'content', None)
        if isinstance(content, (list, tuple)):
            content = ' '.join(
                str(getattr(block, 'text', block))
                for block in content
                if block is not None
            )
        return f"[{role}]: {content or ''}"


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

    def to_prompt(self) -> str:
        return f"[conversation_start]: {self.task}"


class ConversationEndEvent(Event):
    """Conversation ended event."""

    event_type: EventType = EventType.CONVERSATION_END
    success: bool = True
    summary: str | None = None
    total_tokens: int | None = None
    total_tool_calls: int | None = None

    def to_prompt(self) -> str:
        return f"[conversation_end]: {self.summary or ''} tokens={self.total_tokens}"
