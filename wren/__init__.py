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
from wren.langgraph.client import get_client  # noqa: F401
from wren.langgraph.graph import StateGraph, START, END  # noqa: F401
from wren.langgraph.prebuilt import create_react_agent  # noqa: F401
from wren.event import Event, MessageEvent  # noqa: F401
from wren.workspace.local import LocalWorkspace  # noqa: F401
from wren.hooks import HookConfig  # noqa: F401

__all__ = [
    '__version__',
    'get_version',
    'get_client',
    'StateGraph',
    'START',
    'END',
    'create_react_agent',
    'Event',
    'MessageEvent',
    'LocalWorkspace',
    'HookConfig',
]
