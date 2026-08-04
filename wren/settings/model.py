"""Agent settings sub-models and schema version for Wren.

Separated from :mod:`wren.settings` so that
``from wren.sdk.settings.model import AGENT_SETTINGS_SCHEMA_VERSION`` (and the
app-server equivalents) resolves without importing the full settings module.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# Bump when the persisted agent-settings shape changes incompatibly.
# ``OpenHandsAgentSettings.model_dump()`` emits this so loaders can run
# migrations when reading older rows.
AGENT_SETTINGS_SCHEMA_VERSION = 3


class CondenserSettings(BaseModel):
    """Conversation-history condenser settings."""

    enabled: bool = True
    max_size: int = 240
    keep_first: int = 2


class VerificationSettings(BaseModel):
    """Critic/verification settings for the agent."""

    critic_enabled: bool = False
    critic_mode: str = 'auto'
    enable_iterative_refinement: bool = False
    critic_threshold: float = 0.7
    max_refinement_iterations: int = 3


__all__ = [
    'AGENT_SETTINGS_SCHEMA_VERSION',
    'CondenserSettings',
    'VerificationSettings',
]
