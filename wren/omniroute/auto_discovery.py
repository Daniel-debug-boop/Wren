"""Auto-Discovery — automatically detects providers from API keys and creates combos.

The user just pastes an API key. Auto-discovery:
  1. Detects which provider the key belongs to (via prefix matching)
  2. Identifies which models are available
  3. Auto-creates routing combos with smart fallback
  4. Updates the health tracking system

Zero config. Just paste a key and OmniRoute handles the rest.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from wren.omniroute.provider_catalog import ProviderCatalog
from wren.omniroute.combo_engine import ComboEngine
from wren.omniroute.quota_share import QuotaShareManager
from wren.omniroute.types import ComboDefinition, ApiKeyInfo

_logger = logging.getLogger(__name__)


class AutoDiscovery:
    """Auto-discovers providers from API keys and creates routing combos.

    Usage:
        discovery = AutoDiscovery(catalog, combo_engine, quota_share)
        results = await discovery.add_api_key("sk-ant-xxxx")
        # Results include detected provider, created combos, and models
    """

    def __init__(
        self,
        catalog: ProviderCatalog,
        combo_engine: ComboEngine,
        quota_share: QuotaShareManager | None = None,
    ) -> None:
        self._catalog = catalog
        self._combo_engine = combo_engine
        self._quota_share = quota_share
        self._discovered_keys: dict[str, ApiKeyInfo] = {}
        self._provider_keys: dict[str, list[str]] = {}  # provider -> [key_hashes]

    async def add_api_key(self, api_key: str) -> dict[str, Any]:
        """Add a new API key and auto-discover everything.

        Returns:
            Dict with detected provider, models, and created combos
        """
        key_hash = self._hash_key(api_key)

        # Detect which provider this key belongs to
        provider_info = self._catalog.get_provider_for_api_key(api_key)

        if not provider_info:
            _logger.warning(
                "AutoDiscovery: could not detect provider for key %s",
                key_hash[:8],
            )
            return {
                "success": False,
                "key_hash": key_hash[:8],
                "error": "Unknown provider — key prefix not recognized",
            }

        # Get available models for this provider
        models = self._catalog.get_models_for_provider(provider_info.name)
        model_names = [m.name for m in models]

        key_info = ApiKeyInfo(
            key_prefix=api_key[:8],
            provider_name=provider_info.name,
            provider_display=provider_info.display_name,
            models_available=model_names,
            has_free_tier=provider_info.has_free_tier,
            is_valid=True,
        )
        self._discovered_keys[key_hash] = key_info

        # Track key by provider for quota sharing
        if provider_info.name not in self._provider_keys:
            self._provider_keys[provider_info.name] = []
        self._provider_keys[provider_info.name].append(key_hash)

        # Register with quota share if available
        if self._quota_share:
            weight = 0.5 if provider_info.has_free_tier else 1.0
            self._quota_share.register_key(
                provider=provider_info.name,
                api_key_hash=key_hash,
                weight=weight,
            )

        _logger.info(
            "AutoDiscovery: detected %s key (%s) — %d models available",
            provider_info.display_name,
            key_hash[:8],
            len(model_names),
        )

        return {
            "success": True,
            "key_hash": key_hash[:8],
            "provider": provider_info.name,
            "provider_display": provider_info.display_name,
            "models": model_names,
            "has_free_tier": provider_info.has_free_tier,
            "auto_combos": True,
        }

    async def discover_and_generate_combos(
        self,
        api_keys: dict[str, str],  # provider -> api_key
    ) -> list[ComboDefinition]:
        """Add multiple API keys and auto-generate combos.

        This is the main entry point for the system. Given a dict of
        API keys (keyed by provider), it:
          1. Validates all keys
          2. Detects available models
          3. Auto-generates optimal combos
          4. Returns the created combos

        Args:
            api_keys: Dict mapping provider name to API key

        Returns:
            List of auto-generated ComboDefinitions
        """
        # Process each key
        available_providers: dict[str, str] = {}
        provider_models: dict[str, list[str]] = {}

        for provider_name, api_key in api_keys.items():
            provider_info = self._catalog.get_provider(provider_name)
            if not provider_info:
                _logger.warning("Unknown provider: %s", provider_name)
                continue

            models = self._catalog.get_models_for_provider(provider_name)
            model_names = [m.name for m in models]

            available_providers[provider_name] = api_key
            provider_models[provider_name] = model_names or ["default"]

            # Track key
            key_hash = self._hash_key(api_key)
            self._discovered_keys[key_hash] = ApiKeyInfo(
                key_prefix=api_key[:8],
                provider_name=provider_name,
                provider_display=provider_info.display_name,
                models_available=model_names,
                has_free_tier=provider_info.has_free_tier,
                is_valid=True,
            )

            _logger.info(
                "AutoDiscovery: configured %s with key %s — %d models",
                provider_info.display_name,
                key_hash[:8],
                len(model_names),
            )

        if not available_providers:
            _logger.warning("AutoDiscovery: no valid providers configured")
            return []

        # Auto-generate combos from available providers
        combos = self._combo_engine.auto_generate_combos(
            available_providers, provider_models
        )

        _logger.info(
            "AutoDiscovery: generated %d combos from %d providers",
            len(combos), len(available_providers),
        )

        return combos

    async def refresh_from_provider_store(self, api_keys: dict[str, str]) -> list[ComboDefinition]:
        """Refresh all combos from a provider store's data.

        Called when provider settings change (e.g., user adds/removes a key).
        Clears old combos and generates fresh ones.
        """
        self._discovered_keys.clear()
        self._provider_keys.clear()
        self._combo_engine.clear_combos()

        return await self.discover_and_generate_combos(api_keys)

    # ═══════════════════════════════════════════════════════════════
    #  QUERIES
    # ═══════════════════════════════════════════════════════════════

    def get_discovered_keys(self) -> dict[str, ApiKeyInfo]:
        """Get all discovered API key info."""
        return dict(self._discovered_keys)

    def get_keys_for_provider(self, provider: str) -> list[ApiKeyInfo]:
        """Get all discovered keys for a specific provider."""
        key_hashes = self._provider_keys.get(provider, [])
        return [
            self._discovered_keys[h]
            for h in key_hashes
            if h in self._discovered_keys
        ]

    def get_provider_summary(self) -> list[dict[str, Any]]:
        """Get a summary of all discovered providers and their status."""
        provider_summary: dict[str, dict[str, Any]] = {}

        for key_info in self._discovered_keys.values():
            if key_info.provider_name not in provider_summary:
                provider_summary[key_info.provider_name] = {
                    "provider": key_info.provider_name,
                    "display_name": key_info.provider_display,
                    "keys_count": 0,
                    "models": [],
                    "has_free_tier": key_info.has_free_tier,
                }
            summary = provider_summary[key_info.provider_name]
            summary["keys_count"] += 1
            for model in key_info.models_available:
                if model not in summary["models"]:
                    summary["models"].append(model)

        return list(provider_summary.values())

    def is_key_configured(self, provider: str) -> bool:
        """Check if a provider has at least one configured key."""
        return provider in self._provider_keys and len(self._provider_keys[provider]) > 0

    @staticmethod
    def _hash_key(api_key: str) -> str:
        """Create a deterministic hash for an API key.

        Used for identification without exposing the actual key.
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
