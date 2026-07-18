"""Environment variable parser for agent server configuration.

Provides ABC, DiscriminatedUnionMixin, and from_env utilities
using native Wren SDK types instead of the old openhands SDK.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel


class DiscriminatedUnionMixin(BaseModel):
    """Mixin for discriminated unions with automatic type resolution."""

    @classmethod
    def get_discriminator_value(cls, data: dict[str, Any]) -> str | None:
        """Extract the discriminator value from raw data."""
        return data.get('type') or data.get('kind')


T = TypeVar('T', bound=BaseModel)


def from_env(
    model_cls: type[T],
    prefix: str = '',
    strict: bool = False,
) -> T:
    """Load a Pydantic model from environment variables.

    Reads environment variables matching ``{prefix}_{field_name.upper()}``
    for each field in the model and returns a populated instance.

    Args:
        model_cls: The Pydantic model class to instantiate.
        prefix: Environment variable prefix (e.g. 'OH' for OH_* vars).
        strict: If True, raises on missing required fields.

    Returns:
        An instance of ``model_cls`` populated from the environment.
    """
    import os

    field_values: dict[str, Any] = {}
    for field_name, field_info in model_cls.model_fields.items():
        env_key = f'{prefix}_{field_name.upper()}' if prefix else field_name.upper()
        raw = os.environ.get(env_key)
        if raw is not None:
            field_values[field_name] = raw
        elif strict and field_info.is_required():
            raise ValueError(
                f'Missing required environment variable: {env_key}'
            )

    return model_cls(**field_values)


__all__ = [
    'ABC',
    'DiscriminatedUnionMixin',
    'from_env',
]
