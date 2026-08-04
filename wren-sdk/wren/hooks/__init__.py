"""Hooks exports."""

from __future__ import annotations

from typing import Any

from wren.hooks.hook import Hook, HookManager, HookPoint, HookResult


class HookConfig:
    """Hook configuration."""

    def __init__(self, hooks: list[dict[str, Any]] | None = None):
        self.hooks = hooks or []

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HookConfig:
        """Build a HookConfig from a raw hooks payload.

        Accepts both ``{"hooks": [...]}`` and the ``{hook_point: [...]}``
        shapes returned by the agent server.
        """
        if not isinstance(data, dict) or not data:
            return cls(hooks=[])
        raw_hooks = data.get('hooks', [])
        if not isinstance(raw_hooks, list):
            raw_hooks = []
        if raw_hooks:
            return cls(hooks=raw_hooks)
        # {hook_point: [config, ...]} shape — preserve as a single entry so
        # the config is not treated as empty.
        return cls(hooks=[data])

    def is_empty(self) -> bool:
        """Return True when there are no configured hooks."""
        return not self.hooks


__all__ = [
    "Hook",
    "HookManager",
    "HookPoint",
    "HookResult",
    "HookConfig",
]
