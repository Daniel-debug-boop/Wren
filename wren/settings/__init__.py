"""Settings models for Wren.

The agent settings (``OpenHandsAgentSettings`` / ``ACPAgentSettings``) are a
discriminated union on ``agent_kind`` and carry an ``llm`` (see
:mod:`wren.llm`), ``condenser`` and ``verification`` (see
:mod:`wren.settings.model`) configuration. Conversation settings
(``max_iterations``, ``confirmation_mode``, ``security_analyzer``) live in
:class:`ConversationSettings`.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal, TypeAlias, Union

from fastmcp.mcp_config import MCPConfig
from pydantic import BaseModel, Field

from wren.llm import LLM
from wren.settings.model import (
    AGENT_SETTINGS_SCHEMA_VERSION,
    CondenserSettings,
    VerificationSettings,
)

__all__ = [
    'AGENT_SETTINGS_SCHEMA_VERSION',
    'ACPAgentSettings',
    'ACP_PROVIDERS',
    'AgentKind',
    'AgentSettingsConfig',
    'AgentSettingsConfigDict',
    'CondenserSettings',
    'ConversationSettings',
    'LLMSettings',
    'OpenHandsAgentSettings',
    'Settings',
    'SettingsChoice',
    'SettingsFieldSchema',
    'SettingsSectionSchema',
    'SettingsSchema',
    'VerificationSettings',
    'apply_agent_settings_diff',
    'default_agent_settings',
    'detect_acp_provider_by_command',
    'export_agent_settings_schema',
    'validate_agent_settings',
]


class AgentKind(str, Enum):
    """Kind of agent."""

    CODER = 'coder'
    PLANNER = 'planner'
    GENERAL = 'general'


# ── Settings schema helpers (used by settings_router) ─────────────────────


class SettingsChoice(str, Enum):
    """Setting choice type."""

    BOOLEAN = 'boolean'
    STRING = 'string'
    INTEGER = 'integer'
    FLOAT = 'float'


class SettingsFieldSchema(BaseModel):
    """Schema for a single settings field."""

    key: str
    label: str
    type: SettingsChoice
    default: Any = None
    description: str | None = None


class SettingsSectionSchema(BaseModel):
    """Schema for a settings section."""

    key: str
    label: str
    fields: list[SettingsFieldSchema]


class SettingsSchema(BaseModel):
    """Top-level settings schema."""

    sections: list[SettingsSectionSchema]


def export_agent_settings_schema() -> SettingsSchema:
    """Export the agent settings schema."""
    return SettingsSchema(
        sections=[
            SettingsSectionSchema(
                key='general',
                label='General',
                fields=[
                    SettingsFieldSchema(
                        key='model',
                        label='Model',
                        type=SettingsChoice.STRING,
                        default='gpt-4o',
                        description='LLM model to use',
                    ),
                    SettingsFieldSchema(
                        key='enable_sub_agents',
                        label='Enable sub-agents',
                        type=SettingsChoice.BOOLEAN,
                        default=False,
                        description='Allow the agent to spawn sub-agents',
                    ),
                    SettingsFieldSchema(
                        key='temperature',
                        label='Temperature',
                        type=SettingsChoice.FLOAT,
                        default=0.7,
                        description='LLM temperature setting',
                    ),
                    SettingsFieldSchema(
                        key='max_tokens',
                        label='Max Tokens',
                        type=SettingsChoice.INTEGER,
                        default=4096,
                        description='Maximum tokens per response',
                    ),
                ],
            ),
            SettingsSectionSchema(
                key='verification',
                label='Verification',
                fields=[
                    SettingsFieldSchema(
                        key='verification.critic_enabled',
                        label='Enable critic',
                        type=SettingsChoice.BOOLEAN,
                        default=True,
                        description='Run the critic over agent actions',
                    ),
                    SettingsFieldSchema(
                        key='verification.enable_iterative_refinement',
                        label='Iterative refinement',
                        type=SettingsChoice.BOOLEAN,
                        default=False,
                        description='Refine agent output until the critic passes',
                    ),
                ],
            ),
        ],
    )


# ── Conversation settings ─────────────────────────────────────────────────


class ConversationSettings(BaseModel):
    """Conversation-level settings."""

    max_iterations: int = 50
    confirmation_mode: bool = False
    security_analyzer: str = 'none'
    # Conversation-start fields (mirrors the software-agent-sdk layout).
    workspace: Any = None
    conversation_id: str | None = None
    initial_message: Any = None
    plugins: list[Any] | None = None
    secrets: dict[str, Any] | None = None

    @classmethod
    def from_persisted(cls, data: dict[str, Any]) -> ConversationSettings:
        """Load from persisted data."""
        return cls.model_validate(data)

    @classmethod
    def create_request(cls, model_class: type[Any], **kwargs: Any) -> Any:
        """Build a conversation start request from these settings.

        Conversation-level settings (``max_iterations``, ``confirmation_mode``,
        ``security_analyzer``, ``workspace``, ``conversation_id``,
        ``initial_message``, ``plugins``, ``secrets``) flow onto the request;
        caller-provided kwargs (``agent``, ``user_id``, ...) take precedence.
        """
        payload: dict[str, Any] = {
            'max_iterations': cls.max_iterations,
            'confirmation_mode': cls.confirmation_mode,
            'security_analyzer': cls.security_analyzer,
        }
        for field in (
            'workspace',
            'conversation_id',
            'initial_message',
            'plugins',
            'secrets',
        ):
            value = getattr(cls, field, None)
            if value is not None:
                payload[field] = value
        payload.update(kwargs)
        return model_class(**payload)


# ── Agent settings ────────────────────────────────────────────────────────


class LLMSettings(BaseModel):
    """LLM configuration settings (kept for backward compatibility)."""

    model: str = 'gpt-4o'
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096


class OpenHandsAgentSettings(BaseModel):
    """OpenHands-style agent settings (``agent_kind == 'wren'``)."""

    schema_version: int = AGENT_SETTINGS_SCHEMA_VERSION
    agent_kind: Literal['wren'] = 'wren'
    agent: str = 'wren'
    llm: LLM = Field(default_factory=LLM)
    condenser: CondenserSettings | None = None
    verification: VerificationSettings | None = None
    mcp_config: MCPConfig | None = None
    tools: list[Any] = Field(default_factory=list)
    include_default_tools: list[str] = Field(default_factory=list)
    agent_context: Any = None
    enable_sub_agents: bool = False

    def create_agent(self) -> Any:
        """Build the SDK :class:`~wren.agent.Agent` for this configuration."""
        from wren.agent import Agent
        from wren.context.condenser import LLMSummarizingCondenser

        condenser = None
        if self.condenser is not None and getattr(self.condenser, 'enabled', True):
            condenser = LLMSummarizingCondenser(
                llm=self.llm,
                max_size=getattr(self.condenser, 'max_size', 240),
                keep_first=getattr(self.condenser, 'keep_first', 2),
            )

        return Agent(
            name=self.agent,
            llm=self.llm,
            tools=list(self.tools or []),
            include_default_tools=list(self.include_default_tools or []),
            condenser=condenser,
            mcp_config=self.mcp_config,
        )


class ACPAgentSettings(BaseModel):
    """ACP (Agent Client Protocol) agent settings (``agent_kind == 'acp'``)."""

    schema_version: int = AGENT_SETTINGS_SCHEMA_VERSION
    agent_kind: Literal['acp'] = 'acp'
    acp_server: str | None = None
    acp_model: str | None = None
    acp_command: list[str] = Field(default_factory=list)
    acp_args: list[str] = Field(default_factory=list)
    agent_context: Any = None
    llm: LLM = Field(default_factory=LLM)


AgentSettingsConfigDict = AgentKind

# Discriminated union of the two concrete agent-setting variants.
AgentSettingsConfig: TypeAlias = Union[OpenHandsAgentSettings, ACPAgentSettings]


def default_agent_settings() -> OpenHandsAgentSettings:
    """Get default agent settings."""
    return OpenHandsAgentSettings()


def _deep_merge(base: dict[str, Any], diff: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``diff`` onto ``base`` (nested dicts merge)."""
    out = dict(base)
    for key, value in diff.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def validate_agent_settings(
    settings: dict[str, Any] | AgentSettingsConfig,
) -> AgentSettingsConfig:
    """Validate/normalize agent settings into the discriminated union.

    Canonicalizes the legacy ``agent_kind: 'llm'`` tag to ``'wren'`` so every
    read lands on the ``{wren, acp}`` variants.
    """
    if isinstance(settings, (OpenHandsAgentSettings, ACPAgentSettings)):
        return settings

    data = dict(settings or {})
    kind = data.get('agent_kind')
    if kind == 'llm':
        data['agent_kind'] = 'wren'

    if data.get('agent_kind') == 'acp':
        return ACPAgentSettings.model_validate(data)
    return OpenHandsAgentSettings.model_validate(data)


def apply_agent_settings_diff(
    current: AgentSettingsConfig,
    diff: dict[str, Any],
) -> AgentSettingsConfig:
    """Apply a diff to agent settings.

    A change of ``agent_kind`` starts from a fresh base for the new kind
    (cross-kind config is not carried over); within a variant the diff is
    deep-merged so sibling sub-fields (``llm``, ``condenser``, ...) survive.
    ``mcp_config`` is replaced wholesale by the caller.
    """
    current_dump = current.model_dump(mode='json', context={'expose_secrets': True})
    current_kind = current_dump.get('agent_kind', 'wren')
    new_kind = diff.get('agent_kind')

    if new_kind and new_kind != current_kind:
        merged: dict[str, Any] = {
            'agent_kind': new_kind,
            'schema_version': AGENT_SETTINGS_SCHEMA_VERSION,
        }
        merged = _deep_merge(merged, diff)
    else:
        merged = _deep_merge(current_dump, diff)
        if 'mcp_config' in diff:
            merged['mcp_config'] = diff['mcp_config']

    return validate_agent_settings(merged)


# ── ACP providers ─────────────────────────────────────────────────────────


class ACPProviderInfo:
    """Information about a detected ACP provider."""

    def __init__(self, key: str, **kwargs: Any):
        self.key = key
        for k, v in kwargs.items():
            setattr(self, k, v)


ACP_PROVIDERS: dict[str, dict[str, Any]] = {}


def detect_acp_provider_by_command(command: str | list[str]) -> ACPProviderInfo | None:
    """Detect ACP provider from a command string or argument list.

    Returns an ``ACPProviderInfo`` with ``.key`` matching a provider key in
    ``ACP_PROVIDERS``, or ``None`` if no match.
    """
    if not command:
        return None
    if isinstance(command, (list, tuple)):
        command = ' '.join(str(part) for part in command)
    for provider_key, provider_config in ACP_PROVIDERS.items():
        patterns = provider_config.get('command_patterns', [])
        for pattern in patterns:
            if pattern in command:
                return ACPProviderInfo(key=provider_key, **provider_config)
    return None


class Settings(BaseModel):
    """Aggregate settings (kept for backward compatibility)."""

    llm: LLMSettings = Field(default_factory=LLMSettings)
    workspace_root: str = '.'
