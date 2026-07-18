"""OmniRoute — Intelligent AI Gateway for Wren.

Auto-routes LLM requests across 250+ providers with smart fallback,
token compression, cost tracking, and zero-config auto-discovery.

The user just drops an API key — OmniRoute handles the rest:
  - Auto-discovers which providers the key unlocks
  - Auto-creates optimal routing combos
  - Auto-falls back when providers fail
  - Auto-compresses tokens to save costs
  - Tracks everything transparently
"""

from wren.omniroute.router import OmniRouter
from wren.omniroute.combo_engine import ComboEngine, RoutingStrategy
from wren.omniroute.provider_catalog import ProviderCatalog, ProviderInfo
from wren.omniroute.resilience import ResilienceManager
from wren.omniroute.compression import CompressionEngine
from wren.omniroute.cost_tracker import CostTracker
from wren.omniroute.quota_share import QuotaShareManager
from wren.omniroute.auto_discovery import AutoDiscovery

__version__ = "1.0.0"
__all__ = [
    "OmniRouter",
    "ComboEngine",
    "RoutingStrategy",
    "ProviderCatalog",
    "ProviderInfo",
    "ResilienceManager",
    "CompressionEngine",
    "CostTracker",
    "QuotaShareManager",
    "AutoDiscovery",
]
