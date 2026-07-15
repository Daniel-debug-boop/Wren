"""Capability manifest for Wren SDK.

Generates a complete inventory of agent capabilities for the system prompt.
This solves the "agent doesn't know what tools it has" problem.
"""

from __future__ import annotations

from typing import Any

from wren.tool.base import ToolDef, ToolCategory, ToolSafety
from wren.tool.registry import ToolRegistry


class CapabilityManifest:
    """Builds a complete inventory of agent capabilities.

    This generates the system prompt section that tells the agent
    what it can do, what tools are available, and when to use each.
    """

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def to_prompt(self) -> str:
        """Generate the capability section of the system prompt.

        This tells the agent:
        1. What tools exist
        2. What each tool is best for
        3. When to use one tool over another
        4. What NOT to use bash for
        """
        tools = self.registry.list_all()
        if not tools:
            return "No tools registered."

        sections = []

        # Group by category
        by_category: dict[ToolCategory, list[ToolDef]] = {}
        for tool in tools:
            by_category.setdefault(tool.category, []).append(tool)

        for category, cat_tools in by_category.items():
            sections.append(self._format_category(category, cat_tools))

        # Add selection rules
        sections.append(self._format_selection_rules())

        # Add safety guidelines
        sections.append(self._format_safety_guidelines())

        return "\n\n".join(sections)

    def to_openai_tools(self) -> list[dict[str, Any]]:
        """Get all tools in OpenAI function calling format."""
        return self.registry.get_openai_tools()

    def _format_category(self, category: ToolCategory, tools: list[ToolDef]) -> str:
        """Format a category of tools."""
        emoji = {
            ToolCategory.FILE: "📂",
            ToolCategory.TERMINAL: "💻",
            ToolCategory.WEB: "🌐",
            ToolCategory.GITHUB: "🔌",
            ToolCategory.DATABASE: "🗄️",
            ToolCategory.MCP: "🔌",
            ToolCategory.SKILL: "🧠",
            ToolCategory.SUBAGENT: "🤖",
            ToolCategory.CUSTOM: "🔧",
        }.get(category, "🔧")

        lines = [f"{emoji} {category.value.upper()} TOOLS"]

        for tool in sorted(tools, key=lambda t: t.name):
            safety_icon = {
                ToolSafety.SAFE: "✅",
                ToolSafety.MODERATE: "⚠️",
                ToolSafety.DANGEROUS: "🚫",
            }.get(tool.safety, "⚠️")

            lines.append(f"  - {tool.name}: {tool.description} {safety_icon}")

            if tool.best_for:
                lines.append(f"    Best for: {', '.join(tool.best_for)}")

            if tool.worse_for:
                lines.append(f"    Avoid for: {', '.join(tool.worse_for)}")

            if tool.prefer_over:
                lines.append(f"    Prefer over: {', '.join(tool.prefer_over)}")

        return "\n".join(lines)

    def _format_selection_rules(self) -> str:
        """Format tool selection rules."""
        return """TOOL SELECTION RULES
  ALWAYS use the most specific tool available:
  - GitHub tasks → Use GitHub API tools (github_*)
  - File operations → Use file tools (read, write, edit, glob, grep)
  - Web requests → Use web tools (fetch, scrape, browser)
  - Shell commands → Use bash ONLY when no specific tool exists

  NEVER use bash for things that have dedicated tools:
  - Don't use `cat` → Use read_file tool
  - Don't use `echo > file` → Use write_file tool
  - Don't use `find` → Use glob tool
  - Don't use `grep` → Use grep tool
  - Don't use `curl` → Use fetch/scrape tools
  - Don't use `git` commands → Use GitHub API tools

  Use bash ONLY for:
  - Running tests
  - Installing packages
  - System commands with no dedicated tool
  - Complex multi-step operations"""

    def _format_safety_guidelines(self) -> str:
        """Format safety guidelines."""
        return """SAFETY GUIDELINES
  - Read-only operations are SAFE (✅)
  - Write operations need confirmation for important files (⚠️)
  - Destructive operations (rm, force push) need explicit confirmation (🚫)
  - Never log or expose secrets (API keys, passwords)
  - Never access /etc, .env, or system files without explicit permission"""
