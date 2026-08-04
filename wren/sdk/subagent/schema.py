"""Compatibility bridge for ``wren.sdk.subagent.schema``.

Re-exports the subagent schema models from their actual location in
:mod:`wren.subagent.schema`.
"""

from __future__ import annotations

from wren.subagent.schema import AgentDefinition

__all__ = ['AgentDefinition']
