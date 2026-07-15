"""Tools compatibility shim.

Temporary re-exports from openhands.tools for migration.
Will be replaced with full wren-tools implementation.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "wren.tools is a compatibility shim. Migrate to wren-sdk native tools where possible.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from openhands for backward compatibility
try:
    from openhands.tools.preset.default import (
        get_default_tools,
        register_builtins_agents,
    )
    from openhands.tools.preset.planning import (
        format_plan_structure,
        get_planning_tools,
    )
except ImportError:
    pass
