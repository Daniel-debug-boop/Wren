"""Settings models for Wren."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentKind(str, Enum):
    """Kind of agent."""
    CODER = "coder"
    PLANNER = "planner"
    GENERAL = "general"


class SettingsChoice(str, Enum):
    """Setting choice type."""
    BOOLEAN = "boolean"
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"


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


class AgentSettingsConfig(BaseModel):
    """Agent settings configuration."""
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4096


class ConversationSettings(BaseModel):
    """Conversation settings."""
    max_turns: int = 50
    enable_planning: bool = False

    @classmethod
    def from_persisted(cls, data: dict[str, Any]) -> ConversationSettings:
        """Load from persisted data."""
        return cls(**data)

    @classmethod
    def export_schema(cls) -> SettingsSchema:
        """Export the schema definition."""
        return SettingsSchema(
            sections=[
                SettingsSectionSchema(
                    key="conversation",
                    label="Conversation",
                    fields=[
                        SettingsFieldSchema(
                            key="max_turns",
                            label="Max Turns",
                            type=SettingsChoice.INTEGER,
                            default=50,
                            description="Maximum number of conversation turns",
                        ),
                        SettingsFieldSchema(
                            key="enable_planning",
                            label="Enable Planning",
                            type=SettingsChoice.BOOLEAN,
                            default=False,
                            description="Enable planning mode",
                        ),
                    ],
                ),
            ],
        )


class OpenHandsAgentSettings(BaseModel):
    """OpenHands agent settings (kept for backward compat)."""
    agent_settings: AgentSettingsConfig | None = None
    conversation_settings: ConversationSettings | None = None


class ACPAgentSettings(BaseModel):
    """ACP agent settings."""
    provider: str | None = None
    model: str | None = None
    command: str | None = None
    acp_server: str | None = None


def default_agent_settings() -> OpenHandsAgentSettings:
    """Get default agent settings."""
    return OpenHandsAgentSettings()


def validate_agent_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Validate agent settings."""
    return settings


def apply_agent_settings_diff(
    current: OpenHandsAgentSettings,
    diff: dict[str, Any],
) -> OpenHandsAgentSettings:
    """Apply a diff to agent settings."""
    updated = current.model_dump()
    updated.update(diff)
    return OpenHandsAgentSettings(**updated)


def export_agent_settings_schema() -> SettingsSchema:
    """Export the agent settings schema."""
    return SettingsSchema(
        sections=[
            SettingsSectionSchema(
                key="agent",
                label="Agent",
                fields=[
                    SettingsFieldSchema(
                        key="model",
                        label="Model",
                        type=SettingsChoice.STRING,
                        default="gpt-4o",
                        description="LLM model to use",
                    ),
                    SettingsFieldSchema(
                        key="temperature",
                        label="Temperature",
                        type=SettingsChoice.FLOAT,
                        default=0.7,
                        description="LLM temperature setting",
                    ),
                    SettingsFieldSchema(
                        key="max_tokens",
                        label="Max Tokens",
                        type=SettingsChoice.INTEGER,
                        default=4096,
                        description="Maximum tokens per response",
                    ),
                ],
            ),
        ],
    )


# ACP Providers (minimal)
ACP_PROVIDERS: dict[str, dict[str, Any]] = {}


def detect_acp_provider_by_command(command: str) -> ACPProviderInfo | None:
    """Detect ACP provider from a command string.

    Returns an ``ACPProviderInfo`` with ``.key`` attribute matching the
    provider key in ``ACP_PROVIDERS``, or ``None`` if no match.
    """
    if not command:
        return None
    for provider_key, provider_config in ACP_PROVIDERS.items():
        patterns = provider_config.get("command_patterns", [])
        for pattern in patterns:
            if pattern in command:
                return ACPProviderInfo(key=provider_key, **provider_config)
    return None


class ACPProviderInfo:
    """Information about a detected ACP provider."""

    def __init__(self, key: str, **kwargs: Any):
        self.key = key
        for k, v in kwargs.items():
            setattr(self, k, v)


__all__ = [
    "AgentKind",
    "SettingsChoice",
    "SettingsFieldSchema",
    "SettingsSectionSchema",
    "SettingsSchema",
    "AgentSettingsConfig",
    "ConversationSettings",
    "OpenHandsAgentSettings",
    "ACPAgentSettings",
    "default_agent_settings",
    "validate_agent_settings",
    "apply_agent_settings_diff",
    "export_agent_settings_schema",
    "ACP_PROVIDERS",
    "detect_acp_provider_by_command",
]
