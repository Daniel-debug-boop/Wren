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
    cache_prompt: bool = False


class EventSortOrder(str, Enum):
    """Sort order for event listing."""

    ASC = 'asc'
    DESC = 'desc'
    TIMESTAMP = 'timestamp'
    TIMESTAMP_DESC = 'timestamp_desc'


class EventPage(BaseModel):
    """A page of events returned by the agent server."""

    items: list[Any] = Field(default_factory=list)
    next_page_id: str | None = None
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


class OpenHandsModel(BaseModel):
    """Base model class for all OpenHands models."""


class SendMessageRequest(BaseModel):
    """Request to send a message to a conversation."""

    role: str = 'user'
    content: list[TextContent | ImageContent] = Field(default_factory=list)
    run: bool = True


class StartConversationRequest(BaseModel):
    """Request to start an agent conversation.

    Carries the fully-built ``Agent`` (or ACP agent) plus the
    conversation-level configuration resolved by the app server
    (workspace, plugins, secrets, observability metadata, ...).

    Field types for cross-package objects (``Agent``, workspace, plugins,
    secrets) are intentionally ``Any`` to avoid import cycles between
    ``wren.agent_server.models`` and the app-conversation layer.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent: Any
    user_id: str | None = None
    secrets: dict[str, Any] = Field(default_factory=dict)
    observability_metadata: dict[str, Any] = Field(default_factory=dict)
    workspace: Any = None
    conversation_id: Any = None
    initial_message: SendMessageRequest | None = None
    plugins: list[Any] | None = None
    trigger: Any = None
    git_provider: Any = None
    working_dir: str | None = None
    selected_repository: str | None = None
    selected_branch: str | None = None
    remote_workspace: Any = None
    mode: str = 'code'
    max_iterations: int = 50
    confirmation_mode: bool = False
    security_analyzer: str | None = 'none'
    agent_definitions: list[Any] = Field(default_factory=list)


class Success(BaseModel):
    """Success response."""

    success: bool = True
    message: str = 'Success'


__all__ = [
    'ConversationInfo',
    'EventPage',
    'EventSortOrder',
    'ImageContent',
    'OpenHandsModel',
    'SendMessageRequest',
    'StartConversationRequest',
    'Success',
    'TextContent',
]
