"""Summarizing condenser for conversation history compression.

The vendored SDK (v1.0.0) predates this class, but the app server and its
tests consume it. Pydantic model matching the API surface used: ``llm``,
``max_size``, ``keep_first`` and ``model_copy``.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class LLMSummarizingCondenser(BaseModel):
    """Condenses conversation history using an LLM."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    llm: Any = None
    max_size: int = 240
    keep_first: int = 2


__all__ = ['LLMSummarizingCondenser']
