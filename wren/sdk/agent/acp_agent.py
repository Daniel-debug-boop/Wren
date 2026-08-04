"""Compatibility bridge for ``wren.sdk.agent.acp_agent``.

Re-exports :class:`ACPAgent` from its actual location in
:mod:`wren.agent.acp_agent`.
"""

from __future__ import annotations

from wren.agent.acp_agent import ACPAgent

__all__ = ['ACPAgent']
