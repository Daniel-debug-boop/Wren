"""Agent server utilities — native Wren implementation.

Provides OpenHandsUUID, utc_now, and other utilities previously
re-exported from the openhands SDK.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class OpenHandsUUID:
    """UUID generator matching the OpenHands UUID format."""

    @staticmethod
    def generate() -> str:
        """Generate a new UUID4 string."""
        return str(uuid.uuid4())

    @staticmethod
    def from_hex(hex_str: str) -> uuid.UUID:
        """Create a UUID from a hex string."""
        return uuid.UUID(hex=hex_str)

    @staticmethod
    def is_valid(uuid_str: str) -> bool:
        """Check if a string is a valid UUID."""
        try:
            uuid.UUID(uuid_str)
            return True
        except (ValueError, AttributeError):
            return False


__all__ = [
    'OpenHandsUUID',
    'utc_now',
]
