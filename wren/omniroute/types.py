"""Core type definitions for the OmniRoute system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ModelTier(str, Enum):
    """Cost/performance tier for a model."""
    FREE = "free"
    LOW_COST = "low_cost"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class ProviderCategory(str, Enum):
    """Category of AI provider."""
    CHAT = "chat"
    CODING = "coding"
    EMBEDDINGS = "embeddings"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    REASONING = "reasoning"
    SEARCH = "search"
    RERANK = "rerank"


class RoutingStrategy(str, Enum):
    """Available routing strategies for combo steps."""

    PRIORITY = "priority"
    FILL_FIRST = "fill_first"
    WEIGHTED = "weighted"
    ROUND_ROBIN = "round_robin"
    P2C = "p2c"
    LEAST_USED = "least_used"
    RANDOM = "random"
    STRICT_RANDOM = "strict_random"
    COST_OPTIMIZED = "cost_optimized"
    HEADROOM = "headroom"
    RESET_WINDOW = "reset_window"
    RESET_AWARE = "reset_aware"
    CONTEXT_RELAY = "context_relay"
    CONTEXT_OPTIMIZED = "context_optimized"
    LKGP = "lkgp"
    AUTO = "auto"
    FUSION = "fusion"
    PIPELINE = "pipeline"


class ModelCapability(str, Enum):
    """Capabilities a model may support."""
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    STREAMING = "streaming"
    PARALLEL_REQUESTS = "parallel_requests"
    STRUCTURED_OUTPUT = "structured_output"
    PROMPT_CACHING = "prompt_caching"
    REASONING = "reasoning"


@dataclass
class ProviderInfo:
    """Information about an AI provider."""
    name: str
    display_name: str
    base_url: str
    category: ProviderCategory = ProviderCategory.CHAT
    requires_api_key: bool = True
    has_free_tier: bool = False
    is_free_forever: bool = False
    free_tokens_per_month: int = 0
    docs_url: str = ""
    website: str = ""
    api_key_prefix: str = ""  # e.g. "sk-", "sk-ant-"
    models: list[str] = field(default_factory=list)


@dataclass
class ModelInfo:
    """Information about a specific model."""
    name: str
    provider: str
    tier: ModelTier = ModelTier.STANDARD
    is_free: bool = False
    supports_function_calling: bool = True
    supports_vision: bool = False
    supports_streaming: bool = True
    context_window: int = 128_000
    max_output_tokens: int = 4_096
    description: str = ""
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0


@dataclass
class ComboStep:
    """A single step in a routing combo chain."""
    provider: str
    model: str
    strategy: RoutingStrategy = RoutingStrategy.PRIORITY
    weight: float = 1.0
    max_retries: int = 3
    timeout_s: float = 60.0


@dataclass
class ComboDefinition:
    """A complete routing combo definition."""
    name: str
    description: str = ""
    steps: list[ComboStep] = field(default_factory=list)
    fallback_strategy: RoutingStrategy = RoutingStrategy.LKGP
    is_auto_generated: bool = False
    route_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingResult:
    """Result of a routing decision."""
    selected_provider: str
    selected_model: str
    combo_name: str
    estimated_cost_usd: float = 0.0
    fallback_used: bool = False
    fallback_chain: list[str] = field(default_factory=list)
    latency_ms: float = 0.0
    tokens_saved_pct: float = 0.0
    route_strategy: RoutingStrategy = RoutingStrategy.AUTO


@dataclass
class ApiKeyInfo:
    """Information about a detected API key."""
    key_prefix: str
    provider_name: str = ""
    provider_display: str = ""
    models_available: list[str] = field(default_factory=list)
    has_free_tier: bool = False
    is_valid: bool = True
