"""ACP agent model.

Re-exports :class:`ACPAgent` from the agent module so that
``from wren.agent.acp_agent import ACPAgent`` (and the ``wren.sdk.agent.acp_agent``
bridge) resolves to the same class used by the discriminated union.
"""

from __future__ import annotations

from wren.agent.agent import ACPAgent

__all__ = ['ACPAgent']
