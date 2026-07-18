"""Prompt builder for Wren SDK.

Constructs system prompts from agent configuration and capabilities.
"""

from __future__ import annotations

from typing import Any

from wren.tool.registry import ToolRegistry
from wren.tool.manifest import CapabilityManifest


class PromptBuilder:
    """Builds system prompts for agents.

    Assembles prompts from:
    - Base personality/instructions
    - Capability manifest (tools, skills, etc.)
    - Custom sections
    """

    def __init__(
        self,
        base_prompt: str = "",
        tool_registry: ToolRegistry | None = None,
    ):
        self.base_prompt = base_prompt
        self.tool_registry = tool_registry or ToolRegistry()
        self._custom_sections: list[str] = []

    def add_section(self, section: str) -> PromptBuilder:
        """Add a custom section to the prompt."""
        self._custom_sections.append(section)
        return self

    def build(self) -> str:
        """Build the complete system prompt."""
        parts = []

        # Base prompt
        if self.base_prompt:
            parts.append(self.base_prompt)

        # Capability manifest
        manifest = CapabilityManifest(self.tool_registry)
        parts.append(manifest.to_prompt())

        # Custom sections
        parts.extend(self._custom_sections)

        return "\n\n".join(parts)

    @classmethod
    def default(cls, tool_registry: ToolRegistry | None = None) -> PromptBuilder:
        """Create a prompt builder with default Wren personality."""
        base_prompt = """You are Wren, an AI software engineer.

You are helpful, precise, and efficient. You:
- Write clean, well-documented code
- Follow best practices and conventions
- Test your changes when possible
- Explain your reasoning when helpful
- Ask for clarification when needed

You have access to tools that let you read/write files, run commands,
search code, interact with GitHub, and more. Always use the most
appropriate tool for the task."""

        return cls(base_prompt=base_prompt, tool_registry=tool_registry)
