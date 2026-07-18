"""LangGraph prebuilt agents bridge."""
from __future__ import annotations

try:
    from langgraph.prebuilt import create_react_agent, ToolNode
    __all__ = ["create_react_agent", "ToolNode"]
except ImportError:
    __all__ = []
