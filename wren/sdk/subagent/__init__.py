"""Compatibility bridge for ``wren.sdk.subagent``.

Re-exports the subagent registry helpers from their actual location in
:mod:`wren.subagent`.
"""

from __future__ import annotations

from wren.subagent import get_registered_agent_definitions

__all__ = ['get_registered_agent_definitions']
