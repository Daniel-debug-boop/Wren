"""LLM service for AI generation via OpenRouter API.

Supports both streaming and non-streaming completions,
with configurable model selection and error handling.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

_logger = logging.getLogger(__name__)

# Default OpenRouter endpoint
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_REFERER = "https://github.com/Daniel-debug-boop/Wren"
OPENROUTER_TITLE = "Wren AI"


class LLMService:
    """Service for interacting with LLM providers via OpenRouter."""

    def __init__(self, api_key: str | None = None, base_url: str = DEFAULT_BASE_URL):
        self.api_key = api_key or ""
        self.base_url = base_url.rstrip("/")

    @property
    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def is_configured(self) -> bool:
        """Check if the service has an API key configured."""
        return bool(self.api_key)

    async def chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Send a chat completion request."""
        url = f"{self.base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(url, headers=self._headers, json=payload)
                resp.raise_for_status()

                if stream:
                    return await self._handle_stream(resp)

                data = resp.json()
                return {
                    "success": True,
                    "content": data["choices"][0]["message"]["content"],
                    "model": data.get("model", model),
                    "usage": data.get("usage", {}),
                }

            except httpx.HTTPStatusError as e:
                _logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
                return {
                    "success": False,
                    "error": f"API error {e.response.status_code}: {e.response.text[:500]}",
                }
            except httpx.TimeoutException:
                _logger.error("LLM API timeout")
                return {"success": False, "error": "Request timed out after 120s"}
            except Exception as e:
                _logger.error(f"LLM request failed: {e}")
                return {"success": False, "error": str(e)}

    async def _handle_stream(self, response: httpx.Response) -> dict[str, Any]:
        """Process a streaming response."""
        content_parts: list[str] = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    if "content" in delta and delta["content"]:
                        content_parts.append(delta["content"])
                except json.JSONDecodeError:
                    continue

        full_content = "".join(content_parts)
        return {
            "success": True,
            "content": full_content,
            "model": "streaming",
            "usage": {},
        }

    async def generate_code(
        self,
        prompt: str,
        model: str = "openai/gpt-4o-mini",
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Generate code from a natural language prompt.

        This implements the Architect stage of the pipeline.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self.chat_completion(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=8000,
        )

    async def architect(self, prompt: str, model: str = "openai/gpt-4o-mini") -> dict[str, Any]:
        """Architect stage: design the system architecture."""
        system_prompt = """You are a senior software architect. Given a user's request:
1. Analyze requirements and constraints
2. Design the system architecture
3. Specify components, data flow, and tech choices
4. Output a detailed architecture plan

Be specific, practical, and production-focused."""
        return await self.generate_code(prompt, model, system_prompt)

    async def planner(self, architecture: str, model: str = "openai/gpt-4o-mini") -> dict[str, Any]:
        """Planner stage: create implementation steps."""
        system_prompt = """You are a technical project planner. Given an architecture plan:
1. Break down the implementation into concrete steps
2. Order steps by dependencies
3. Estimate effort for each step
4. Identify potential risks

Output a numbered implementation plan."""
        return await self.generate_code(architecture, model, system_prompt)

    async def writer(self, plan: str, model: str = "openai/gpt-4o-mini") -> dict[str, Any]:
        """Writer stage: generate code from plan."""
        system_prompt = """You are a senior developer. Given an implementation plan:
1. Write production-quality code for each step
2. Include proper error handling, types, and documentation
3. Follow best practices for the target language/framework
4. Output complete, working code files

Generate real, runnable code."""
        return await self.generate_code(plan, model, system_prompt)

    async def reviewer(self, code: str, model: str = "openai/gpt-4o-mini") -> dict[str, Any]:
        """Reviewer stage: audit generated code for bugs."""
        system_prompt = """You are a senior code reviewer. Given the generated code:
1. Check for bugs, security issues, and edge cases
2. Verify best practices are followed
3. Suggest improvements
4. Rate code quality (1-10)

Output a detailed code review with actionable feedback."""
        return await self.generate_code(code, model, system_prompt)
