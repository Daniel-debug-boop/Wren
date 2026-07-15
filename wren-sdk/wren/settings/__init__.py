"""Settings exports."""

from typing import Any

from wren.settings.settings import (
    Settings,
    LLMSettings,
    WorkspaceSettings,
    AgentSettings,
)


class ACPAgentSettings:
    """ACP Agent settings."""

    def __init__(self, **kwargs: Any):
        for k, v in kwargs.items():
            setattr(self, k, v)


ACP_PROVIDERS: dict[str, Any] = {}


__all__ = [
    "Settings",
    "LLMSettings",
    "WorkspaceSettings",
    "AgentSettings",
    "ACPAgentSettings",
    "ACP_PROVIDERS",
]
