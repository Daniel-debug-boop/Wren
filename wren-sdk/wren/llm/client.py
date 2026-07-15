"""LLM client for Wren SDK.

Wraps litellm with a clean, async-first interface.
Supports streaming, fallback strategies, and tool calling.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable

import litellm

from wren.llm.message import (
    Message,
    MessageRole,
    TextContent,
    ToolUseContent,
    ContentBlock,
)
from wren.utils.models import WrenModel
from wren.utils.async_utils import async_retry

logger = logging.getLogger("wren.llm")


class TokenUsage(WrenModel):
    """Token usage statistics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float | None = None


class LLMResponse(WrenModel):
    """Response from LLM."""

    content: str
    tool_calls: list[ToolCallInfo] | None = None
    usage: TokenUsage | None = None
    model: str | None = None
    finish_reason: str | None = None


class ToolCallInfo(WrenModel):
    """Tool call extracted from LLM response."""

    id: str
    name: str
    arguments: dict[str, Any]


class LLMStreamChunk(WrenModel):
    """A chunk from LLM streaming."""

    delta: str = ""
    tool_call_delta: ToolCallInfo | None = None
    usage: TokenUsage | None = None
    finish_reason: str | None = None


@dataclass
class LLMConfig:
    """LLM configuration."""

    model: str = "gpt-4o"
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: float = 120.0
    fallback_models: list[str] | None = None


class LLMClient:
    """Async LLM client wrapping litellm.

    Features:
    - Async-first API
    - Streaming support
    - Tool/function calling
    - Automatic retries
    - Fallback strategies
    - Token tracking
    """

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        self._total_usage = TokenUsage()

    @property
    def total_usage(self) -> TokenUsage:
        """Get total token usage across all calls."""
        return self._total_usage

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Send chat completion request.

        Args:
            messages: List of messages.
            tools: Tool definitions for function calling.
            tool_choice: Tool selection strategy ("auto", "none", or specific).
            temperature: Override default temperature.
            max_tokens: Override default max tokens.

        Returns:
            LLMResponse with content and optional tool calls.
        """
        openai_messages = [m.to_openai() for m in messages]

        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": openai_messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "timeout": self.config.timeout,
        }

        if self.config.api_key:
            kwargs["api_key"] = self.config.api_key
        if self.config.base_url:
            kwargs["base_url"] = self.config.base_url

        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice

        try:
            response = await self._call_with_fallback(**kwargs)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

        return self._parse_response(response)

    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[LLMStreamChunk]:
        """Stream chat completion response.

        Yields chunks as they arrive from the LLM.
        """
        openai_messages = [m.to_openai() for m in messages]

        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": openai_messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "timeout": self.config.timeout,
            "stream": True,
        }

        if self.config.api_key:
            kwargs["api_key"] = self.config.api_key
        if self.config.base_url:
            kwargs["base_url"] = self.config.base_url
        if tools:
            kwargs["tools"] = tools

        response = await litellm.acompletion(**kwargs)

        async for chunk in response:
            yield self._parse_stream_chunk(chunk)

    async def _call_with_fallback(self, **kwargs) -> Any:
        """Call LLM with fallback to other models on failure."""
        models_to_try = [self.config.model]
        if self.config.fallback_models:
            models_to_try.extend(self.config.fallback_models)

        last_error = None
        for model in models_to_try:
            try:
                kwargs["model"] = model
                return await litellm.acompletion(**kwargs)
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}, trying next...")
                last_error = e
                continue

        raise last_error or RuntimeError("No models available")

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse litellm response into LLMResponse."""
        choice = response.choices[0]
        message = choice.message

        # Extract content
        content = message.content or ""

        # Extract tool calls
        tool_calls = None
        if message.tool_calls:
            tool_calls = []
            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(
                    ToolCallInfo(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                    )
                )

        # Extract usage
        usage = None
        if response.usage:
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
            self._total_usage.prompt_tokens += usage.prompt_tokens
            self._total_usage.completion_tokens += usage.completion_tokens
            self._total_usage.total_tokens += usage.total_tokens

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=usage,
            model=response.model,
            finish_reason=choice.finish_reason,
        )

    def _parse_stream_chunk(self, chunk: Any) -> LLMStreamChunk:
        """Parse a streaming chunk."""
        choice = chunk.choices[0] if chunk.choices else None
        delta = choice.delta if choice else None

        text_delta = delta.content if delta and delta.content else ""

        tool_call_delta = None
        if delta and delta.tool_calls:
            tc = delta.tool_calls[0]
            try:
                args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            except json.JSONDecodeError:
                args = {}
            tool_call_delta = ToolCallInfo(
                id=tc.id or "",
                name=tc.function.name or "",
                arguments=args,
            )

        usage = None
        if chunk.usage:
            usage = TokenUsage(
                prompt_tokens=chunk.usage.prompt_tokens,
                completion_tokens=chunk.usage.completion_tokens,
                total_tokens=chunk.usage.total_tokens,
            )

        return LLMStreamChunk(
            delta=text_delta,
            tool_call_delta=tool_call_delta,
            usage=usage,
            finish_reason=choice.finish_reason if choice else None,
        )
