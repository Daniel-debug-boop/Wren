"""Wren top-level package.

This is a namespace package - extend the path to include installed packages
(we need to do this to support dependencies wren-sdk, wren-tools and
wren-agent-server which all have a top level ``wren`` package).

IMPORTANT: Heavy dependencies (FastAPI, pydantic, langgraph) are lazy-loaded
so that the wren module can be imported without them. This is critical for:
  - CLI tools (run_app_builder.py) that only need app_builder
  - Environments where heavy deps are not installed
"""
import os as _os

_sdk_wren_dir = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'wren-sdk', 'wren'
)
if _os.path.isdir(_sdk_wren_dir) and _sdk_wren_dir not in __path__:
    __path__.append(_sdk_wren_dir)
__path__ = __import__('pkgutil').extend_path(__path__, __name__)

# ── Lazy imports (heavy deps loaded on first access) ──────────────────────

# Version — try to load the real version, fall back gracefully
__version__ = "0.0.0"
get_version = lambda: __version__

try:
    from wren.app_server.version import __version__ as _ver, get_version as _gv  # type: ignore
    __version__ = _ver
    get_version = _gv
except ImportError:
    pass

# Use module-level __getattr__ for Python 3.7+ lazy attribute loading
# This is called when normal attribute lookup fails (i.e., for attributes
# NOT defined at module level). Heavy deps are imported here on demand.


def __getattr__(name):
    """Lazy-load heavy attributes."""
    if name == 'get_client':
        try:
            from wren.langgraph.client import get_client as _gc
            return _gc
        except ImportError:
            raise ImportError("langgraph not installed. Install with: pip install langgraph")
    if name in ('StateGraph', 'START', 'END'):
        try:
            from wren.langgraph import graph as _graph
            return getattr(_graph, name)
        except ImportError:
            raise ImportError("langgraph not installed. Install with: pip install langgraph")
    if name == 'create_react_agent':
        try:
            from wren.langgraph.prebuilt import create_react_agent as _cra
            return _cra
        except ImportError:
            raise ImportError("langgraph not installed. Install with: pip install langgraph")
    if name == 'Event':
        try:
            from wren.event import Event as _evt
            return _evt
        except ImportError:
            raise ImportError("wren.event module not available")
    if name == 'MessageEvent':
        try:
            from wren.event import MessageEvent as _mevt
            return _mevt
        except ImportError:
            raise ImportError("wren.event module not available")
    if name == 'LocalWorkspace':
        try:
            from wren.workspace.workspace import LocalWorkspace as _ws
            return _ws
        except ImportError:
            raise ImportError("wren.workspace module not available")
    if name == 'HookConfig':
        try:
            from wren.hooks import HookConfig as _hk
            return _hk
        except ImportError:
            raise ImportError("wren.hooks module not available")
    raise AttributeError(f"module 'wren' has no attribute '{name}'")


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
