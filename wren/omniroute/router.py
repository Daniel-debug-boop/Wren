"""OmniRouter — the main orchestrator for OmniRoute's intelligent routing.

This is the primary entry point for the OmniRoute system. It ties together:
  - Provider catalog (250+ providers)
  - Auto-Combo engine (18 routing strategies)
  - 3-layer resilience (circuit breakers, cooldowns, lockouts)
  - Token compression (RTK + Caveman)
  - Cost tracking
  - Quota sharing
  - Auto-discovery

Usage:
    router = OmniRouter()
    await router.initialize(api_keys={"openai": "sk-...", ...})
    result = await router.route("auto/coding", task_type="coding")
"""

from __future__ import annotations

import logging
from typing import Any

from wren.omniroute.provider_catalog import ProviderCatalog
from wren.omniroute.combo_engine import ComboEngine
from wren.omniroute.resilience import ResilienceManager
from wren.omniroute.compression import CompressionEngine
from wren.omniroute.cost_tracker import CostTracker
from wren.omniroute.quota_share import QuotaShareManager
from wren.omniroute.auto_discovery import AutoDiscovery
from wren.omniroute.types import (
    ComboDefinition,
    RoutingResult,
    RoutingStrategy,
)

_logger = logging.getLogger(__name__)


class OmniRouter:
    """Main OmniRoute router — intelligent AI request routing.

    Initialize with API keys, and the system automatically:
    - Discovers which providers are available
    - Creates optimal routing combos
    - Handles fallback with 3-layer resilience
    - Compresses tokens
    - Tracks costs

    The user only needs to provide API keys. Everything else is auto.
    """

    def __init__(self) -> None:
        # Core components
        self._catalog = ProviderCatalog()
        self._combo_engine = ComboEngine()
        self._resilience = ResilienceManager()
        self._compression = CompressionEngine()
        self._cost_tracker = CostTracker()
        self._quota_share = QuotaShareManager()
        self._discovery = AutoDiscovery(self._catalog, self._combo_engine, self._quota_share)

        # State
        self._initialized = False
        self._available_providers: dict[str, str] = {}  # provider -> api_key

    # ═══════════════════════════════════════════════════════════════
    #  INITIALIZATION
    # ═══════════════════════════════════════════════════════════════

    async def initialize(
        self,
        api_keys: dict[str, str] | None = None,
        enable_compression: bool = True,
    ) -> dict[str, Any]:
        """Initialize the OmniRoute system with API keys.

        This is the main entry point. Call once with all available API keys.
        The system will:
        1. Auto-detect all providers from keys
        2. Auto-generate optimal routing combos
        3. Register keys with quota sharing
        4. Enable compression if requested

        Args:
            api_keys: Dict mapping provider name to API key
                      E.g., {"openai": "sk-...", "anthropic": "sk-ant-..."}
            enable_compression: Whether to enable token compression

        Returns:
            Dict with initialization results
        """
        self._compression.enabled = enable_compression
        self._available_providers = api_keys or {}

        if api_keys:
            # Auto-discover everything from API keys
            combos = await self._discovery.discover_and_generate_combos(api_keys)

            self._initialized = True

            provider_count = len(api_keys)
            model_count = sum(
                len(self._catalog.get_models_for_provider(p))
                for p in api_keys
            )

            _logger.info(
                "OmniRouter: initialized with %d providers, %d models, %d combos",
                provider_count, model_count, len(combos),
            )

            return {
                "success": True,
                "providers_configured": provider_count,
                "models_available": model_count,
                "combos_auto_generated": len(combos),
                "compression_enabled": enable_compression,
                "combos": [c.name for c in combos],
                "free_providers": [p.name for p in self._catalog.list_free_providers()],
            }

        self._initialized = True
        return {
            "success": True,
            "providers_configured": 0,
            "models_available": 0,
            "combos_auto_generated": 0,
            "message": "No API keys provided. Configure keys via settings to enable OmniRoute.",
        }

    # ═══════════════════════════════════════════════════════════════
    #  ROUTING
    # ═══════════════════════════════════════════════════════════════

    async def route(
        self,
        combo_name: str = "auto",
        task_type: str = "chat",
        require_vision: bool = False,
        context: str = "",
        role: str = "writer",
    ) -> RoutingResult:
        """Route a request to the best provider-model pair.

        Automatically handles:
        - Selection from optimal combo
        - Resilience checks (circuit breaker, cooldown, lockout)
        - Token compression
        - Cost tracking

        Args:
            combo_name: Which combo to use ("auto", "auto/coding", "auto/cheap", etc.)
            task_type: Type of task ("chat", "coding", "reasoning", etc.)
            require_vision: Whether vision capabilities are needed
            context: The actual request text (for compression)
            role: Agent role for cost tracking

        Returns:
            RoutingResult with selected provider/model
        """
        if not self._initialized:
            return RoutingResult(
                selected_provider="",
                selected_model="",
                combo_name="uninitialized",
                estimated_cost_usd=0.0,
            )

        # Route via combo engine
        result = await self._combo_engine.route(
            combo_name=combo_name,
            task_type=task_type,
            require_vision=require_vision,
        )

        # Apply resilience check
        if result.selected_provider:
            key_hash = ""
            api_key = self._available_providers.get(result.selected_provider, "")
            if api_key:
                import hashlib
                key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            available, reason = self._resilience.is_available(
                result.selected_provider,
                result.selected_model,
                key_hash,
            )

            if not available:
                # Try fallback chain
                result.fallback_used = True
                for fallback in result.fallback_chain:
                    fallback_provider = fallback.split("/")[0]
                    available, _ = self._resilience.is_available(fallback_provider, "")
                    if available:
                        result.selected_provider = fallback_provider
                        break
                else:
                    # Last resort — any available provider
                    for provider in self._available_providers:
                        avail, _ = self._resilience.is_available(provider, "")
                        if avail:
                            result.selected_provider = provider
                            break

        return result

    # ═══════════════════════════════════════════════════════════════
    #  API KEY MANAGEMENT
    # ═══════════════════════════════════════════════════════════════

    async def add_key(self, provider: str, api_key: str) -> dict[str, Any]:
        """Add a new API key and auto-configure everything."""
        self._available_providers[provider] = api_key
        result = await self._discovery.add_api_key(api_key)

        # Re-generate combos with updated providers
        await self._discovery.discover_and_generate_combos(self._available_providers)

        return result

    async def remove_key(self, provider: str) -> bool:
        """Remove an API key and rebuild combos."""
        if provider in self._available_providers:
            del self._available_providers[provider]
            # Rebuild combos
            if self._available_providers:
                await self._discovery.refresh_from_provider_store(self._available_providers)
            else:
                self._combo_engine.clear_combos()
            return True
        return False

    # ═══════════════════════════════════════════════════════════════    # COMPRESSION
    # ═══════════════════════════════════════════════════════════════

    def compress(self, text: str, aggressive: bool = False) -> str:
        """Compress text using the OmniRoute compression engine."""
        return self._compression.compress(text, aggressive=aggressive)

    def compress_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Compress message content for LLM API calls."""
        return self._compression.compress_messages(messages)

    # ═══════════════════════════════════════════════════════════════
    #  RECORD CALLS
    # ═══════════════════════════════════════════════════════════════

    def record_call(
        self,
        provider: str = "",
        model: str = "",
        role: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration_ms: float = 0.0,
        success: bool = True,
    ) -> None:
        """Record an API call — tracks cost and updates health."""
        self._cost_tracker.record_call(
            provider=provider,
            model=model,
            role=role,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            success=success,
        )

        if success:
            self._combo_engine.record_success(provider, duration_ms)
            self._resilience.record_provider_success(provider)
        else:
            self._combo_engine.record_failure(provider)
            self._resilience.record_provider_failure(provider)

    # ═══════════════════════════════════════════════════════════════
    #  STATUS & QUERIES
    # ═══════════════════════════════════════════════════════════════

    @property
    def catalog(self) -> ProviderCatalog:
        return self._catalog

    @property
    def combo_engine(self) -> ComboEngine:
        return self._combo_engine

    @property
    def resilience(self) -> ResilienceManager:
        return self._resilience

    @property
    def compression_engine(self) -> CompressionEngine:
        return self._compression

    @property
    def cost_tracker(self) -> CostTracker:
        return self._cost_tracker

    @property
    def quota_share(self) -> QuotaShareManager:
        return self._quota_share

    @property
    def auto_discovery(self) -> AutoDiscovery:
        return self._discovery

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def get_provider_summary(self) -> list[dict[str, Any]]:
        """Get summary of all configured providers."""
        return self._discovery.get_provider_summary()

    def get_full_status(self) -> dict[str, Any]:
        """Get complete OmniRoute system status."""
        return {
            "initialized": self._initialized,
            "providers": {
                "configured": len(self._available_providers),
                "available": len(self._available_providers),
                "list": list(self._available_providers.keys()),
            },
            "combos": {
                "auto_generated": self._combo_engine.list_combos() != [],
                "count": len(self._combo_engine.list_combos()),
                "names": [c.name for c in self._combo_engine.list_combos()],
            },
            "resilience": self._resilience.stats(),
            "compression": self._compression.get_stats(),
            "cost_tracking": {
                "total_cost": self._cost_tracker.total_cost(),
                "total_calls": self._cost_tracker.total_calls(),
                "tokens": self._cost_tracker.total_tokens(),
            },
            "quota_sharing": self._quota_share.stats(),
            "discovery": {
                "keys_discovered": len(self._discovery.get_discovered_keys()),
                "providers": self._discovery.get_provider_summary(),
            },
        }
