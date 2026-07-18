"""LLM profile store utilities."""

from __future__ import annotations

import re

PROFILE_NAME_REGEX = re.compile(r'^[a-zA-Z0-9_-]+$')

__all__ = ["PROFILE_NAME_REGEX"]
