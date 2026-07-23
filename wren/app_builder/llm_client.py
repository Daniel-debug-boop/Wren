"""Shared LLM Client — single implementation used by all app builder modules.

Zero external dependencies — uses only Python stdlib (urllib + asyncio).
OpenAI-compatible API, works with any provider (OpenAI, Anthropic, DeepSeek, etc.).

Optionally integrates with OmniRoute for intelligent provider routing:
  - Pass `omnirouter` to auto-select the best provider/model
  - Falls back gracefully to direct config when OmniRoute is not available
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def get_omnirouter() -> Any | None:
    """Lazy-import OmniRouter — returns None if the module isn't available.

    This allows the LLMClient to work even when the full Wren app server
    isn't running (e.g., CLI usage). OmniRoute integration is optional.
    """
    try:
        from wren.omniroute.omniroute_router import get_omnirouter as _get
        return _get()
    except (ImportError, ModuleNotFoundError):
        return None


class LLMClient:
    """Async HTTP client for LLM API calls with OmniRoute integration.

    Two modes:
    1. Direct mode: Pass api_key + model + base_url directly
    2. OmniRoute mode: Pass omnirouter for intelligent provider routing

    When both direct config AND omnirouter are provided, OmniRoute takes
    priority for provider selection, while max_tokens/temperature use
    the direct config as fallback defaults.
    """

    def __init__(
        self,
        api_key: str = "",
        model: str = "gpt-4o",
        base_url: str | None = None,
        max_tokens: int = 16384,
        temperature: float = 0.3,
        timeout_read: float = 120.0,
        omnirouter: Any | None = None,
        combo_name: str = "auto/coding",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._timeout = timeout_read
        self._omnirouter = omnirouter
        self._combo_name = combo_name

        # Track which provider was actually used (for cost tracking)
        self._last_provider: str = ""
        self._last_model: str = ""

    async def close(self) -> None:
        # urllib has no persistent client — nothing to clean up
        pass

    async def send(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        task_type: str = "coding",
        role: str = "writer",
    ) -> str:
        """Send a chat completion request and return the response text.

        If OmniRoute is configured, it handles provider selection and
        automatic failover. Otherwise, uses the directly configured
        api_key + model + base_url.

        Args:
            system_prompt: System-level instructions
            user_prompt: User message
            task_type: Task category for OmniRoute routing ("coding", "chat", etc.)
            role: Agent role for cost tracking

        Returns:
            Response text from the LLM

        Raises:
            RuntimeError: If API call fails or no providers available
        """
        # ── Determine provider, model, and API key ────────────────
        api_key = self.api_key
        model = self.model
        base_url = self.base_url

        if self._omnirouter is not None and self._omnirouter.is_initialized:
            # Use OmniRoute to pick the best provider/model
            route_result = await self._omnirouter.route(
                combo_name=self._combo_name,
                task_type=task_type,
                role=role,
            )

            if route_result.selected_provider:
                provider = route_result.selected_provider
                model = route_result.selected_model or model

                # Get API key from OmniRoute's store
                routed_key = self._omnirouter.get_api_key(provider)
                if routed_key:
                    api_key = routed_key

                # Get base URL from provider catalog
                provider_info = self._omnirouter.catalog.get_provider(provider)
                if provider_info:
                    base_url = provider_info.base_url.rstrip("/")

                self._last_provider = provider
                self._last_model = model

        if not api_key:
            raise RuntimeError(
                "No API key available. Either pass api_key directly or "
                "configure OmniRoute with API keys."
            )

        # ── Build and send the request ─────────────────────────────
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        body = json.dumps(payload).encode("utf-8")
        url = f"{base_url}/chat/completions"
        start_time = time.time()

        def _sync_request() -> str:
            req = Request(
                url,
                data=body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urlopen(req, timeout=self._timeout) as resp:
                    response_data = json.loads(resp.read().decode("utf-8"))
            except HTTPError as e:
                error_body = e.read().decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"LLM API error {e.code}: {error_body[:500]}"
                ) from e
            except URLError as e:
                raise RuntimeError(
                    f"LLM API connection failed: {e.reason}"
                ) from e
            except json.JSONDecodeError as e:
                raise RuntimeError(
                    f"LLM API returned invalid JSON: {e}"
                ) from e

            content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content or ""

        duration_ms = 0.0
        success = False
        try:
            result = await asyncio.to_thread(_sync_request)
            duration_ms = (time.time() - start_time) * 1000
            success = True
            return result
        except Exception:
            duration_ms = (time.time() - start_time) * 1000
            success = False
            raise
        finally:
            # Record the call in OmniRoute for cost tracking + health
            if self._omnirouter is not None and self._omnirouter.is_initialized:
                self._omnirouter.record_call(
                    provider=self._last_provider or "unknown",
                    model=self._last_model or model,
                    role=role,
                    input_tokens=len(system_prompt + user_prompt) // 4,  # rough estimate
                    output_tokens=0,  # will be updated by cost tracker
                    duration_ms=duration_ms,
                    success=success,
                )

    @classmethod
    def from_env(cls) -> "LLMClient":
        """Create client from environment variables.

        Uses:
          OPENAI_API_KEY  — API key (required)
          LLM_MODEL       — Model name (default: gpt-4o)
          LLM_BASE_URL    — Custom API base URL
        """
        import os
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("LLM_MODEL", "gpt-4o"),
            base_url=os.getenv("LLM_BASE_URL"),
        )
