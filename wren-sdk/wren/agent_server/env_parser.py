"""env_parser compatibility shim."""

from __future__ import annotations

try:
    from openhands.agent_server.env_parser import (
        ABC,
        DiscriminatedUnionMixin,
        from_env,
    )
except ImportError:
    pass
