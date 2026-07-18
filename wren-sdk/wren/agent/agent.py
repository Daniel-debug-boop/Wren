"""Agent for Wren SDK.

The main agent class that orchestrates LLM, tools, and conversation.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from wren.context.context import AgentContext
from wren.context.prompt import PromptBuilder
from wren.conversation.conversation import Conversation, ConversationState
from wren.event.base import Event
from wren.event.store import EventLog
from wren.llm.client import LLMClient, LLMConfig
from wren.tool.base import Tool
from wren.tool.registry import ToolRegistry
from wren.tool.guardrail import GuardrailEnforcer
from wren.utils.models import WrenModel

logger = logging.getLogger("wren.agent")


class AgentConfig(WrenModel):
    """Agent configuration."""

    name: str = "wren"
    model: str = "gpt-4o"
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    max_turns: int = 50
    system_prompt: str = ""
    fallback_models: list[str] | None = None


class Agent:
    """The main Wren agent.

    Orchestrates:
    - LLM communication
    - Tool execution
    - Conversation management
    - Event handling

    Usage:
        agent = Agent(config=AgentConfig(model="gpt-4o"))
        agent.register_tool(MyTool())
        response = await agent.run("Fix the bug in auth.py")
    """

    def __init__(
        self,
        config: AgentConfig | None = None,
        on_event: Callable[[Event], None] | None = None,
    ):
        self.config = config or AgentConfig()

        # Initialize components
        self._tool_registry = ToolRegistry()
        self._guardrails = GuardrailEnforcer.default()
        self._event_log = EventLog()
        self._llm = LLMClient(
            LLMConfig(
                model=self.config.model,
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                fallback_models=self.config.fallback_models,
            )
        )

        # Event callback
        self._on_event = on_event

    @property
    def tool_registry(self) -> ToolRegistry:
        """Get the tool registry."""
        return self._tool_registry

    @property
    def guardrails(self) -> GuardrailEnforcer:
        """Get the guardrail enforcer."""
        return self._guardrails

    @property
    def event_log(self) -> EventLog:
        """Get the event log."""
        return self._event_log

    @property
    def llm(self) -> LLMClient:
        """Get the LLM client."""
        return self._llm

    def register_tool(self, tool: Tool) -> Agent:
        """Register a tool with the agent.

        Args:
            tool: Tool instance to register.

        Returns:
            Self for chaining.
        """
        self._tool_registry.register(tool)
        return self

    def register_tools(self, tools: list[Tool]) -> Agent:
        """Register multiple tools.

        Args:
            tools: List of tool instances.

        Returns:
            Self for chaining.
        """
        for tool in tools:
            self._tool_registry.register(tool)
        return self

    async def run(self, task: str) -> str:
        """Run the agent on a task.

        Args:
            task: The task to accomplish.

        Returns:
            Agent's response.
        """
        # Build conversation
        conversation = Conversation(
            llm=self._llm,
            tool_registry=self._tool_registry,
            guardrails=self._guardrails,
            event_log=self._event_log,
            system_prompt=self._build_system_prompt(),
            max_turns=self.config.max_turns,
            on_event=self._on_event,
        )

        # Run
        response = await conversation.run(task)

        # Log stats
        stats = conversation.stats
        logger.info(
            f"Agent '{self.config.name}' completed: "
            f"{stats.total_messages} messages, "
            f"{stats.total_tool_calls} tool calls, "
            f"{stats.total_tokens} tokens"
        )

        return response

    def _build_system_prompt(self) -> str:
        """Build the system prompt."""
        builder = PromptBuilder(
            base_prompt=self.config.system_prompt,
            tool_registry=self._tool_registry,
        )
        return builder.build()

    def to_dict(self) -> dict[str, Any]:
        """Serialize agent to dict."""
        return {
            "config": self.config.to_dict(),
            "tools": [t.get_definition().name for t in self._tool_registry.list_all()],
            "stats": {
                "events": len(self._event_log),
            },
        }
