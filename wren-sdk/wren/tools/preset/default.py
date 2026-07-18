"""Default tools preset compatibility shim."""

from __future__ import annotations

try:
    from openhands.tools.preset.default import (
        get_default_tools,
        register_builtins_agents,
    )
except ImportError:
    pass
