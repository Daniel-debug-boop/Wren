"""Model Router — API-key-aware model selection and multi-model dispatch.

The ModelRouter knows:
  - Which API keys the user has configured
  - Which models are free vs paid
  - Which model is best for which agent role (planner, researcher, writer, reviewer)

It always prefers free models when available, falling back to paid models
when the task requires it. Supports parallel dispatch to multiple models.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

_logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """Cost tier for a model — free models are preferred."""

    FREE = 'free'
    LOW_COST = 'low_cost'
    STANDARD = 'standard'
    PREMIUM = 'premium'


@dataclass
class ModelInfo:
    """Information about a model: provider, capabilities, and cost."""

    name: str
    provider: str  # e.g. 'openai', 'anthropic', 'google', 'deepseek', 'mistral'
    tier: ModelTier = ModelTier.STANDARD
    supports_function_calling: bool = True
    supports_vision: bool = False
    supports_parallel_requests: bool = True
    max_tokens: int = 128_000
    context_window: int = 128_000
    is_free: bool = False
    description: str = ''


@dataclass
class AgentRoleConfig:
    """Config for which model an agent role should use."""

    role: str  # 'planner', 'researcher', 'writer', 'reviewer'
    preferred_model: str = ''
    fallback_model: str = ''
    requires_premium: bool = False
    max_cost_per_task_usd: float = 0.0  # 0 = unlimited
    parallel_calls: int = 1  # How many parallel model calls to make


@dataclass
class ModelSelectionResult:
    """Result of a model selection — which model(s) to use."""

    primary_model: ModelInfo
    fallback_models: list[ModelInfo] = field(default_factory=list)
    estimated_cost_usd: float = 0.0
    parallel_calls: int = 1
    all_models_queried: list[str] = field(default_factory=list)


class ModelRegistry:
    """Registry of all available models with their capabilities and costs.

    Pre-populated with well-known models. Users can add custom models.
    """

    def __init__(self) -> None:
        self._models: dict[str, ModelInfo] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register well-known models with their tiers and capabilities."""
        defaults: list[ModelInfo] = [
            # ── FREE models ──────────────────────────────────
            ModelInfo(
                name='gemini-1.5-flash',
                provider='google',
                tier=ModelTier.FREE,
                is_free=True,
                supports_vision=True,
                context_window=1_000_000,
                description='Fast, free Gemini Flash — great for research/parsing',
            ),
            ModelInfo(
                name='gemini-2.0-flash',
                provider='google',
                tier=ModelTier.FREE,
                is_free=True,
                supports_vision=True,
                context_window=1_000_000,
                description='Latest free Gemini Flash — best for research',
            ),
            ModelInfo(
                name='llama-3.1-8b',
                provider='meta',
                tier=ModelTier.FREE,
                is_free=True,
                supports_function_calling=False,
                context_window=128_000,
                description='Free 8B model via Ollama/Groq',
            ),
            ModelInfo(
                name='deepseek-chat',
                provider='deepseek',
                tier=ModelTier.LOW_COST,
                is_free=False,
                context_window=128_000,
                description='DeepSeek V3 — excellent low-cost coder',
            ),
            # ── LOW-COST models ──────────────────────────────
            ModelInfo(
                name='claude-3-haiku',
                provider='anthropic',
                tier=ModelTier.LOW_COST,
                supports_vision=True,
                context_window=200_000,
                description='Fast Anthropic model — good for quick reviews',
            ),
            ModelInfo(
                name='gpt-4o-mini',
                provider='openai',
                tier=ModelTier.LOW_COST,
                supports_vision=True,
                context_window=128_000,
                description='Low-cost OpenAI — good for reviews & planning',
            ),
            ModelInfo(
                name='mistral-small',
                provider='mistral',
                tier=ModelTier.LOW_COST,
                context_window=128_000,
                description='Mistral Small — fast & cheap',
            ),
            # ── STANDARD models ──────────────────────────────
            ModelInfo(
                name='gpt-4o',
                provider='openai',
                tier=ModelTier.STANDARD,
                supports_vision=True,
                description='Standard OpenAI — good for most tasks',
            ),
            ModelInfo(
                name='claude-3-5-sonnet',
                provider='anthropic',
                tier=ModelTier.STANDARD,
                supports_vision=True,
                context_window=200_000,
                description='Claude Sonnet — balanced quality & speed',
            ),
            ModelInfo(
                name='deepseek-r1',
                provider='deepseek',
                tier=ModelTier.LOW_COST,
                context_window=128_000,
                description='DeepSeek R1 — reasoning-focused',
            ),
            # ── PREMIUM models ───────────────────────────────
            ModelInfo(
                name='claude-3-5-sonnet-v2',
                provider='anthropic',
                tier=ModelTier.PREMIUM,
                supports_vision=True,
                context_window=200_000,
                description='Claude Sonnet v2 — best for planning & writing',
            ),
            ModelInfo(
                name='gpt-4-turbo',
                provider='openai',
                tier=ModelTier.PREMIUM,
                supports_vision=True,
                description='Premium OpenAI — best for complex coding',
            ),
            ModelInfo(
                name='gemini-1.5-pro',
                provider='google',
                tier=ModelTier.PREMIUM,
                supports_vision=True,
                context_window=1_000_000,
                description='Premium Gemini — large context & vision',
            ),
        ]
        for m in defaults:
            self._models[m.name] = m

    def register(self, model: ModelInfo) -> None:
        """Register a custom model."""
        self._models[model.name] = model

    def get(self, name: str) -> ModelInfo | None:
        """Look up a model by name."""
        return self._models.get(name)

    def list_by_tier(self, tier: ModelTier) -> list[ModelInfo]:
        """List all models at a given tier."""
        return [m for m in self._models.values() if m.tier == tier]

    def list_free(self) -> list[ModelInfo]:
        """List all free models."""
        return [m for m in self._models.values() if m.is_free]

    def list_supporting(self, capability: str) -> list[ModelInfo]:
        """List models supporting a capability (vision, function_calling)."""
        if capability == 'vision':
            return [m for m in self._models.values() if m.supports_vision]
        if capability == 'function_calling':
            return [m for m in self._models.values() if m.supports_function_calling]
        return []

    def all(self) -> list[ModelInfo]:
        return list(self._models.values())


class ModelRouter:
    """Routes tasks to the best available model based on user API keys.

    Priority:
      1. Free models (if user has their API key)
      2. Low-cost models
      3. Standard models
      4. Premium models (only if task requires it)

    Supports parallel dispatch to multiple models for a single task.
    Includes per-session cost tracking with token counters.
    """

    def __init__(self, registry: ModelRegistry | None = None) -> None:
        self._registry = registry or ModelRegistry()
        self._user_api_keys: dict[str, str] = {}  # provider -> api_key

        # ── Cost tracking ───────────────────────────────────────
        self._total_input_tokens: int = 0
        self._total_output_tokens: int = 0
        self._total_api_calls: int = 0
        self._total_cost_usd: float = 0.0
        self._cost_by_model: dict[str, float] = {}  # model_name -> cost_usd
        self._cost_by_role: dict[str, float] = {}  # role -> cost_usd

    def configure_api_keys(self, api_keys: dict[str, str]) -> None:
        """Register user API keys. Key = provider name, value = API key."""
        self._user_api_keys.update(api_keys)
        _logger.debug(
            'ModelRouter: configured %d API keys: %s',
            len(api_keys),
            list(api_keys.keys()),
        )

    def has_key_for(self, provider: str) -> bool:
        """Check if the user has an API key for a provider."""
        return provider in self._user_api_keys

    def select_for_role(
        self,
        role: str,
        task_description: str = '',
        require_vision: bool = False,
        allow_premium: bool = False,
        force_model: str | None = None,
    ) -> ModelSelectionResult:
        """Select the best model(s) for a given agent role.

        Args:
            role: Agent role ('planner', 'researcher', 'writer', 'reviewer')
            task_description: Description of the task (for context)
            require_vision: Whether the task needs vision capabilities
            allow_premium: Whether premium models are acceptable
            force_model: Force a specific model (bypass selection)

        Returns:
            ModelSelectionResult with primary and fallback models
        """
        if force_model:
            model = self._registry.get(force_model)
            if model:
                return ModelSelectionResult(
                    primary_model=model,
                    estimated_cost_usd=self._estimate_cost(model, role),
                    parallel_calls=1,
                    all_models_queried=[force_model],
                )

        # Determine which tiers to consider based on role
        if role == 'researcher':
            # Researchers use free/low-cost models for fast parsing
            tiers = [ModelTier.FREE, ModelTier.LOW_COST]
        elif role == 'reviewer':
            # Reviewers use low-cost models for quick checks
            tiers = [ModelTier.LOW_COST, ModelTier.FREE, ModelTier.STANDARD]
        elif role == 'writer':
            # Writers use standard+ for quality code generation
            tiers = [ModelTier.STANDARD, ModelTier.LOW_COST, ModelTier.PREMIUM]
        elif role == 'planner':
            # Planners need good reasoning
            tiers = [ModelTier.STANDARD, ModelTier.PREMIUM, ModelTier.LOW_COST]
        else:
            tiers = [ModelTier.STANDARD, ModelTier.LOW_COST, ModelTier.PREMIUM]

        if not allow_premium:
            tiers = [t for t in tiers if t != ModelTier.PREMIUM]

        # Find the best model that the user has API key for
        candidates: list[ModelInfo] = []
        for tier in tiers:
            tier_models = self._registry.list_by_tier(tier)
            for model in tier_models:
                if require_vision and not model.supports_vision:
                    continue
                if not self.has_key_for(model.provider):
                    continue
                candidates.append(model)
            if candidates:
                # Take the best model from this tier
                primary = candidates[0]
                fallbacks = candidates[1:3]  # 2 fallbacks
                return ModelSelectionResult(
                    primary_model=primary,
                    fallback_models=fallbacks,
                    estimated_cost_usd=self._estimate_cost(primary, role),
                    parallel_calls=min(3, len(candidates)),
                    all_models_queried=[m.name for m in candidates],
                )

        # No model found with user's keys — return a reasonable default
        default = self._registry.get('gpt-4o-mini') or self._registry.all()[0]
        _logger.warning(
            'No model found for role=%s with user keys; defaulting to %s',
            role,
            default.name,
        )
        return ModelSelectionResult(
            primary_model=default,
            estimated_cost_usd=0.0,
            parallel_calls=1,
            all_models_queried=[],
        )

    def select_parallel(
        self,
        model_names: list[str],
        task_description: str = '',
    ) -> list[ModelSelectionResult]:
        """Select multiple models for parallel execution.

        Returns a ModelSelectionResult for each model name.
        """
        results = []
        for name in model_names:
            model = self._registry.get(name)
            if model:
                results.append(
                    ModelSelectionResult(
                        primary_model=model,
                        parallel_calls=1,
                        all_models_queried=[name],
                    )
                )
        return results

    def rank_by_cost(
        self, model_names: list[str]
    ) -> list[tuple[ModelInfo, float]]:
        """Rank models by estimated cost (cheapest first)."""
        tier_cost = {
            ModelTier.FREE: 0.0,
            ModelTier.LOW_COST: 0.5,
            ModelTier.STANDARD: 1.0,
            ModelTier.PREMIUM: 3.0,
        }
        scored: list[tuple[ModelInfo, float]] = []
        for name in model_names:
            model = self._registry.get(name)
            if model:
                scored.append((model, tier_cost.get(model.tier, 1.0)))
        scored.sort(key=lambda x: x[1])
        return scored

    @staticmethod
    def _estimate_cost(model: ModelInfo, role: str) -> float:
        """Rough cost estimate for one task with this model."""
        base_costs = {
            'planner': 0.005,
            'researcher': 0.002,
            'writer': 0.02,
            'reviewer': 0.003,
        }
        cost = base_costs.get(role, 0.01)
        tier_multipliers = {
            ModelTier.FREE: 0.0,
            ModelTier.LOW_COST: 0.5,
            ModelTier.STANDARD: 1.0,
            ModelTier.PREMIUM: 2.5,
        }
        return cost * tier_multipliers.get(model.tier, 1.0)

    # ── Cost tracking ──────────────────────────────────────────────

    def record_call(
        self,
        model_name: str,
        role: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """Record an API call for cost and usage tracking.

        Should be called after every model invocation so the session
        accumulates accurate cost data.

        Args:
            model_name: The model that was called (e.g. 'gpt-4o')
            role: The agent role that made the call (e.g. 'planner', 'writer')
            input_tokens: Number of input tokens consumed
            output_tokens: Number of output tokens produced
        """
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        self._total_api_calls += 1

        # Estimate cost based on model tier
        model = self._registry.get(model_name)
        if model:
            cost = self._estimate_cost(model, role)
            self._total_cost_usd += cost
            self._cost_by_model[model_name] = (
                self._cost_by_model.get(model_name, 0.0) + cost
            )
            self._cost_by_role[role] = self._cost_by_role.get(role, 0.0) + cost

    @property
    def total_cost_usd(self) -> float:
        return round(self._total_cost_usd, 4)

    @property
    def total_api_calls(self) -> int:
        return self._total_api_calls

    @property
    def total_tokens(self) -> dict[str, int]:
        return {
            'input': self._total_input_tokens,
            'output': self._total_output_tokens,
            'total': self._total_input_tokens + self._total_output_tokens,
        }

    def cost_summary(self) -> dict[str, object]:
        """Full cost and usage summary for the current session."""
        return {
            'total_input_tokens': self._total_input_tokens,
            'total_output_tokens': self._total_output_tokens,
            'total_api_calls': self._total_api_calls,
            'estimated_cost_usd': self.total_cost_usd,
            'by_model': dict(self._cost_by_model),
            'by_role': dict(self._cost_by_role),
        }

    @property
    def registry(self) -> ModelRegistry:
        return self._registry
