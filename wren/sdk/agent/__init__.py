"""Compatibility bridge for ``wren.sdk.agent``.

Re-exports the agent abstractions from their actual location in
:mod:`wren.agent`.
"""

from __future__ import annotations

from wren.agent import ACPAgent, Agent, AgentBase, AgentConfig, AgentUnion

__all__ = ['ACPAgent', 'Agent', 'AgentBase', 'AgentConfig', 'AgentUnion']
