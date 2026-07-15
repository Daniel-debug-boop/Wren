"""utils compatibility shim."""

from __future__ import annotations

try:
    from openhands.agent_server.utils import (
        OpenHandsUUID,
        utc_now,
    )
except ImportError:
    pass
