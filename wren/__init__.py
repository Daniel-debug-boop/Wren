# This is a namespace package - extend the path to include installed packages
# (We need to do this to support dependencies wren-sdk, wren-tools and wren-agent-server
# which all have a top level `wren`` package.)
import os as _os

_sdk_wren_dir = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'wren-sdk', 'wren'
)
if _os.path.isdir(_sdk_wren_dir) and _sdk_wren_dir not in __path__:
    __path__.append(_sdk_wren_dir)
__path__ = __import__('pkgutil').extend_path(__path__, __name__)

# Import version information for backward compatibility
from wren.app_server.version import __version__, get_version

# Re-export commonly used SDK types for backward compat (from wren import X)
from openhands.sdk.event import Event, MessageEvent  # noqa: F401
from openhands.sdk.agent import Agent  # noqa: F401
from openhands.sdk.context import AgentContext  # noqa: F401
from openhands.sdk.context.condenser.llm_summarizing_condenser import (
    LLMSummarizingCondenser,
)  # noqa: F401
from openhands.sdk.conversation.conversation_stats import ConversationStats  # noqa: F401
from openhands.sdk.conversation.state import ConversationExecutionStatus  # noqa: F401
from openhands.sdk.workspace.local import LocalWorkspace  # noqa: F401
from openhands import tools  # type: ignore[attr-defined]  # noqa: F401

__all__ = [
    '__version__',
    'get_version',
    'Event',
    'MessageEvent',
    'Agent',
    'AgentContext',
    'LocalWorkspace',
    'LLMSummarizingCondenser',
    'ConversationStats',
    'ConversationExecutionStatus',
    'tools',
]
