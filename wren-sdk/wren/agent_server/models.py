"""models compatibility shim."""

from __future__ import annotations

try:
    from wren.agent_server.models import (
        ConversationInfo,
        EventPage,
        EventSortOrder,
        ImageContent,
        Success,
        TextContent,
    )
except ImportError:
    pass
