"""LLM message types for Wren SDK.

Defines the message format for LLM communication.
Compatible with OpenAI/Anthropic message formats.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional, Union

from wren.utils.models import WrenModel


class MessageRole(str, Enum):
    """Message role in conversation."""

    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'
    TOOL = 'tool'


class ContentType(str, Enum):
    """Content block type."""

    TEXT = 'text'
    IMAGE = 'image'
    TOOL_USE = 'tool_use'
    TOOL_RESULT = 'tool_result'
    THINKING = 'thinking'


class TextContent(WrenModel):
    """Text content block."""

    type: ContentType = ContentType.TEXT
    text: str


class ImageSource(WrenModel):
    """Image source (URL or base64)."""

    type: str  # "url" or "base64"
    url: str | None = None
    media_type: str | None = None  # "image/png", "image/jpeg", etc.
    data: str | None = None  # base64 encoded


class ImageContent(WrenModel):
    """Image content block."""

    type: ContentType = ContentType.IMAGE
    source: ImageSource


class ToolUseContent(WrenModel):
    """Tool use content block (assistant requesting tool call)."""

    type: ContentType = ContentType.TOOL_USE
    id: str
    name: str
    input: dict[str, Any]


class ToolResultContent(WrenModel):
    """Tool result content block (tool response)."""

    type: ContentType = ContentType.TOOL_RESULT
    tool_use_id: str
    content: str
    is_error: bool = False


class ThinkingContent(WrenModel):
    """Thinking/reasoning content block."""

    type: ContentType = ContentType.THINKING
    thinking: str


# Content block types
ContentBlock = Union[
    TextContent,
    ImageContent,
    ToolUseContent,
    ToolResultContent,
    ThinkingContent,
]


class Message(WrenModel):
    """A message in the conversation.

    Compatible with OpenAI and Anthropic message formats.
    """

    role: MessageRole
    content: str | list[ContentBlock]
    name: str | None = None
    tool_call_id: str | None = None

    def to_prompt(self) -> str:
        """Convert to simple prompt string."""
        if isinstance(self.content, str):
            return f'[{self.role.value}]: {self.content}'

        parts = []
        for block in self.content:
            if isinstance(block, TextContent):
                parts.append(block.text)
            elif isinstance(block, ToolUseContent):
                args = ', '.join(f'{k}={v!r}' for k, v in block.input.items())
                parts.append(f'[tool_use: {block.name}({args})]')
            elif isinstance(block, ToolResultContent):
                parts.append(f'[tool_result]: {block.content}')
            elif isinstance(block, ThinkingContent):
                parts.append(f'[thinking]: {block.thinking}')

        return f'[{self.role.value}]: {" ".join(parts)}'

    def to_openai(self) -> dict[str, Any]:
        """Convert to OpenAI message format."""
        msg: dict[str, Any] = {'role': self.role.value}

        if isinstance(self.content, str):
            msg['content'] = self.content
        else:
            # Convert content blocks
            content = []
            for block in self.content:
                if isinstance(block, TextContent):
                    content.append({'type': 'text', 'text': block.text})
                elif isinstance(block, ImageContent):
                    content.append(
                        {
                            'type': 'image_url',
                            'image_url': {'url': block.source.url},
                        }
                    )
                elif isinstance(block, ToolUseContent):
                    content.append(
                        {
                            'type': 'function',
                            'function': {
                                'name': block.name,
                                'arguments': block.input,
                            },
                        }
                    )
            msg['content'] = content

        if self.name:
            msg['name'] = self.name
        if self.tool_call_id:
            msg['tool_call_id'] = self.tool_call_id

        return msg

    def to_anthropic(self) -> dict[str, Any]:
        """Convert to Anthropic message format."""
        msg: dict[str, Any] = {'role': self.role.value}

        if isinstance(self.content, str):
            msg['content'] = self.content
        else:
            content = []
            for block in self.content:
                if isinstance(block, TextContent):
                    content.append({'type': 'text', 'text': block.text})
                elif isinstance(block, ImageContent):
                    content.append(
                        {
                            'type': 'image',
                            'source': block.source.to_dict(),
                        }
                    )
                elif isinstance(block, ToolUseContent):
                    content.append(
                        {
                            'type': 'tool_use',
                            'id': block.id,
                            'name': block.name,
                            'input': block.input,
                        }
                    )
                elif isinstance(block, ToolResultContent):
                    content.append(
                        {
                            'type': 'tool_result',
                            'tool_use_id': block.tool_use_id,
                            'content': block.content,
                        }
                    )
            msg['content'] = content

        return msg

    @classmethod
    def user(cls, content: str) -> Message:
        """Create a user message."""
        return cls(role=MessageRole.USER, content=content)

    @classmethod
    def assistant(cls, content: str) -> Message:
        """Create an assistant message."""
        return cls(role=MessageRole.ASSISTANT, content=content)

    @classmethod
    def system(cls, content: str) -> Message:
        """Create a system message."""
        return cls(role=MessageRole.SYSTEM, content=content)

    @classmethod
    def tool_result(
        cls, tool_call_id: str, content: str, is_error: bool = False
    ) -> Message:
        """Create a tool result message."""
        return cls(
            role=MessageRole.TOOL,
            content=[
                ToolResultContent(
                    tool_use_id=tool_call_id,
                    content=content,
                    is_error=is_error,
                )
            ],
            tool_call_id=tool_call_id,
        )
