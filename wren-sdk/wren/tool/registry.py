"""Tool registry with selection intelligence.

Provides auto-discovery, ranking, and selection of the best tool for a task.
"""

from __future__ import annotations

import re
import logging
from typing import Any

from wren.tool.base import Tool, ToolDef, ToolCategory, ToolSafety, Action, Observation

logger = logging.getLogger("wren.tool")


class ToolSelectionRule:
    """Rule for selecting the best tool for a task."""

    # Patterns that indicate which tool to use
    TASK_PATTERNS: dict[str, list[str]] = {
        # File operations
        r"read.*file": ["read_file", "NOT bash cat", "NOT bash head"],
        r"write.*file": ["write_file", "NOT bash echo", "NOT bash tee"],
        r"edit.*file": ["edit_file", "NOT bash sed"],
        r"find.*file": ["glob", "NOT bash find"],
        r"search.*content": ["grep", "NOT bash grep"],
        r"list.*directory": ["list_directory", "NOT bash ls"],
        # Git operations
        r"create.*issue": ["github_create_issue", "NOT bash curl"],
        r"create.*pr": ["github_create_pr", "NOT bash curl"],
        r"list.*pr": ["github_list_prs", "NOT bash curl"],
        r"merge.*pr": ["github_merge_pr", "NOT bash curl"],
        # Web operations
        r"fetch.*url": ["fetch", "NOT bash curl", "NOT bash wget"],
        r"scrape.*page": ["scrape", "NOT bash curl"],
        r"take.*screenshot": ["screenshot", "NOT bash cutycapt"],
        # Terminal (last resort)
        r"run.*command": ["bash"],
        r"install.*package": ["bash"],
        r"run.*test": ["bash"],
    }

    # Anti-patterns: never use these tools for these tasks
    ANTI_PATTERNS: dict[str, list[str]] = {
        "bash": [
            "read file",
            "write file",
            "find file",
            "search content",
            "create issue",
            "create pr",
            "fetch url",
        ],
    }


class ToolRegistry:
    """Registry of available tools with selection intelligence.

    Features:
    - Auto-discovery of registered tools
    - Tool selection based on task description
    - Safety checking
    - Tool priority ranking
    """

    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._definitions: dict[str, ToolDef] = {}
        self._selection_rules = ToolSelectionRule()

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        defn = tool.get_definition()
        self._tools[defn.name] = tool
        self._definitions[defn.name] = defn
        logger.debug(f"Registered tool: {defn.name} ({defn.category.value})")

    def register_def(self, defn: ToolDef) -> None:
        """Register a tool definition (metadata-only, no Tool instance)."""
        self._definitions[defn.name] = defn
        logger.debug(f"Registered tool def: {defn.name} ({defn.category.value})")

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        self._tools.pop(name, None)
        self._definitions.pop(name, None)

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_definition(self, name: str) -> ToolDef | None:
        """Get a tool definition by name."""
        return self._definitions.get(name)

    def list_all(self) -> list[ToolDef]:
        """List all registered tool definitions."""
        return list(self._definitions.values())

    def list_by_category(self, category: ToolCategory) -> list[ToolDef]:
        """List tools by category."""
        return [d for d in self._definitions.values() if d.category == category]

    def list_by_safety(self, safety: ToolSafety) -> list[ToolDef]:
        """List tools by safety level."""
        return [d for d in self._definitions.values() if d.safety == safety]

    def get_openai_tools(self) -> list[dict[str, Any]]:
        """Get all tools in OpenAI function calling format."""
        return [d.to_openai_tool() for d in self._definitions.values()]

    def select_best(self, task_description: str) -> list[str]:
        """Select the best tools for a given task.

        Returns:
            List of tool names ranked by suitability.
        """
        task_lower = task_description.lower()
        candidates: dict[str, int] = {}

        # Check task patterns
        for pattern, preferred in self._selection_rules.TASK_PATTERNS.items():
            if re.search(pattern, task_lower):
                for i, tool_name in enumerate(preferred):
                    if tool_name.startswith("NOT "):
                        # Anti-pattern: penalize this tool
                        anti_tool = tool_name[4:]
                        candidates[anti_tool] = candidates.get(anti_tool, 0) - 10
                    else:
                        # Preferred: boost this tool
                        candidates[tool_name] = candidates.get(tool_name, 0) + (10 - i)

        # Boost tools that are actually registered
        for name in candidates:
            if name in self._definitions:
                candidates[name] += 5

        # Sort by score descending
        ranked = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
        return [name for name, score in ranked if score > 0]

    async def execute(self, tool_name: str, action: Action) -> Observation:
        """Execute a tool action.

        Args:
            tool_name: Name of the tool to execute.
            action: The action to execute.

        Returns:
            Observation with the result.
        """
        tool = self._tools.get(tool_name)
        if tool is None:
            return Observation(
                success=False,
                result="",
                error=f"Tool not found: {tool_name}",
            )

        # Validate
        validation_error = await tool.validate(action)
        if validation_error:
            return Observation(
                success=False,
                result="",
                error=f"Validation error: {validation_error}",
            )

        # Execute
        try:
            return await tool.execute(action)
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return Observation(
                success=False,
                result="",
                error=str(e),
            )

    def _get_task_patterns(self) -> dict[str, list[str]]:
        """Get task patterns (for testing)."""
        return self._selection_rules.TASK_PATTERNS
