"""Shared utilities for the OmniRoute module."""

from __future__ import annotations

import hashlib


def hash_api_key(api_key: str) -> str:
    """Create a deterministic hash for an API key.

    Used for identification without exposing the actual key value.
    Always use this instead of hashing inline to maintain consistency.
    """
    return hashlib.sha256(api_key.encode()).hexdigest()
