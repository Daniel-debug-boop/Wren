"""Compatibility bridge for the newer ``wren.sdk`` namespace.

The vendored SDK copy (v1.0.0) predates the ``wren.sdk`` layout that the
app server and its tests import from. This package re-exports the symbols
from their actual locations so ``from wren.sdk import ...`` keeps working
while the vendored copy is upgraded.

Sibling bridge modules (``wren.sdk.llm``, ``wren.sdk.settings``,
``wren.sdk.workspace``, ...) provide the same forwarding for their
respective sub-namespaces.
"""

from wren.agent import Agent, AgentConfig
from wren.context import AgentContext
from wren.conversation import ConversationStats
from wren.event import Event, EventType, MessageEvent
from wren.llm import Message, MessageRole, TextContent

# Import the sibling bridge subpackages so ``import wren.sdk.llm`` and friends
# resolve even without an explicit ``from wren.sdk.llm import ...``.
from wren.sdk import (  # noqa: F401  (re-exported subpackages)
    agent,
    conversation,
    event,
    llm,
    secret,
    security,
    settings,
    subagent,
    utils,
    workspace,
)

__all__ = [
    'Agent',
    'AgentConfig',
    'AgentContext',
    'ConversationStats',
    'Event',
    'EventType',
    'Message',
    'MessageEvent',
    'MessageRole',
    'TextContent',
]
