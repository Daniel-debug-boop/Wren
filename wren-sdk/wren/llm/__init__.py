"""LLM exports."""

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

class LLM(WrenModel):
    """LLM configuration model (native replacement for openhands.sdk.llm.LLM)."""

    model: str = "gpt-4o"
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    max_retries: int = 2
    timeout: float = 60.0


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
