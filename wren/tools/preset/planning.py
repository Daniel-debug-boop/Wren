"""Planning tools preset for Wren."""

from __future__ import annotations

from typing import Any


def get_planning_tools() -> list[Any]:
    """Get planning-specific tools."""
    return []


def format_plan_structure(plan: dict[str, Any]) -> str:
    """Format a plan dict into a human-readable string."""
    return str(plan)


__all__ = ["get_planning_tools", "format_plan_structure"]
