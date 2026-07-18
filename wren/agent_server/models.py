"""Agent server models — native Wren types replacing openhands SDK re-exports.

Provides the models that the app server's webhook router and other
components consume. Uses Pydantic v2 throughout.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ImageContent(BaseModel):
    """Image content within a message."""

    image_url: str
    detail: str | None = None


class TextContent(BaseModel):
    """Text content within a message."""

    text: str


class EventSortOrder(str, Enum):
    """Sort order for event listing."""

    ASC = 'asc'
    DESC = 'desc'


class EventPage(BaseModel):
    """A page of events returned by the agent server."""

    events: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 50


class ConversationInfo(BaseModel):
    """Information about a conversation from the agent server."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: UUID
    title: str | None = None
    execution_status: Any = None  # ConversationExecutionStatus
    agent: Any = None  # Agent or ACPAgent discriminated union
    tags: dict[str, str] | None = None
    current_model_id: str | None = None
    created_at: float | None = None
    updated_at: float | None = None


class Success(BaseModel):
    """Success response."""

    success: bool = True
    message: str = 'Success'


__all__ = [
    'ConversationInfo',
    'EventPage',
    'EventSortOrder',
    'ImageContent',
    'Success',
    'TextContent',
]
