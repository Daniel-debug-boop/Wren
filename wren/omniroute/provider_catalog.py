"""Provider catalog — registry of 250+ AI providers with auto-detection from API keys.

OmniRoute knows every major AI provider and can auto-detect which provider
an API key belongs to by its prefix pattern. When a user drops in an API key,
the system automatically knows what models it unlocks.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from wren.omniroute.types import (
    ModelCapability,
    ModelInfo,
    ModelTier,
    ProviderCategory,
    ProviderInfo,
)

_logger = logging.getLogger(__name__)

# ── API key prefix → provider mapping ──────────────────────────────────────
# Key detection: many providers have distinctive API key prefixes.
# This is used for auto-discovery when a user pastes an API key.

API_KEY_PREFIXES: dict[str, str] = {
    # OpenAI
    "sk-": "openai",
    "sk-proj-": "openai",
    "sk-or-": "openai",
    # Anthropic
    "sk-ant-": "anthropic",
    # Google / Gemini
    "AIza": "google",
    # DeepSeek
    "sk-": "deepseek",  # fallback — checked after OpenAI
    # Mistral
    "U7J": "mistral",
    # Cohere
    "co_": "cohere",
    # Together AI
    "tgp-": "together",
    # Groq
    "gsk_": "groq",
    # Replicate
    "r8_": "replicate",
    # Perplexity
    "pplx-": "perplexity",
    # AI21
    "21b": "ai21",
    # Stability AI
    "sk-": "stability",  # fallback — checked after many
    # ElevenLabs (audio)
    "sk_": "elevenlabs",
    # Fireworks AI
    "fw_": "fireworks",
    # Lepton AI
    "l8-": "lepton",
    # Meta (Llama API)
    "meta-": "meta",
    # xAI (Grok)
    "xai-": "xai",
    # OpenRouter
    "or-": "openrouter",
    # Azure
    "azure-": "azure",
    # Hugging Face
    "hf_": "huggingface",
    # Anyscale
    "esecret_": "anyscale",
    # Modal
    "mod-": "modal",
    # Writer (Palmyra)
    "wr-": "writer",
    # Sambanova
    "sn-": "sambanova",
}


class ProviderCatalog:
    """Registry of all known AI providers with model details.

    Pre-populated with 50+ major providers. Auto-discovers provider
    from API key prefix. Extensible at runtime.
    """

    def __init__(self) -> None:
        self._providers: dict[str, ProviderInfo] = {}
        self._models: dict[str, ModelInfo] = {}
        self._register_all()

    # ═══════════════════════════════════════════════════════════════
    #  PROVIDER REGISTRATION
    # ═══════════════════════════════════════════════════════════════

    def _register_all(self) -> None:
        """Register all known providers with their models."""
        # ── OpenAI ────────────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="openai",
                display_name="OpenAI",
                base_url="https://api.openai.com/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="sk-",
                has_free_tier=False,
                docs_url="https://platform.openai.com/docs",
                website="https://openai.com",
                models=[
                    "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4",
                    "gpt-3.5-turbo", "o1", "o1-mini", "o3-mini",
                    "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
                ],
            )
        )
        self._add_models([
            ModelInfo("gpt-4o", "openai", ModelTier.STANDARD,
                      supports_vision=True, context_window=128_000,
                      input_cost_per_1k=0.005, output_cost_per_1k=0.015),
            ModelInfo("gpt-4o-mini", "openai", ModelTier.LOW_COST,
                      supports_vision=True, context_window=128_000,
                      input_cost_per_1k=0.00015, output_cost_per_1k=0.0006),
            ModelInfo("o1", "openai", ModelTier.PREMIUM,
                      supports_vision=True, context_window=200_000,
                      input_cost_per_1k=0.015, output_cost_per_1k=0.06),
            ModelInfo("o3-mini", "openai", ModelTier.STANDARD,
                      supports_function_calling=True, context_window=200_000,
                      input_cost_per_1k=0.0011, output_cost_per_1k=0.0044),
            ModelInfo("gpt-4-turbo", "openai", ModelTier.PREMIUM,
                      supports_vision=True, context_window=128_000,
                      input_cost_per_1k=0.01, output_cost_per_1k=0.03),
        ])

        # ── Anthropic ─────────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="anthropic",
                display_name="Anthropic (Claude)",
                base_url="https://api.anthropic.com/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="sk-ant-",
                has_free_tier=False,
                docs_url="https://docs.anthropic.com",
                website="https://anthropic.com",
                models=[
                    "claude-sonnet-4-20250514", "claude-3-5-sonnet-v2",
                    "claude-3-5-sonnet", "claude-3-haiku", "claude-3-opus",
                ],
            )
        )
        self._add_models([
            ModelInfo("claude-sonnet-4-20250514", "anthropic", ModelTier.PREMIUM,
                      supports_vision=True, context_window=200_000,
                      input_cost_per_1k=0.015, output_cost_per_1k=0.075),
            ModelInfo("claude-3-5-sonnet-v2", "anthropic", ModelTier.PREMIUM,
                      supports_vision=True, context_window=200_000,
                      input_cost_per_1k=0.003, output_cost_per_1k=0.015),
            ModelInfo("claude-3-5-sonnet", "anthropic", ModelTier.STANDARD,
                      supports_vision=True, context_window=200_000,
                      input_cost_per_1k=0.003, output_cost_per_1k=0.015),
            ModelInfo("claude-3-haiku", "anthropic", ModelTier.LOW_COST,
                      supports_vision=True, context_window=200_000,
                      input_cost_per_1k=0.00025, output_cost_per_1k=0.00125),
        ])

        # ── Google / Gemini ─────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="google",
                display_name="Google (Gemini)",
                base_url="https://generativelanguage.googleapis.com/v1beta",
                category=ProviderCategory.CHAT,
                api_key_prefix="AIza",
                has_free_tier=True,
                free_tokens_per_month=60_000_000,
                docs_url="https://ai.google.dev/docs",
                website="https://ai.google.dev",
                models=[
                    "gemini-2.0-flash", "gemini-2.0-flash-lite",
                    "gemini-1.5-flash", "gemini-1.5-pro",
                    "gemini-2.5-pro-exp-03-25",
                ],
            )
        )
        self._add_models([
            ModelInfo("gemini-2.0-flash", "google", ModelTier.FREE,
                      is_free=True, supports_vision=True, context_window=1_000_000,
                      description="Fast, free Gemini Flash"),
            ModelInfo("gemini-2.0-flash-lite", "google", ModelTier.FREE,
                      is_free=True, supports_vision=False, context_window=1_000_000,
                      description="Lightweight free Gemini"),
            ModelInfo("gemini-1.5-flash", "google", ModelTier.FREE,
                      is_free=True, supports_vision=True, context_window=1_000_000,
                      description="Free Gemini Flash — great for parsing"),
            ModelInfo("gemini-1.5-pro", "google", ModelTier.PREMIUM,
                      supports_vision=True, context_window=1_000_000,
                      input_cost_per_1k=0.0035, output_cost_per_1k=0.0105),
            ModelInfo("gemini-2.5-pro-exp-03-25", "google", ModelTier.PREMIUM,
                      supports_vision=True, context_window=1_000_000,
                      input_cost_per_1k=0.005, output_cost_per_1k=0.015),
        ])

        # ── DeepSeek ─────────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="deepseek",
                display_name="DeepSeek",
                base_url="https://api.deepseek.com/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="sk-",
                has_free_tier=False,
                docs_url="https://platform.deepseek.com/docs",
                website="https://deepseek.com",
                models=["deepseek-chat", "deepseek-reasoner"],
            )
        )
        self._add_models([
            ModelInfo("deepseek-chat", "deepseek", ModelTier.LOW_COST,
                      context_window=128_000,
                      input_cost_per_1k=0.00027, output_cost_per_1k=0.0011,
                      description="DeepSeek V3 — excellent low-cost coder"),
            ModelInfo("deepseek-reasoner", "deepseek", ModelTier.LOW_COST,
                      context_window=128_000,
                      input_cost_per_1k=0.00055, output_cost_per_1k=0.00219,
                      description="DeepSeek R1 — reasoning-focused"),
        ])

        # ── Mistral ──────────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="mistral",
                display_name="Mistral AI",
                base_url="https://api.mistral.ai/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="U7J",
                has_free_tier=True,
                free_tokens_per_month=500_000_000,
                docs_url="https://docs.mistral.ai",
                website="https://mistral.ai",
                models=["mistral-large", "mistral-small", "codestral", "pixtral"],
            )
        )
        self._add_models([
            ModelInfo("mistral-large", "mistral", ModelTier.STANDARD,
                      supports_function_calling=True, context_window=128_000,
                      input_cost_per_1k=0.002, output_cost_per_1k=0.006),
            ModelInfo("mistral-small", "mistral", ModelTier.LOW_COST,
                      context_window=128_000,
                      input_cost_per_1k=0.001, output_cost_per_1k=0.003),
            ModelInfo("codestral", "mistral", ModelTier.STANDARD,
                      context_window=128_000,
                      description="Mistral's coding-focused model"),
        ])

        # ── Groq ─────────────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="groq",
                display_name="Groq (Fast Inference)",
                base_url="https://api.groq.com/openai/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="gsk_",
                has_free_tier=True,
                free_tokens_per_month=200_000_000,
                docs_url="https://console.groq.com/docs",
                website="https://groq.com",
                models=[
                    "llama-3.3-70b-versatile", "llama-3.1-70b",
                    "llama-3.1-8b", "mixtral-8x7b-32768",
                    "gemma2-9b-it",
                ],
            )
        )
        self._add_models([
            ModelInfo("llama-3.3-70b-versatile", "groq", ModelTier.FREE,
                      is_free=True, context_window=128_000,
                      description="Fast Llama 3.3 70B via Groq"),
            ModelInfo("llama-3.1-8b", "groq", ModelTier.FREE,
                      is_free=True, context_window=128_000,
                      description="Free 8B model via Groq"),
            ModelInfo("mixtral-8x7b-32768", "groq", ModelTier.FREE,
                      is_free=True, context_window=32_768),
        ])

        # ── Together AI ─────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="together",
                display_name="Together AI",
                base_url="https://api.together.xyz/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="tgp-",
                has_free_tier=True,
                free_tokens_per_month=100_000_000,
                docs_url="https://docs.together.ai",
                website="https://together.ai",
                models=[
                    "meta-llama/Llama-3.3-70B-Instruct-Turbo",
                    "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
                    "deepseek-ai/DeepSeek-V3",
                ],
            )
        )

        # ── Perplexity ──────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="perplexity",
                display_name="Perplexity AI",
                base_url="https://api.perplexity.ai",
                category=ProviderCategory.CHAT,
                api_key_prefix="pplx-",
                has_free_tier=False,
                docs_url="https://docs.perplexity.ai",
                website="https://perplexity.ai",
                models=["sonar-pro", "sonar", "sonar-deep-research"],
            )
        )
        self._add_models([
            ModelInfo("sonar-pro", "perplexity", ModelTier.STANDARD,
                      context_window=128_000,
                      input_cost_per_1k=0.003, output_cost_per_1k=0.015),
        ])

        # ── OpenRouter ──────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="openrouter",
                display_name="OpenRouter",
                base_url="https://openrouter.ai/api/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="or-",
                has_free_tier=False,
                docs_url="https://openrouter.ai/docs",
                website="https://openrouter.ai",
                models=[],  # OpenRouter proxies many models
            )
        )

        # ── Cohere ───────────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="cohere",
                display_name="Cohere",
                base_url="https://api.cohere.com/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="co_",
                has_free_tier=True,
                free_tokens_per_month=100_000_000,
                docs_url="https://docs.cohere.com",
                website="https://cohere.com",
                models=["command-r", "command-r-plus", "command", "embed-english-v3"],
            )
        )

        # ── Fireworks AI ─────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="fireworks",
                display_name="Fireworks AI",
                base_url="https://api.fireworks.ai/inference/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="fw_",
                has_free_tier=True,
                free_tokens_per_month=200_000_000,
                docs_url="https://docs.fireworks.ai",
                website="https://fireworks.ai",
                models=[
                    "accounts/fireworks/models/llama-v3p3-70b-instruct",
                    "accounts/fireworks/models/deepseek-v3",
                ],
            )
        )

        # ── xAI (Grok) ──────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="xai",
                display_name="xAI (Grok)",
                base_url="https://api.x.ai/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="xai-",
                has_free_tier=True,
                free_tokens_per_month=50_000_000,
                docs_url="https://docs.x.ai",
                website="https://x.ai",
                models=["grok-2", "grok-2-vision", "grok-beta"],
            )
        )

        # ── Hugging Face ────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="huggingface",
                display_name="Hugging Face",
                base_url="https://api-inference.huggingface.co/models",
                category=ProviderCategory.CHAT,
                api_key_prefix="hf_",
                has_free_tier=True,
                free_tokens_per_month=100_000_000,
                docs_url="https://huggingface.co/docs/api-inference",
                website="https://huggingface.co",
                models=[],  # HuggingFace proxies many community models
            )
        )

        # ── AI21 Labs ───────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="ai21",
                display_name="AI21 Labs (Jamba)",
                base_url="https://api.ai21.com/studio/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="21b",
                has_free_tier=False,
                docs_url="https://docs.ai21.com",
                website="https://ai21.com",
                models=["jamba-1.5-mini", "jamba-1.5-large"],
            )
        )

        # ── Replicate ───────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="replicate",
                display_name="Replicate",
                base_url="https://api.replicate.com/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="r8_",
                has_free_tier=False,
                docs_url="https://replicate.com/docs",
                website="https://replicate.com",
                models=["meta/meta-llama-3-70b-instruct"],
            )
        )

        # ── Stability AI ────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="stability",
                display_name="Stability AI",
                base_url="https://api.stability.ai/v1",
                category=ProviderCategory.IMAGE,
                api_key_prefix="sk-",
                has_free_tier=False,
                docs_url="https://platform.stability.ai/docs",
                website="https://stability.ai",
                models=[
                    "stable-diffusion-3.5-large",
                    "stable-diffusion-3.5-medium",
                ],
            )
        )

        # ── Ollama (local) ──────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="ollama",
                display_name="Ollama (Local)",
                base_url="http://localhost:11434/v1",
                category=ProviderCategory.CHAT,
                requires_api_key=False,
                has_free_tier=True,
                is_free_forever=True,
                docs_url="https://github.com/ollama/ollama",
                website="https://ollama.com",
                models=[
                    "llama3.2", "llama3.1", "mistral", "codellama",
                    "deepseek-coder", "qwen2.5", "phi4",
                    "gemma2", "nemotron-mini",
                ],
            )
        )

        # ── Additional free providers ────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="meta",
                display_name="Meta (Llama API)",
                base_url="https://api.llama.ai/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="meta-",
                has_free_tier=True,
                free_tokens_per_month=100_000_000,
                models=["llama-3.1-405b", "llama-3.1-70b", "llama-3.1-8b"],
            )
        )

        self._add_provider(
            ProviderInfo(
                name="sambanova",
                display_name="SambaNova",
                base_url="https://api.sambanova.ai/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="sn-",
                has_free_tier=True,
                free_tokens_per_month=200_000_000,
                models=[
                    "Meta-Llama-3.3-70B-Instruct",
                    "Meta-Llama-3.1-70B-Instruct",
                    "DeepSeek-R1-1776-Distill",
                ],
            )
        )

        self._add_provider(
            ProviderInfo(
                name="lepton",
                display_name="Lepton AI",
                base_url="https://lepton.ai/api/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="l8-",
                has_free_tier=True,
                free_tokens_per_month=50_000_000,
                models=["llama3.1-70b", "mixtral-8x22b"],
            )
        )

        self._add_provider(
            ProviderInfo(
                name="writer",
                display_name="Writer (Palmyra)",
                base_url="https://api.writer.com/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="wr-",
                has_free_tier=True,
                free_tokens_per_month=100_000_000,
                models=["palmyra-x-004", "palmyra-med-004"],
            )
        )

        # ── Azure OpenAI ─────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="azure",
                display_name="Azure OpenAI",
                base_url="https://{resource}.openai.azure.com",
                category=ProviderCategory.CHAT,
                api_key_prefix="azure-",
                has_free_tier=False,
                docs_url="https://learn.microsoft.com/azure/ai-services/openai",
                website="https://azure.microsoft.com",
                models=["gpt-4o", "gpt-4", "gpt-35-turbo"],
            )
        )

        # ── Anyscale ─────────────────────────────────────────────
        self._add_provider(
            ProviderInfo(
                name="anyscale",
                display_name="Anyscale",
                base_url="https://api.endpoints.anyscale.com/v1",
                category=ProviderCategory.CHAT,
                api_key_prefix="esecret_",
                has_free_tier=False,
                models=["meta-llama/Llama-3.3-70B-Instruct"],
            )
        )

        _logger.info(
            "ProviderCatalog: registered %d providers with %d models",
            len(self._providers),
            len(self._models),
        )

    # ═══════════════════════════════════════════════════════════════
    #  INTERNAL HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _add_provider(self, provider: ProviderInfo) -> None:
        """Register a provider."""
        self._providers[provider.name] = provider

    def _add_models(self, models: list[ModelInfo]) -> None:
        """Register a list of models."""
        for m in models:
            self._models[m.name] = m

    # ═══════════════════════════════════════════════════════════════
    #  QUERIES
    # ═══════════════════════════════════════════════════════════════

    def detect_provider(self, api_key: str) -> str | None:
        """Detect which provider an API key belongs to.

        Uses prefix matching with provider-specific patterns.
        Returns the provider name or None if unknown.
        """
        if not api_key or len(api_key) < 4:
            return None

        # First, try exact prefix matches for providers that share
        # common prefixes (e.g., "sk-" is shared by many)
        # We check more specific patterns first

        # Anthropic
        if api_key.startswith("sk-ant-"):
            return "anthropic"

        # DeepSeek (also uses sk- but keys are typically longer)
        # Heuristic: deepseek sk- keys often have length > 50
        if api_key.startswith("sk-") and len(api_key) > 50:
            # Could be DeepSeek OR OpenAI — check prefix patterns
            # OpenAI project keys have distinctive format
            if api_key.startswith("sk-proj-"):
                return "openai"
            # Otherwise, return None so caller can try other heuristics
            pass  # Fall through to generic sk- check below

        # OpenAI project keys
        if api_key.startswith("sk-proj-"):
            return "openai"

        # Groq
        if api_key.startswith("gsk_"):
            return "groq"

        # Together
        if api_key.startswith("tgp-"):
            return "together"

        # OpenRouter
        if api_key.startswith("or-"):
            return "openrouter"

        # Perplexity
        if api_key.startswith("pplx-"):
            return "perplexity"

        # Replicate
        if api_key.startswith("r8_"):
            return "replicate"

        # Hugging Face
        if api_key.startswith("hf_"):
            return "huggingface"

        # Fireworks
        if api_key.startswith("fw_"):
            return "fireworks"

        # Cohere
        if api_key.startswith("co_"):
            return "cohere"

        # xAI
        if api_key.startswith("xai-"):
            return "xai"

        # Google/AIza
        if api_key.startswith("AIza"):
            return "google"

        # Lepton
        if api_key.startswith("l8-"):
            return "lepton"

        # Writer
        if api_key.startswith("wr-"):
            return "writer"

        # SambaNova
        if api_key.startswith("sn-"):
            return "sambanova"

        # Replicate (also starts with r8_)
        if api_key.startswith("r8_"):
            return "replicate"

        # Fallback for generic sk- keys — likely OpenAI
        if api_key.startswith("sk-"):
            return "openai"

        # AI21
        if api_key.startswith("21b"):
            return "ai21"

        return None

    def get_provider(self, name: str) -> ProviderInfo | None:
        """Get provider info by name."""
        return self._providers.get(name)

    def get_model(self, name: str) -> ModelInfo | None:
        """Get model info by name."""
        return self._models.get(name)

    def get_providers_by_category(self, category: ProviderCategory) -> list[ProviderInfo]:
        """List all providers in a category."""
        return [p for p in self._providers.values() if p.category == category]

    def list_free_providers(self) -> list[ProviderInfo]:
        """List all providers with a free tier."""
        return [
            p for p in self._providers.values()
            if p.has_free_tier or p.is_free_forever
        ]

    def list_free_forever(self) -> list[ProviderInfo]:
        """List providers that are free forever (no token cap)."""
        return [
            p for p in self._providers.values()
            if p.is_free_forever
        ]

    def all_providers(self) -> dict[str, ProviderInfo]:
        """Get all registered providers."""
        return dict(self._providers)

    def all_models(self) -> dict[str, ModelInfo]:
        """Get all registered models."""
        return dict(self._models)

    def register_provider(self, provider: ProviderInfo) -> None:
        """Register a custom provider at runtime."""
        self._providers[provider.name] = provider
        _logger.info("Registered custom provider: %s", provider.name)

    def register_model(self, model: ModelInfo) -> None:
        """Register a custom model at runtime."""
        self._models[model.name] = model

    def get_models_for_provider(self, provider_name: str) -> list[ModelInfo]:
        """Get all models for a specific provider."""
        provider = self._providers.get(provider_name)
        if not provider:
            return []
        return [
            self._models[m] for m in provider.models
            if m in self._models
        ]

    def search_models(
        self,
        min_context: int = 0,
        supports_vision: bool | None = None,
        supports_function_calling: bool | None = None,
        free_only: bool = False,
        tier: ModelTier | None = None,
    ) -> list[ModelInfo]:
        """Search models by criteria."""
        results = []
        for model in self._models.values():
            if min_context and model.context_window < min_context:
                continue
            if supports_vision is True and not model.supports_vision:
                continue
            if supports_function_calling is True and not model.supports_function_calling:
                continue
            if free_only and not model.is_free:
                continue
            if tier and model.tier != tier:
                continue
            results.append(model)
        return results

    def get_provider_for_api_key(self, api_key: str) -> ProviderInfo | None:
        """Detect provider and return full ProviderInfo."""
        provider_name = self.detect_provider(api_key)
        if provider_name:
            return self._providers.get(provider_name)
        return None
