"""Compatibility bridge for ``wren.sdk.agent.agent``.

Re-exports the agent classes from their actual location in
:mod:`wren.agent.agent`.
"""

from __future__ import annotations

from wren.agent.agent import (
    ACPAgent,
    Agent,
    AgentBase,
    AgentConfig,
    AgentUnion,
)

__all__ = ['ACPAgent', 'Agent', 'AgentBase', 'AgentConfig', 'AgentUnion']
