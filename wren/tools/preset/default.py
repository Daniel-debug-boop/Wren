"""Default tools preset for Wren."""

from __future__ import annotations

from typing import Any


def get_default_tools(
    enable_browser: bool = False,
    enable_sub_agents: bool = False,
    **_: Any,
) -> list[Any]:
    """Get the default set of tools.

    ``enable_browser`` and ``enable_sub_agents`` are accepted for API
    compatibility with the OpenHands-based tools preset; this standalone
    implementation ships an empty default tool set.
    """
    return []


def register_builtins_agents(
    enable_browser: bool = False,
    **_: Any,
) -> None:
    """Register built-in agent tools.

    ``enable_browser`` is accepted for API compatibility with the
    OpenHands-based tools preset; no-op in this standalone implementation.
    """
    pass


__all__ = ["get_default_tools", "register_builtins_agents"]
