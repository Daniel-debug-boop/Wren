"""Tool framework for Wren SDK.

Provides the Tool ABC, Action/Observation types, and tool registry
with selection intelligence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from wren.utils.models import WrenModel


class ToolCategory(str, Enum):
    """Tool categories for grouping and selection."""

    FILE = "file"
    TERMINAL = "terminal"
    WEB = "web"
    GITHUB = "github"
    DATABASE = "database"
    MCP = "mcp"
    SKILL = "skill"
    SUBAGENT = "subagent"
    CUSTOM = "custom"


class ToolSafety(str, Enum):
    """Tool safety level."""

    SAFE = "safe"  # Read-only, no side effects
    MODERATE = "moderate"  # Has side effects, reversible
    DANGEROUS = "dangerous"  # Destructive, requires confirmation


class Action(WrenModel):
    """An action to be executed by a tool."""

    tool_name: str
    arguments: dict[str, Any]
    action_id: str | None = None


class Observation(WrenModel):
    """The result of executing an action."""

    action_id: str | None = None
    success: bool
    result: str
    error: str | None = None
    metadata: dict[str, Any] | None = None


class ToolDef(WrenModel):
    """Tool definition for LLM function calling."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    category: ToolCategory = ToolCategory.CUSTOM
    safety: ToolSafety = ToolSafety.MODERATE
    best_for: list[str] = []
    worse_for: list[str] = []
    prefer_over: list[str] = []  # Use this INSTEAD of these tools
    tags: list[str] = []

    def to_openai_tool(self) -> dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class Tool(ABC):
    """Base class for all tools.

    Subclass this to create new tools. The tool will be automatically
    registered and available for agent use.
    """

    @abstractmethod
    def get_definition(self) -> ToolDef:
        """Return the tool definition.

        This defines the tool's name, description, parameters,
        and metadata for selection intelligence.
        """
        ...

    @abstractmethod
    async def execute(self, action: Action) -> Observation:
        """Execute the tool action.

        Args:
            action: The action to execute with arguments.

        Returns:
            Observation with the result.
        """
        ...

    async def validate(self, action: Action) -> str | None:
        """Validate action arguments before execution.

        Returns:
            None if valid, error message if invalid.
        """
        return None
