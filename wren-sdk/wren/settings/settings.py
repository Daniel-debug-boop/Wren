"""Settings for Wren SDK.

Configuration management with environment variable support.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import Field

from wren.utils.models import WrenModel


class LLMSettings(WrenModel):
    """LLM configuration settings."""

    model: str = Field(default="gpt-4o", alias="WREN_MODEL")
    api_key: str | None = Field(default=None, alias="WREN_API_KEY")
    base_url: str | None = Field(default=None, alias="WREN_BASE_URL")
    temperature: float = Field(default=0.7, alias="WREN_TEMPERATURE")
    max_tokens: int = Field(default=4096, alias="WREN_MAX_TOKENS")
    timeout: float = Field(default=120.0, alias="WREN_TIMEOUT")
    fallback_models: list[str] | None = Field(default=None, alias="WREN_FALLBACK_MODELS")


class WorkspaceSettings(WrenModel):
    """Workspace configuration settings."""

    root: str = Field(default=".", alias="WREN_WORKSPACE_ROOT")
    max_file_size: int = Field(default=10 * 1024 * 1024, alias="WREN_MAX_FILE_SIZE")  # 10MB


class AgentSettings(WrenModel):
    """Agent configuration settings."""

    name: str = Field(default="wren", alias="WREN_AGENT_NAME")
    max_turns: int = Field(default=50, alias="WREN_MAX_TURNS")
    system_prompt: str = Field(default="", alias="WREN_SYSTEM_PROMPT")


class Settings(WrenModel):
    """Main settings class.

    Loads configuration from environment variables with fallback defaults.
    """

    llm: LLMSettings = Field(default_factory=LLMSettings)
    workspace: WorkspaceSettings = Field(default_factory=WorkspaceSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)

    @classmethod
    def from_env(cls) -> Settings:
        """Load settings from environment variables."""
        return cls(
            llm=LLMSettings(
                model=os.getenv("WREN_MODEL", "gpt-4o"),
                api_key=os.getenv("WREN_API_KEY"),
                base_url=os.getenv("WREN_BASE_URL"),
                temperature=float(os.getenv("WREN_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("WREN_MAX_TOKENS", "4096")),
                timeout=float(os.getenv("WREN_TIMEOUT", "120")),
            ),
            workspace=WorkspaceSettings(
                root=os.getenv("WREN_WORKSPACE_ROOT", "."),
                max_file_size=int(os.getenv("WREN_MAX_FILE_SIZE", str(10 * 1024 * 1024))),
            ),
            agent=AgentSettings(
                name=os.getenv("WREN_AGENT_NAME", "wren"),
                max_turns=int(os.getenv("WREN_MAX_TURNS", "50")),
                system_prompt=os.getenv("WREN_SYSTEM_PROMPT", ""),
            ),
        )

    @classmethod
    def from_file(cls, path: str | Path) -> Settings:
        """Load settings from a JSON file."""
        import json

        file_path = Path(path)
        if not file_path.exists():
            return cls()

        with open(file_path) as f:
            data = json.load(f)

        return cls.model_validate(data)

    def to_file(self, path: str | Path) -> None:
        """Save settings to a JSON file."""
        import json

        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
