"""Hooks exports."""

from __future__ import annotations

from typing import Any

from wren.hooks.hook import Hook, HookManager, HookPoint, HookResult


class _HookDef:
    """A single hook definition within a matcher."""

    def __init__(self, data: dict[str, Any]):
        self.type = data.get('type')
        self.command = data.get('command')
        self.timeout = data.get('timeout')
        self.async_ = data.get('async', data.get('async_', False))
        self.name = data.get('name')


class _HookMatcher:
    """A matcher (glob) with its hook definitions."""

    def __init__(self, data: dict[str, Any]):
        self.matcher = data.get('matcher', '*')
        raw_hooks = data.get('hooks', [])
        self.hooks = [
            hook if isinstance(hook, _HookDef) else _HookDef(hook)
            for hook in raw_hooks
        ]


class HookConfig:
    """Hook configuration.

    Exposes each hook point (``stop``, ``pre_tool_use``, ...) as an attribute
    containing a list of :class:`_HookMatcher` objects, so callers can do
    ``hook_config.stop`` and iterate ``matcher.hooks``.
    """

    def __init__(self, hook_points: dict[str, list[_HookMatcher]] | None = None):
        self._hook_points = hook_points or {}

    def __getattr__(self, name: str) -> list[_HookMatcher]:
        if name.startswith('_'):
            raise AttributeError(name)
        return self._hook_points.get(name, [])

    def get(self, name: str) -> list[_HookMatcher]:
        """Return the matchers configured for a hook point."""
        return self._hook_points.get(name, [])

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HookConfig:
        """Build a HookConfig from a raw hooks payload.

        Accepts both ``{"hooks": [...]}`` and the ``{hook_point: [config, ...]}``
        shapes returned by the agent server.
        """
        if not isinstance(data, dict) or not data:
            return cls()
        hook_points: dict[str, list[_HookMatcher]] = {}
        for point, matchers in data.items():
            if point == 'hooks' and isinstance(matchers, list) and matchers:
                # {hooks: [...]} shape — merge the wrapped entries.
                for entry in matchers:
                    if isinstance(entry, dict):
                        for inner_point, inner_matchers in entry.items():
                            if isinstance(inner_matchers, list):
                                hook_points.setdefault(inner_point, []).extend(
                                    _HookMatcher(m)
                                    for m in inner_matchers
                                    if isinstance(m, dict)
                                )
                continue
            if isinstance(matchers, list):
                hook_points[point] = [
                    _HookMatcher(m) for m in matchers if isinstance(m, dict)
                ]
        return cls(hook_points)

    def is_empty(self) -> bool:
        """Return True when there are no configured hooks."""
        return not any(self._hook_points.values())


__all__ = [
    "Hook",
    "HookManager",
    "HookPoint",
    "HookResult",
    "HookConfig",
]
