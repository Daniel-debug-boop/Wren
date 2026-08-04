"""Agent models for Wren SDK.

The app server and its tests consume the agent as a Pydantic model so that
it can be dumped to JSON (``ConversationInfo.agent``), deep-copied
(``Agent.model_copy(update=...)``) and discriminated from ``ACPAgent`` via
the ``agent_kind`` field. This native implementation replaces the earlier
imperative ``Agent`` class whose constructor took ``config=``/``on_event=``.
"""

from __future__ import annotations

from typing import Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from wren.context.condenser import LLMSummarizingCondenser
from wren.llm import LLM

__all__ = [
    'Agent',
    'AgentBase',
    'AgentConfig',
    'AgentUnion',
    'ACPAgent',
]


class AgentConfig(BaseModel):
    """Agent configuration (kept for backward compatibility)."""

    name: str = 'wren'
    model: str = 'gpt-4o'
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    max_turns: int = 50
    system_prompt: str = ''
    fallback_models: list[str] | None = None


class AgentBase(BaseModel):
    """Shared base for the ``Agent | ACPAgent`` discriminated union."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = 'wren'
    system_prompt_filename: str | None = None
    system_prompt_kwargs: dict[str, Any] = Field(default_factory=dict)
    # Non-optional on both arms of the union (webhook reads ``.llm.model``).
    llm: LLM = Field(default_factory=LLM)


class Agent(AgentBase):
    """OpenHands-style LLM agent (``agent_kind == 'wren'``)."""

    agent_kind: Literal['wren'] = 'wren'
    tools: list[Any] = Field(default_factory=list)
    include_default_tools: list[str] = Field(default_factory=list)
    condenser: LLMSummarizingCondenser | None = None
    mcp_config: Any = None


class ACPAgent(AgentBase):
    """Agent Protocol (ACP) agent (``agent_kind == 'acp'``)."""

    agent_kind: Literal['acp'] = 'acp'
    acp_command: list[str] = Field(default_factory=list)
    acp_args: list[str] = Field(default_factory=list)
    acp_server: str | None = None
    acp_model: str | None = None
    agent_context: Any = None


# Discriminated union used by the unified /api/conversations payload.
AgentUnion = Union[Agent, ACPAgent]
