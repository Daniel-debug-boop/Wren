"""Conversation exports."""

from enum import Enum

from wren.conversation.conversation import (
    Conversation,
    ConversationState,
    ConversationStats,
)


class ConversationExecutionStatus(str, Enum):
    """Conversation execution status."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


__all__ = [
    "Conversation",
    "ConversationState",
    "ConversationStats",
    "ConversationExecutionStatus",
]
