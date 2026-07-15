"""LLM exports."""

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

# LLM alias: use openhands SDK's LLM (Pydantic model) for backward compat
# with wren/app_server/settings/llm_profiles.py and other pydantic-dependent code.
# Our LLMClient is available directly as LLMClient.
from openhands.sdk.llm import LLM  # noqa: F401


class MetricsSnapshot:
    """LLM metrics snapshot."""

    def __init__(self, **kwargs):
        self.total_tokens = kwargs.get("total_tokens", 0)
        self.total_cost = kwargs.get("total_cost", 0.0)
        self.request_count = kwargs.get("request_count", 0)


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
    "MetricsSnapshot",
]
