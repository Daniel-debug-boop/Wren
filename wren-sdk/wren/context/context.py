"""Agent context for Wren SDK.

Provides the execution context for an agent run, including
message history, tool registry, and event logging.
"""

from __future__ import annotations

import logging
from typing import Any

from wren.event.store import EventLog
from wren.llm.message import Message, MessageRole
from wren.tool.registry import ToolRegistry
from wren.tool.manifest import CapabilityManifest
from wren.tool.guardrail import GuardrailEnforcer

logger = logging.getLogger("wren.agent.context")


class AgentContext:
    """Execution context for an agent run.

    Holds all state needed during agent execution:
    - Message history
    - Tool registry and guardrails
    - Event log
    - System prompt
    """

    def __init__(
        self,
        system_prompt: str = "",
        tool_registry: ToolRegistry | None = None,
        guardrails: GuardrailEnforcer | None = None,
        event_log: EventLog | None = None,
        max_turns: int = 50,
        metadata: dict[str, Any] | None = None,
    ):
        self.system_prompt = system_prompt
        self.tool_registry = tool_registry or ToolRegistry()
        self.guardrails = guardrails or GuardrailEnforcer.default()
        self.event_log = event_log or EventLog()
        self.max_turns = max_turns
        self.metadata = metadata or {}

        # Message history
        self._messages: list[Message] = []

        # State
        self._turn_count = 0
        self._total_tool_calls = 0
        self._total_tokens = 0

    @property
    def messages(self) -> list[Message]:
        """Get message history."""
        return list(self._messages)

    @property
    def turn_count(self) -> int:
        """Get current turn count."""
        return self._turn_count

    @property
    def total_tool_calls(self) -> int:
        """Get total tool calls made."""
        return self._total_tool_calls

    @property
    def total_tokens(self) -> int:
        """Get total tokens used."""
        return self._total_tokens

    def add_message(self, message: Message) -> None:
        """Add a message to history."""
        self._messages.append(message)

    def get_messages_for_llm(self) -> list[Message]:
        """Get messages formatted for LLM consumption.

        Includes system prompt as first message.
        """
        messages = []

        # Build full system prompt with capabilities
        full_system_prompt = self._build_system_prompt()
        if full_system_prompt:
            messages.append(Message.system(full_system_prompt))

        # Add conversation history
        messages.extend(self._messages)

        return messages

    def increment_turn(self) -> None:
        """Increment turn counter."""
        self._turn_count += 1

    def add_tool_call(self) -> None:
        """Record a tool call."""
        self._total_tool_calls += 1

    def add_tokens(self, count: int) -> None:
        """Record token usage."""
        self._total_tokens += count

    def is_complete(self) -> bool:
        """Check if agent should stop.

        Stops when:
        - Max turns reached
        - Agent sends FINISH action
        """
        return self._turn_count >= self.max_turns

    def _build_system_prompt(self) -> str:
        """Build complete system prompt with capabilities."""
        parts = []

        # Base system prompt
        if self.system_prompt:
            parts.append(self.system_prompt)

        # Add capability manifest
        manifest = CapabilityManifest(self.tool_registry)
        parts.append(manifest.to_prompt())

        return "\n\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Serialize context to dict."""
        return {
            "system_prompt": self.system_prompt,
            "messages": [m.to_dict() for m in self._messages],
            "turn_count": self._turn_count,
            "total_tool_calls": self._total_tool_calls,
            "total_tokens": self._total_tokens,
            "metadata": self.metadata,
        }
