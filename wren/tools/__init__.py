"""Tools compatibility shim."""

from __future__ import annotations

import warnings

warnings.warn(
    "wren.tools is a compatibility shim. Migrate to wren-sdk native tools where possible.",
    DeprecationWarning,
    stacklevel=2,
)

try:
    from wren.tools.preset.default import (
        get_default_tools,
        register_builtins_agents,
    )
    from wren.tools.preset.planning import (
        format_plan_structure,
        get_planning_tools,
    )
except ImportError:
    pass
