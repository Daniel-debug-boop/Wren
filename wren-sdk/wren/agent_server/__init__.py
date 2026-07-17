"""Agent server compatibility shim.

Temporary re-exports from wren.agent_server for migration.
Will be replaced with full wren-server implementation.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "wren.agent_server is a compatibility shim. Migrate to wren-sdk native modules where possible.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from openhands for backward compatibility
try:
    from wren.agent_server.env_parser import ABC, DiscriminatedUnionMixin, from_env  # noqa: F401
    from wren.agent_server.models import (  # noqa: F401
        ConversationInfo,
        EventPage,
        EventSortOrder,
        ImageContent,
        Success,
        TextContent,
    )
    from wren.agent_server.utils import OpenHandsUUID, utc_now  # noqa: F401
except ImportError:
    pass
