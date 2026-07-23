"""Multi-Provider LLM Support — unified interface for OpenAI, Anthropic, Gemini, and local models.

Each provider implements the same async interface:
    async def send(system_prompt: str, user_prompt: str) -> str

The ProviderRouter automatically selects the best provider based on:
  - Available API keys
  - Model capability requirements (vision, 3d, code)
  - Cost optimization
  - Provider availability
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

_logger = logging.getLogger(__name__)


# ── Provider configuration ────────────────────────────────────────────────


@dataclass
class ProviderConfig:
    """Configuration for a single LLM provider."""

    name: str
    api_key_env: str
    default_model: str
    base_url: str | None = None
    supports_vision: bool = False
    supports_streaming: bool = True
    cost_per_1k_input: float = 0.0  # USD
    cost_per_1k_output: float = 0.0  # USD
    models: list[str] = field(default_factory=list)
    weight: int = 10  # Higher = preferred when multiple providers available


# ── Registry of built-in providers ────────────────────────────────────────

BUILTIN_PROVIDERS: dict[str, ProviderConfig] = {
    "openai": ProviderConfig(
        name="openai",
        api_key_env="OPENAI_API_KEY",
        default_model="gpt-4o",
        base_url=None,
        supports_vision=True,
        models=[
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4",
            "o1", "o3-mini",
        ],
        cost_per_1k_input=0.0025,
        cost_per_1k_output=0.01,
        weight=50,
    ),
    "anthropic": ProviderConfig(
        name="anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        default_model="claude-sonnet-4-20250514",
        base_url=None,
        supports_vision=True,
        models=[
            "claude-sonnet-4-20250514",
            "claude-sonnet-4.5-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ],
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        weight=40,
    ),
    "google": ProviderConfig(
        name="google",
        api_key_env="GOOGLE_API_KEY",
        default_model="gemini-2.0-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        supports_vision=True,
        models=[
            "gemini-2.0-flash", "gemini-2.0-pro",
            "gemini-1.5-flash", "gemini-1.5-pro",
        ],
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0004,
        weight=30,
    ),
    "deepseek": ProviderConfig(
        name="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        default_model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        supports_vision=False,
        models=["deepseek-chat", "deepseek-reasoner"],
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0002,
        weight=35,
    ),
    "local": ProviderConfig(
        name="local",
        api_key_env="LOCAL_API_KEY",
        default_model="local-model",
        base_url=os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:1234/v1"),
        supports_vision=False,
        supports_streaming=True,
        models=["local-model"],
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        weight=5,
    ),
}


# ── Provider client implementations ───────────────────────────────────────


class OpenAIProvider:
    """OpenAI API provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str | None = None):
        import httpx

        self.model = model
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.max_tokens = 16384
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=15.0, read=120.0, write=60.0),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )

    async def send(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": self.max_tokens,
            "temperature": temperature,
        }
        response = await self._client.post(f"{self.base_url}/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"] or ""

    async def close(self) -> None:
        await self._client.aclose()


class AnthropicProvider:
    """Anthropic Claude API provider."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", base_url: str | None = None):
        import httpx

        self.model = model
        self.base_url = (base_url or "https://api.anthropic.com/v1").rstrip("/")
        self.max_tokens = 8192
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=15.0, read=120.0, write=60.0),
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )

    async def send(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        payload = {
            "model": self.model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "max_tokens": self.max_tokens,
            "temperature": temperature,
        }
        response = await self._client.post(f"{self.base_url}/messages", json=payload)
        response.raise_for_status()
        data = response.json()
        # Extract text from content blocks
        content = data.get("content", [])
        texts = [block["text"] for block in content if block.get("type") == "text"]
        return "\n".join(texts)

    async def close(self) -> None:
        await self._client.aclose()


class GoogleProvider:
    """Google Gemini API provider."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", base_url: str | None = None):
        import httpx

        self.model = model
        self.base_url = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=15.0, read=120.0, write=60.0),
        )

    async def send(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 8192,
            },
        }
        response = await self._client.post(
            f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            texts = [p["text"] for p in parts if "text" in p]
            return "\n".join(texts)
        return ""

    async def close(self) -> None:
        await self._client.aclose()


class LocalProvider:
    """Local LLM provider (LM Studio, Ollama, etc.)."""

    def __init__(self, api_key: str, model: str = "local-model", base_url: str | None = None):
        import httpx

        self.model = model
        self.base_url = (base_url or os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:1234/v1")).rstrip("/")
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=30.0, read=300.0, write=120.0),
            headers={
                "Authorization": f"Bearer {api_key}" if api_key else "",
                "Content-Type": "application/json",
            },
        )

    async def send(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 8192,
            "temperature": temperature,
        }
        response = await self._client.post(f"{self.base_url}/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"] or ""

    async def close(self) -> None:
        await self._client.aclose()


# ── Provider Router ────────────────────────────────────────────────────────


@dataclass
class RouteResult:
    """Result of routing a request to a provider."""

    provider: str
    model: str
    content: str
    duration_s: float = 0.0


class ProviderRouter:
    """Routes LLM requests to the best available provider.

    Usage:
        router = ProviderRouter()
        router.configure(openai_api_key="sk-...", anthropic_api_key="sk-ant-...")
        result = await router.route("Write code", "Generate a React component")
    """

    def __init__(self):
        self._providers: dict[str, Any] = {}
        self._configs: dict[str, ProviderConfig] = {}
        self._loaded = False

    def configure(
        self,
        openai_api_key: str | None = None,
        anthropic_api_key: str | None = None,
        google_api_key: str | None = None,
        deepseek_api_key: str | None = None,
        local_api_key: str | None = None,
        preferred_provider: str | None = None,
    ) -> None:
        """Configure available providers with API keys."""
        self._providers.clear()
        self._configs.clear()

        # Priority order for routing
        provider_order = [
            ("openai", openai_api_key, OpenAIProvider),
            ("anthropic", anthropic_api_key, AnthropicProvider),
            ("google", google_api_key, GoogleProvider),
            ("deepseek", deepseek_api_key, OpenAIProvider),  # OpenAI-compatible API
            ("local", local_api_key, LocalProvider),
        ]

        for name, api_key, provider_cls in provider_order:
            if api_key:
                config = BUILTIN_PROVIDERS.get(name)
                if config:
                    # Set base_url for deepseek
                    kwargs = {"api_key": api_key}
                    if name == "deepseek":
                        kwargs["base_url"] = "https://api.deepseek.com/v1"
                        kwargs["model"] = "deepseek-chat"
                    elif name == "local":
                        kwargs["api_key"] = api_key or ""
                        kwargs["model"] = "local-model"
                        kwargs["base_url"] = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:1234/v1")
                    elif name == "google":
                        kwargs["model"] = config.default_model
                    else:
                        kwargs["model"] = config.default_model

                    self._providers[name] = provider_cls(**kwargs)
                    self._configs[name] = config

        # Also check environment variables as fallback
        for name, config in BUILTIN_PROVIDERS.items():
            if name not in self._providers:
                env_key = os.getenv(config.api_key_env)
                if env_key:
                    provider_cls_map = {
                        "openai": OpenAIProvider,
                        "anthropic": AnthropicProvider,
                        "google": GoogleProvider,
                        "deepseek": OpenAIProvider,
                        "local": LocalProvider,
                    }
                    cls = provider_cls_map.get(name)
                    if cls:
                        kwargs = {"api_key": env_key}
                        if name == "deepseek":
                            kwargs["base_url"] = "https://api.deepseek.com/v1"
                            kwargs["model"] = "deepseek-chat"
                        elif name == "local":
                            kwargs["model"] = "local-model"
                            kwargs["base_url"] = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:1234/v1")
                        elif name == "google":
                            kwargs["model"] = config.default_model
                        else:
                            kwargs["model"] = config.default_model

                        self._providers[name] = cls(**kwargs)
                        self._configs[name] = config

        # If preferred provider is set and available, boost its weight
        if preferred_provider and preferred_provider in self._configs:
            for name in self._configs:
                self._configs[name].weight = 5  # Lower all
            self._configs[preferred_provider].weight = 100  # Boost preferred

        self._loaded = bool(self._providers)

    async def route(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        require_vision: bool = False,
        task_type: str = "code",  # code, architecture, review, research
    ) -> RouteResult:
        """Send a request to the best available provider.

        Args:
            system_prompt: System instruction
            user_prompt: User message
            temperature: Generation temperature
            require_vision: Whether the task requires vision capabilities
            task_type: Type of task for model selection

        Returns:
            RouteResult with provider, model, content, and duration
        """
        if not self._loaded:
            raise RuntimeError("No LLM providers configured. Set at least one API key.")

        # Select the best provider
        provider_name = self._select_provider(require_vision, task_type)
        provider = self._providers[provider_name]
        config = self._configs[provider_name]

        _logger.debug("ProviderRouter: routing to %s/%s (%s)", provider_name, config.default_model, task_type)

        start = time.time()
        try:
            content = await provider.send(system_prompt, user_prompt, temperature)
            elapsed = time.time() - start
            return RouteResult(
                provider=provider_name,
                model=config.default_model,
                content=content,
                duration_s=elapsed,
            )
        except Exception as e:
            # Fallback: try the next best provider
            _logger.warning("ProviderRouter: %s failed: %s. Trying fallback...", provider_name, e)
            for fallback_name in self._providers:
                if fallback_name != provider_name:
                    try:
                        fallback = self._providers[fallback_name]
                        content = await fallback.send(system_prompt, user_prompt, temperature)
                        elapsed = time.time() - start
                        return RouteResult(
                            provider=fallback_name,
                            model=self._configs[fallback_name].default_model,
                            content=content,
                            duration_s=elapsed,
                        )
                    except Exception:
                        continue
            raise

    def _select_provider(self, require_vision: bool, task_type: str) -> str:
        """Select the best provider based on requirements and weights."""
        candidates = []

        for name, provider in self._providers.items():
            config = self._configs.get(name)
            if not config:
                continue

            # Skip if vision required but provider doesn't support it
            if require_vision and not config.supports_vision:
                continue

            # Task-specific model selection
            if task_type == "architecture":
                # Prefer models with strong reasoning
                if name in ("anthropic", "openai"):
                    candidates.append((config.weight + 20, name))
                else:
                    candidates.append((config.weight, name))
            elif task_type == "code":
                # Prefer coding-specialized models
                if name in ("anthropic", "deepseek"):
                    candidates.append((config.weight + 15, name))
                else:
                    candidates.append((config.weight, name))
            elif task_type == "review":
                # Prefer cheaper models for review
                if name in ("openai", "google"):
                    candidates.append((config.weight + 10, name))
                else:
                    candidates.append((config.weight, name))
            else:
                candidates.append((config.weight, name))

        if not candidates:
            # Fallback: use any available provider
            candidates = [(0, name) for name in self._providers]

        candidates.sort(key=lambda x: -x[0])
        return candidates[0][1]

    async def close_all(self) -> None:
        """Close all provider connections."""
        for provider in self._providers.values():
            try:
                await provider.close()
            except Exception:
                pass

    @property
    def available_providers(self) -> list[str]:
        return list(self._providers.keys())

    def is_configured(self, provider_name: str) -> bool:
        return provider_name in self._providers
