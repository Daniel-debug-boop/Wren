"""Secret registry and management."""
from __future__ import annotations

from typing import Any

from wren.secret import SecretSource, SecretValue, StaticSecret

__all__ = ["SecretSource", "SecretValue", "StaticSecret"]
