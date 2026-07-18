"""Builtin tools for Wren."""

from __future__ import annotations

from typing import Any


class SwitchLLMTool:
    """Tool to switch LLM models mid-conversation."""

    name: str = "switch_llm"
    description: str = "Switch to a different LLM model."

    def run(self, model: str, **kwargs: Any) -> str:
        return f"Switched to model: {model}"


class SwitchLLMObservation:
    """Observation from switching LLM."""

    def __init__(self, model: str, success: bool = True, error: str | None = None):
        self.model = model
        self.success = success
        self.error = error


__all__ = ["SwitchLLMTool", "SwitchLLMObservation"]
