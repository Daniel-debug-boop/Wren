"""Secret management module for Wren."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SecretValue(BaseModel):
    """A secret value."""

    value: str


class SecretSource:
    """Base class for secret sources."""

    def get_value(self) -> Any:
        """Resolve the raw secret value, or ``None`` if it cannot be resolved."""
        raise NotImplementedError


class StaticSecret(SecretSource):
    """Static secret with a fixed value.

    The value may be a plain ``str``, a pydantic ``SecretStr``, or ``None``
    (for secrets that exist by name but carry no value yet).
    """

    def __init__(self, value: Any = None, description: str | None = None):
        self.value = value
        self.description = description

    def get_value(self) -> Any:
        if hasattr(self.value, 'get_secret_value'):
            return self.value.get_secret_value()  # type: ignore[union-attr]
        return self.value


class LookupSecret(SecretSource):
    """Secret that is looked up at runtime (e.g. from a sandbox webhook).

    ``key`` is the legacy name-based form; the app server uses ``url`` +
    ``headers`` so the sandbox can fetch the secret value on demand.
    """

    def __init__(
        self,
        key: str | None = None,
        url: str | None = None,
        headers: dict[str, Any] | None = None,
        description: str | None = None,
    ):
        self.key = key
        self.url = url
        self.headers = headers or {}
        self.description = description

    def get_value(self) -> Any:
        # LookupSecrets resolve through the sandbox webhook endpoint, not
        # locally; report that no value is available here.
        return None


__all__ = [
    "SecretSource",
    "StaticSecret",
    "LookupSecret",
    "SecretValue",
]
