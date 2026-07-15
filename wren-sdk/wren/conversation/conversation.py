"""Conversation lifecycle for Wren SDK.

Manages the conversation between user, agent, and tools.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, AsyncIterator, Callable

from wren.context.context import AgentContext
from wren.event.base import (
    Event,
    EventType,
    ConversationStartEvent,
    ConversationEndEvent,
    MessageEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from wren.event.store import EventLog
from wren.llm.client import LLMClient, LLMResponse, LLMStreamChunk
from wren.llm.message import Message, MessageRole, ToolUseContent, ToolResultContent
from wren.tool.base import Action, Observation
from wren.tool.registry import ToolRegistry
from wren.tool.guardrail import GuardrailEnforcer
from wren.utils.models import WrenModel

logger = logging.getLogger("wren.conversation")


class ConversationState(str, Enum):
    """Conversation state."""

    IDLE = "idle"
    RUNNING = "running"
    WAITING_FOR_TOOL = "waiting_for_tool"
    COMPLETE = "complete"
    ERROR = "error"
    CANCELLED = "cancelled"


class ConversationStats(WrenModel):
    """Statistics for a conversation."""

    total_messages: int = 0
    total_tool_calls: int = 0
    total_tokens: int = 0
    total_duration_ms: float = 0


class Conversation:
    """Manages a conversation between user, agent, and tools.

    This is the main orchestration class that:
    1. Takes user input
    2. Sends to LLM
    3. Executes tool calls
    4. Returns results
    5. Repeats until done
    """

    def __init__(
        self,
        llm: LLMClient,
        tool_registry: ToolRegistry | None = None,
        guardrails: GuardrailEnforcer | None = None,
        event_log: EventLog | None = None,
        system_prompt: str = "",
        max_turns: int = 50,
        on_event: Callable[[Event], None] | None = None,
    ):
        self.llm = llm
        self.tool_registry = tool_registry or ToolRegistry()
        self.guardrails = guardrails or GuardrailEnforcer.default()
        self.event_log = event_log or EventLog()
        self.system_prompt = system_prompt
        self.max_turns = max_turns
        self.on_event = on_event

        # State
        self._state = ConversationState.IDLE
        self._context: AgentContext | None = None
        self._stats = ConversationStats()

    @property
    def state(self) -> ConversationState:
        """Get current conversation state."""
        return self._state

    @property
    def stats(self) -> ConversationStats:
        """Get conversation statistics."""
        return self._stats

    @property
    def context(self) -> AgentContext | None:
        """Get the current agent context."""
        return self._context

    async def run(self, task: str) -> str:
        """Run a complete conversation.

        Args:
            task: The user's task/request.

        Returns:
            Final response from the agent.
        """
        # Initialize context
        self._context = AgentContext(
            system_prompt=self.system_prompt,
            tool_registry=self.tool_registry,
            guardrails=self.guardrails,
            event_log=self.event_log,
            max_turns=self.max_turns,
        )

        # Emit start event
        start_event = ConversationStartEvent(task=task)
        self.event_log.add(start_event)
        self._emit(start_event)

        self._state = ConversationState.RUNNING

        # Add user message
        user_message = Message.user(task)
        self._context.add_message(user_message)

        try:
            response = await self._run_agent_loop()
            self._state = ConversationState.COMPLETE

            # Emit end event
            end_event = ConversationEndEvent(
                success=True,
                summary=response[:500] if response else None,
                total_tokens=self._stats.total_tokens,
                total_tool_calls=self._stats.total_tool_calls,
            )
            self.event_log.add(end_event)
            self._emit(end_event)

            return response

        except Exception as e:
            self._state = ConversationState.ERROR
            logger.error(f"Conversation failed: {e}")

            end_event = ConversationEndEvent(
                success=False,
                summary=str(e),
            )
            self.event_log.add(end_event)
            self._emit(end_event)

            raise

    async def step(self, user_input: str) -> AsyncIterator[Event]:
        """Single step of conversation (for streaming UI).

        Yields events as they happen.
        """
        if self._context is None:
            self._context = AgentContext(
                system_prompt=self.system_prompt,
                tool_registry=self.tool_registry,
                guardrails=self.guardrails,
                event_log=self.event_log,
                max_turns=self.max_turns,
            )

        # Add user message
        user_message = Message.user(user_input)
        self._context.add_message(user_message)

        # Get LLM response
        self._state = ConversationState.RUNNING
        messages = self._context.get_messages_for_llm()
        tools = self.tool_registry.get_openai_tools()

        async for chunk in self.llm.chat_stream(messages, tools=tools if tools else None):
            if chunk.delta:
                yield LLMChunkEvent(
                    delta=chunk.delta,
                    model=chunk.model,
                    finish_reason=chunk.finish_reason,
                )

            if chunk.tool_call_delta:
                yield ToolCallEvent(
                    tool_name=chunk.tool_call_delta.name,
                    tool_args=chunk.tool_call_delta.arguments,
                    tool_call_id=chunk.tool_call_delta.id,
                )

    async def _run_agent_loop(self) -> str:
        """Run the agent loop until completion."""
        while not self._context.is_complete():
            self._context.increment_turn()

            # Get LLM response
            messages = self._context.get_messages_for_llm()
            tools = self.tool_registry.get_openai_tools()

            response = await self.llm.chat(
                messages,
                tools=tools if tools else None,
            )

            # Track usage
            if response.usage:
                self._stats.total_tokens += response.usage.total_tokens
                self._context.add_tokens(response.usage.total_tokens)

            # Add assistant message
            if response.content:
                assistant_message = Message.assistant(response.content)
                self._context.add_message(assistant_message)

            # Handle tool calls
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    self._stats.total_tool_calls += 1
                    self._context.add_tool_call()

                    # Emit tool call event
                    tool_call_event = ToolCallEvent(
                        tool_name=tool_call.name,
                        tool_args=tool_call.arguments,
                        tool_call_id=tool_call.id,
                    )
                    self.event_log.add(tool_call_event)
                    self._emit(tool_call_event)

                    # Execute tool
                    action = Action(
                        tool_name=tool_call.name,
                        arguments=tool_call.arguments,
                        action_id=tool_call.id,
                    )

                    # Check guardrails
                    tool_def = self.tool_registry.get_definition(tool_call.name)
                    if tool_def:
                        guardrail_result = self.guardrails.check(tool_def, action)
                        if not guardrail_result.allowed:
                            observation = Observation(
                                success=False,
                                result="",
                                error=f"Blocked by guardrail: {guardrail_result.reason}",
                                action_id=tool_call.id,
                            )
                        else:
                            observation = await self.tool_registry.execute(tool_call.name, action)
                    else:
                        observation = Observation(
                            success=False,
                            result="",
                            error=f"Tool not found: {tool_call.name}",
                            action_id=tool_call.id,
                        )

                    # Emit tool result event
                    result_event = ToolResultEvent(
                        tool_name=tool_call.name,
                        tool_call_id=tool_call.id,
                        result=observation.result
                        if observation.success
                        else observation.error or "",
                        success=observation.success,
                    )
                    self.event_log.add(result_event)
                    self._emit(result_event)

                    # Add tool result to messages
                    tool_result_content = ToolResultContent(
                        tool_use_id=tool_call.id,
                        content=observation.result
                        if observation.success
                        else f"Error: {observation.error}",
                        is_error=not observation.success,
                    )
                    tool_result_message = Message(
                        role=MessageRole.TOOL,
                        content=[tool_result_content],
                        tool_call_id=tool_call.id,
                    )
                    self._context.add_message(tool_result_message)

                # Continue loop for more tool calls
                continue

            # No tool calls — we're done
            return response.content

        return "Max turns reached"


class LLMChunkEvent(Event):
    """LLM streaming chunk event."""

    event_type: EventType = EventType.LLM_CHUNK
    delta: str = ""
    model: str | None = None
    finish_reason: str | None = None

    def to_prompt(self) -> str:
        return self.delta
