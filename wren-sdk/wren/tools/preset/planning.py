"""Planning tools preset compatibility shim."""

from __future__ import annotations

try:
    from openhands.tools.preset.planning import (
        format_plan_structure,
        get_planning_tools,
    )
except ImportError:
    pass
