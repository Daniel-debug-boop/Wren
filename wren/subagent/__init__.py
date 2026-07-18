"""Subagent registry for Wren."""

from __future__ import annotations

from typing import Any


def get_registered_agent_definitions() -> dict[str, dict[str, Any]]:
    """Get all registered agent definitions."""
    return {}


__all__ = ["get_registered_agent_definitions"]
