"""Shared LLM Client — single implementation used by all app builder modules.

Eliminates the duplicate LLMClient classes that existed in:
  - agents/architect_agent.py
  - build_orchestrator.py
"""

from __future__ import annotations

from typing import Any

import httpx


class LLMClient:
    """Async HTTP client for LLM API calls with configurable model, tokens, and timeout."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: str | None = None,
        max_tokens: int = 16384,
        temperature: float = 0.3,
        timeout_read: float = 120.0,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=15.0, read=timeout_read, write=60.0),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def send(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat completion request and return the response text."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        response = await self._client.post(
            f"{self.base_url}/chat/completions", json=payload
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return content or ""

    @classmethod
    def from_env(cls) -> "LLMClient":
        """Create client from environment variables (OPENAI_API_KEY, LLM_MODEL, etc.)."""
        import os
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("LLM_MODEL", "gpt-4o"),
            base_url=os.getenv("LLM_BASE_URL"),
        )
