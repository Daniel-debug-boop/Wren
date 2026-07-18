"""Secret management module for Wren."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SecretValue(BaseModel):
    """A secret value."""
    value: str


class SecretSource:
    """Base class for secret sources."""
    pass


class StaticSecret(SecretSource):
    """Static secret with a fixed value."""

    def __init__(self, value: str):
        self.value = value


class LookupSecret(SecretSource):
    """Secret that is looked up at runtime."""

    def __init__(self, key: str):
        self.key = key


__all__ = [
    "SecretSource",
    "StaticSecret",
    "LookupSecret",
    "SecretValue",
]
