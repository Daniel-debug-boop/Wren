"""Plugin system for Wren."""

from __future__ import annotations

from enum import Enum


class PluginSource(str, Enum):
    """Source of a plugin."""
    LOCAL = "local"
    GITHUB = "github"
    MARKETPLACE = "marketplace"


__all__ = ["PluginSource"]
