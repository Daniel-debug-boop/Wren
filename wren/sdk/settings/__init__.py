"""Compatibility bridge for ``wren.sdk.settings``.

Re-exports the agent/conversation settings models from their actual location
in :mod:`wren.settings` so ``from wren.sdk.settings import
OpenHandsAgentSettings`` keeps working.
"""

from __future__ import annotations

from wren.settings import (
    ACPAgentSettings,
    ACP_PROVIDERS,
    AGENT_SETTINGS_SCHEMA_VERSION,
    AgentKind,
    AgentSettingsConfig,
    AgentSettingsConfigDict,
    CondenserSettings,
    ConversationSettings,
    LLMSettings,
    OpenHandsAgentSettings,
    Settings,
    SettingsChoice,
    SettingsFieldSchema,
    SettingsSchema,
    SettingsSectionSchema,
    VerificationSettings,
    apply_agent_settings_diff,
    default_agent_settings,
    detect_acp_provider_by_command,
    export_agent_settings_schema,
    validate_agent_settings,
)

__all__ = [
    'ACPAgentSettings',
    'ACP_PROVIDERS',
    'AGENT_SETTINGS_SCHEMA_VERSION',
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
    'SettingsSchema',
    'SettingsSectionSchema',
    'VerificationSettings',
    'apply_agent_settings_diff',
    'default_agent_settings',
    'detect_acp_provider_by_command',
    'export_agent_settings_schema',
    'validate_agent_settings',
]
