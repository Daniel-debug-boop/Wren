"""Tool exports."""

from __future__ import annotations

import os as _os

# The vendored SDK package owns ``wren.tool`` (this file), but the app server
# keeps additional local subpackages under ``wren/tool/`` (e.g. ``builtins``).
# Attach that directory so ``from wren.tool.builtins import ...`` resolves.
_local_tool_dir = _os.path.join(
    _os.path.dirname(
        _os.path.dirname(
            _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        )
    ),
    'wren',
    'tool',
)
if _os.path.isdir(_local_tool_dir) and _local_tool_dir not in __path__:
    __path__.append(_local_tool_dir)

from wren.tool.base import (
    Tool,
    ToolDef,
    ToolCategory,
    ToolSafety,
    Action,
    Observation,
)
from wren.tool.registry import ToolRegistry
from wren.tool.manifest import CapabilityManifest
from wren.tool.guardrail import (
    Guardrail,
    GuardrailResult,
    GuardrailEnforcer,
    CommandBlocklist,
    PathBlocklist,
    GitGuardrail,
    NetworkGuardrail,
)

__all__ = [
    "Tool",
    "ToolDef",
    "ToolCategory",
    "ToolSafety",
    "Action",
    "Observation",
    "ToolRegistry",
    "CapabilityManifest",
    "Guardrail",
    "GuardrailResult",
    "GuardrailEnforcer",
    "CommandBlocklist",
    "PathBlocklist",
    "GitGuardrail",
    "NetworkGuardrail",
]
