"""Default tools preset for Wren."""

from __future__ import annotations

from typing import Any


def get_default_tools() -> list[Any]:
    """Get the default set of tools."""
    return []


def register_builtins_agents() -> None:
    """Register built-in agent tools."""
    pass


__all__ = ["get_default_tools", "register_builtins_agents"]
