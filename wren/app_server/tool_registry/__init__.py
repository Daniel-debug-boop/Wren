"""Dynamic Tool Registry for OpenHands.

Provides automatic capability discovery, missing-tool detection,
web scraping for open-source tools, and dynamic skill creation.
"""

from wren.app_server.tool_registry.inventory import ToolInventory
from wren.app_server.tool_registry.scraper import ToolScraper
from wren.app_server.tool_registry.installer import ToolInstaller
from wren.app_server.tool_registry.orchestrator import ToolOrchestrator

__all__ = [
    'ToolInventory',
    'ToolScraper',
    'ToolInstaller',
    'ToolOrchestrator',
]
