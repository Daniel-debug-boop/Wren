"""Subagent schema models for Wren."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentDefinition(BaseModel):
    """Definition of a built-in or registered subagent."""

    name: str
    description: str = ''
    tools: list[str] = Field(default_factory=list)
    prompt: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = ['AgentDefinition']
