"""Hooks exports."""

from typing import Any

from wren.hooks.hook import Hook, HookManager, HookPoint, HookResult


class HookConfig:
    """Hook configuration."""

    def __init__(self, hooks: list[dict[str, Any]] | None = None):
        self.hooks = hooks or []


__all__ = [
    "Hook",
    "HookManager",
    "HookPoint",
    "HookResult",
    "HookConfig",
]
