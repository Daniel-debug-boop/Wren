"""LLM exports."""

from __future__ import annotations

from typing import Any

from pydantic import SecretStr, field_serializer, field_validator

from wren.utils.models import WrenModel
from wren.llm.message import (
    Message,
    MessageRole,
    ContentType,
    TextContent,
    ImageContent,
    ImageSource,
    ToolUseContent,
    ToolResultContent,
    ThinkingContent,
    ContentBlock,
)
from wren.llm.client import (
    LLMClient,
    LLMConfig,
    LLMResponse,
    TokenUsage,
    LLMStreamChunk,
    ToolCallInfo,
)

# Canonical masked placeholder. Matches pydantic's ``SecretStr`` default
# representation (``'**********'``) so payloads that pass through
# ``model_dump(mode='json')`` round-trip to ``None`` instead of
# materializing a fake key on the receiving side.
MASKED_API_KEY_PLACEHOLDER = "**********"


class LLM(WrenModel):
    """LLM configuration model (native replacement for openhands.sdk.llm.LLM)."""

    model: str = "gpt-4o"
    api_key: SecretStr | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    max_retries: int = 2
    timeout: float = 60.0
    usage_id: str | None = None
    litellm_extra_body: dict[str, Any] | None = None
    reasoning_effort: str | None = "high"
    extended_thinking_budget: int | None = None
    drop_params: bool | None = None

    model_config = WrenModel.model_config.copy()  # type: ignore[has-type]

    @field_validator("api_key", mode="before")
    @classmethod
    def _strip_masked_api_key(cls, value: Any) -> Any:
        if value == MASKED_API_KEY_PLACEHOLDER:
            return None
        return value

    @property
    def is_subscription(self) -> bool:
        """Whether this LLM config uses a subscription-based API key.

        Always False in the self-hosted / OSS context. The SaaS SDK
        overrides this to track subscription-tier credentials.
        """
        return False

    @field_serializer("api_key")
    def _serialize_api_key(self, api_key: SecretStr | None, info) -> str | None:
        if api_key is None:
            return None
        context = info.context or {}
        if context.get("expose_secrets", False):
            return api_key.get_secret_value()
        return str(api_key)


class Metrics(WrenModel):
    """Accumulated metrics for a single LLM role (agent/condenser)."""

    model_name: str | None = None
    accumulated_cost: float = 0.0
    max_budget_per_task: float | None = None
    accumulated_token_usage: TokenUsage | None = None


class MetricsSnapshot(WrenModel):
    """LLM metrics snapshot."""

    total_tokens: int = 0
    total_cost: float = 0.0
    request_count: int = 0
    accumulated_token_usage: TokenUsage | None = None
    accumulated_cost: float = 0.0
    max_budget_per_task: float | None = None


__all__ = [
    "Message",
    "MessageRole",
    "ContentType",
    "TextContent",
    "ImageContent",
    "ImageSource",
    "ToolUseContent",
    "ToolResultContent",
    "ThinkingContent",
    "ContentBlock",
    "LLMClient",
    "LLMConfig",
    "LLMResponse",
    "TokenUsage",
    "LLMStreamChunk",
    "ToolCallInfo",
    "LLM",
    "Metrics",
    "MetricsSnapshot",
]
