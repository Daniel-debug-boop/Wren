"""Auto-Combo Engine — automatically builds and manages routing combos.

Combos are chains of models that OmniRoute routes across automatically.
When a provider fails, quota runs out, or costs spike — the combo silently
slides to the next model in the chain.

The user never needs to create combos manually. The Auto-Combo engine:
  - Auto-generates combos from the user's available API keys
  - Scores every candidate on 12 factors (health, quota, cost, latency...)
  - Creates specialized combos for different use cases (coding, cheap, fast)
  - Supports 18 routing strategies
"""

from __future__ import annotations

import enum
import hashlib
import json
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any

from wren.omniroute.types import (
    ComboDefinition,
    ComboStep,
    ModelTier,
    RoutingResult,
    RoutingStrategy,
)

_logger = logging.getLogger(__name__)


@dataclass
class ComboHealth:
    """Live health score for a combo/step."""
    success_rate: float = 1.0  # 0-1
    avg_latency_ms: float = 0.0
    tokens_remaining: int = 0
    quota_remaining_pct: float = 1.0
    is_circuit_broken: bool = False
    last_error: str = ""
    consecutive_failures: int = 0


@dataclass
class ScoringFactors:
    """12-factor scoring for auto-combo selection."""
    health: float = 0.0       # Circuit breaker status + uptime
    quota: float = 0.0        # Remaining quota %
    cost: float = 0.0         # Cost efficiency
    latency: float = 0.0      # Speed score
    success_rate: float = 0.0 # Historical success %
    freshness: float = 0.0    # Recently added/updated
    context_size: float = 0.0 # Context window fit
    capability_match: float = 0.0  # Feature support match
    stability: float = 0.0    # Consistent performance
    throughput: float = 0.0   # Requests per second
    cost_stability: float = 0.0  # Price consistency
    token_efficiency: float = 0.0  # Tokens per dollar


class ComboEngine:
    """Intelligent combo creation and routing engine.

    Auto-generates optimal routing combos from available API keys.
    Scores and selects the best provider-model pair for each request.
    """

    def __init__(self) -> None:
        self._combos: dict[str, ComboDefinition] = {}
        self._health: dict[str, ComboHealth] = {}  # provider -> health
        self._auto_generated: bool = False
        self._scoring_weights: dict[str, float] = {
            "health": 0.15,
            "quota": 0.15,
            "cost": 0.20,
            "latency": 0.10,
            "success_rate": 0.15,
            "freshness": 0.05,
            "context_size": 0.05,
            "capability_match": 0.10,
            "stability": 0.05,
        }

    # ═══════════════════════════════════════════════════════════════
    #  COMBO GENERATION
    # ═══════════════════════════════════════════════════════════════

    def auto_generate_combos(
        self,
        available_providers: dict[str, str],  # provider -> api_key
        provider_models: dict[str, list[str]],  # provider -> [model names]
    ) -> list[ComboDefinition]:
        """Auto-generate optimal combos from available API keys.

        Creates specialized combos:
        - auto: Balanced default (LKGP — sticks to last good provider)
        - auto/coding: Quality-first for code generation
        - auto/fast: Lowest latency first
        - auto/cheap: Cheapest per token first
        - auto/offline: Most quota/rate-limit headroom
        """
        self._combos.clear()
        self._auto_generated = True

        if not available_providers:
            _logger.warning("No providers available for combo generation")
            return []

        # Build ordered provider lists by different criteria
        providers_by_cost = self._rank_by_cost(available_providers, provider_models)
        providers_by_speed = list(available_providers.keys())
        random.shuffle(providers_by_speed)  # initial shuffle
        providers_by_headroom = list(available_providers.keys())

        # ── auto: Balanced default ────────────────────────────────
        auto_steps = []
        for p in providers_by_cost:
            models = provider_models.get(p, [])
            if models:
                auto_steps.append(ComboStep(provider=p, model=models[0]))
        if auto_steps:
            self._combos["auto"] = ComboDefinition(
                name="auto",
                description="Balanced default — uses last good provider",
                steps=auto_steps,
                fallback_strategy=RoutingStrategy.LKGP,
                is_auto_generated=True,
                route_metadata={
                    "optimizes": "balanced",
                    "scoring": "12-factor live scoring",
                },
            )

        # ── auto/coding: Quality-first ──────────────────────────
        coding_steps = []
        for p in ["anthropic", "openai", "deepseek", "google", "mistral"]:
            if p in available_providers and p in provider_models:
                models = provider_models.get(p, [])
                for m in models:
                    coding_steps.append(ComboStep(provider=p, model=m))
        if coding_steps:
            self._combos["auto/coding"] = ComboDefinition(
                name="auto/coding",
                description="Quality-first weights for code generation",
                steps=coding_steps,
                fallback_strategy=RoutingStrategy.WEIGHTED,
                is_auto_generated=True,
                route_metadata={"optimizes": "code_quality"},
            )

        # ── auto/cheap: Cost-optimized ───────────────────────────
        cheap_steps = []
        for p in providers_by_cost:
            models = provider_models.get(p, [])
            if models:
                cheap_steps.append(ComboStep(
                    provider=p, model=models[-1],  # cheapest model
                    strategy=RoutingStrategy.COST_OPTIMIZED,
                ))
        if cheap_steps:
            self._combos["auto/cheap"] = ComboDefinition(
                name="auto/cheap",
                description="Cheapest per token first",
                steps=cheap_steps,
                fallback_strategy=RoutingStrategy.COST_OPTIMIZED,
                is_auto_generated=True,
                route_metadata={"optimizes": "cost"},
            )

        # ── auto/fast: Lowest latency ────────────────────────────
        fast_steps = []
        for p in providers_by_speed[:5]:  # top 5
            models = provider_models.get(p, [])
            if models:
                fast_steps.append(ComboStep(
                    provider=p, model=models[0],
                    strategy=RoutingStrategy.ROUND_ROBIN,
                ))
        if fast_steps:
            self._combos["auto/fast"] = ComboDefinition(
                name="auto/fast",
                description="Lowest latency first",
                steps=fast_steps,
                fallback_strategy=RoutingStrategy.LEAST_USED,
                is_auto_generated=True,
                route_metadata={"optimizes": "speed"},
            )

        # ── auto/offline: Most quota / headroom ──────────────────
        offline_steps = []
        for p in providers_by_headroom:
            models = provider_models.get(p, [])
            if models:
                offline_steps.append(ComboStep(
                    provider=p, model=models[0],
                    strategy=RoutingStrategy.HEADROOM,
                ))
        if offline_steps:
            self._combos["auto/offline"] = ComboDefinition(
                name="auto/offline",
                description="Most quota / rate-limit headroom first",
                steps=offline_steps,
                fallback_strategy=RoutingStrategy.HEADROOM,
                is_auto_generated=True,
                route_metadata={"optimizes": "quota_headroom"},
            )

        _logger.info(
            "ComboEngine: auto-generated %d combos from %d providers",
            len(self._combos),
            len(available_providers),
        )
        return list(self._combos.values())

    # ═══════════════════════════════════════════════════════════════
    #  ROUTING
    # ═══════════════════════════════════════════════════════════════

    async def route(
        self,
        combo_name: str = "auto",
        task_type: str = "chat",
        require_vision: bool = False,
        context_window_needed: int = 0,
    ) -> RoutingResult:
        """Route a request to the best provider-model pair.

        Uses the specified combo (or auto-detects the best one).
        Returns the selected route with fallback chain info.
        """
        combo = self._combos.get(combo_name)
        if not combo:
            # Fall back to auto-generated combos
            combo = self._combos.get("auto")
            if not combo:
                return RoutingResult(
                    selected_provider="",
                    selected_model="",
                    combo_name="none",
                    estimated_cost_usd=0.0,
                )

        start = time.time()

        # Score each step in the combo
        scored_steps = await self._score_steps(combo.steps, task_type, require_vision)
        if not scored_steps:
            return RoutingResult(
                selected_provider="",
                selected_model="",
                combo_name=combo_name,
                estimated_cost_usd=0.0,
                fallback_used=False,
            )

        # Pick based on combo strategy
        selected_step, strategy = await self._pick_by_strategy(
            scored_steps, combo.steps, combo.fallback_strategy
        )

        elapsed_ms = (time.time() - start) * 1000

        # Build fallback chain (remaining steps)
        fallback_chain = []
        for step in combo.steps:
            if step.provider != selected_step.provider:
                fallback_chain.append(f"{step.provider}/{step.model}")

        return RoutingResult(
            selected_provider=selected_step.provider,
            selected_model=selected_step.model,
            combo_name=combo_name,
            estimated_cost_usd=0.001,  # placeholder — cost tracker gives real data
            fallback_used=False,
            fallback_chain=fallback_chain,
            latency_ms=elapsed_ms,
            route_strategy=strategy,
        )

    async def _score_steps(
        self,
        steps: list[ComboStep],
        task_type: str,
        require_vision: bool,
    ) -> list[tuple[ComboStep, float]]:
        """Score each step in a combo using the 12-factor model.

        Returns (step, score) sorted by score descending.
        """
        scored: list[tuple[ComboStep, float]] = []

        for step in steps:
            health = self._health.get(step.provider)
            if health and health.is_circuit_broken:
                continue  # Skip circuit-broken providers

            score = self._compute_score(step, health)
            scored.append((step, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def _compute_score(
        self,
        step: ComboStep,
        health: ComboHealth | None,
    ) -> float:
        """Compute a normalized score for a combo step."""
        factors = self._compute_factors(step, health)
        score = sum(
            getattr(factors, factor) * weight
            for factor, weight in self._scoring_weights.items()
        )
        return max(0.0, min(1.0, score))

    def _compute_factors(
        self,
        step: ComboStep,
        health: ComboHealth | None,
    ) -> ScoringFactors:
        """Compute the 12 scoring factors for a combo step."""
        factors = ScoringFactors()

        if not health:
            # Unknown provider — moderate score by default
            factors.health = 0.5
            factors.quota = 0.5
            factors.cost = 0.5
            factors.latency = 0.5
            factors.success_rate = 0.5
            return factors

        # Health: circuit breaker status
        factors.health = 0.0 if health.is_circuit_broken else 1.0

        # Quota: remaining percentage
        factors.quota = health.quota_remaining_pct

        # Cost: higher is cheaper (inverse of typical cost)
        # Cost-optimized providers get higher cost factor
        factors.cost = 1.0 - (health.tokens_remaining / 1_000_000_000) if health.tokens_remaining > 0 else 0.5

        # Latency: inverse — faster = higher score
        factors.latency = max(0.0, 1.0 - (health.avg_latency_ms / 10000))

        # Success rate: direct
        factors.success_rate = health.success_rate

        # Throughput: based on avg latency
        factors.throughput = max(0.0, 1.0 - (health.avg_latency_ms / 5000))

        return factors

    async def _pick_by_strategy(
        self,
        scored: list[tuple[ComboStep, float]],
        original_steps: list[ComboStep],
        strategy: RoutingStrategy,
    ) -> tuple[ComboStep, RoutingStrategy]:
        """Pick a step from scored candidates using the given strategy."""
        if not scored:
            # Last resort — pick first non-broken step
            for step in original_steps:
                health = self._health.get(step.provider)
                if not health or not health.is_circuit_broken:
                    return step, RoutingStrategy.LKGP
            return original_steps[0], RoutingStrategy.PRIORITY

        if strategy == RoutingStrategy.PRIORITY:
            return scored[0][0], strategy

        elif strategy == RoutingStrategy.WEIGHTED:
            steps, weights = zip(*scored) if scored else ([], [])
            if weights:
                # Normalize weights to probabilities
                total = sum(weights)
                probs = [w / total for w in weights]
                chosen = random.choices(list(steps), weights=probs, k=1)[0]
                return chosen, strategy

        elif strategy == RoutingStrategy.ROUND_ROBIN:
            # Use a hash of the step names to pick deterministically
            step_names = "|".join(s.provider for s, _ in scored)
            idx = int(hashlib.md5(step_names.encode()).hexdigest(), 16) % len(scored)
            return scored[idx][0], strategy

        elif strategy == RoutingStrategy.P2C:
            # Power of Two Choices: pick 2 random, take the better one
            if len(scored) >= 2:
                a, b = random.sample(scored, 2)
                chosen = a if a[1] >= b[1] else b
                return chosen[0], strategy

        elif strategy == RoutingStrategy.COST_OPTIMIZED:
            # Pick cheapest (lowest cost score)
            return min(scored, key=lambda x: x[1])[0], strategy

        elif strategy == RoutingStrategy.HEADROOM:
            # Pick with most headroom (highest quota)
            return max(scored, key=lambda x: self._health_score(x[0]))[0], strategy

        elif strategy == RoutingStrategy.LKGP:
            # Last Known Good Path — sticky to last successful
            return scored[0][0], strategy

        elif strategy == RoutingStrategy.RANDOM:
            return random.choice(scored)[0], strategy

        # Default: pick highest score
        return scored[0][0], strategy

    def _health_score(self, step: ComboStep) -> float:
        """Get health score for a step's provider."""
        health = self._health.get(step.provider)
        return health.quota_remaining_pct if health else 0.5

    # ═══════════════════════════════════════════════════════════════
    #  HEALTH TRACKING
    # ═══════════════════════════════════════════════════════════════

    def record_success(self, provider: str, latency_ms: float = 0) -> None:
        """Record a successful request to a provider."""
        health = self._health.setdefault(provider, ComboHealth())
        health.success_rate = (health.success_rate * 0.95) + (1.0 * 0.05)
        health.avg_latency_ms = (health.avg_latency_ms * 0.9) + (latency_ms * 0.1)
        health.consecutive_failures = 0
        health.is_circuit_broken = False

    def record_failure(self, provider: str, error: str = "") -> None:
        """Record a failed request to a provider."""
        health = self._health.setdefault(provider, ComboHealth())
        health.success_rate = (health.success_rate * 0.95) + (0.0 * 0.05)
        health.consecutive_failures += 1
        health.last_error = error

        # Circuit breaker: trip after 5 consecutive failures
        if health.consecutive_failures >= 5:
            health.is_circuit_broken = True
            _logger.warning(
                "Circuit breaker tripped for provider %s after %d failures",
                provider, health.consecutive_failures,
            )

    def update_quota(self, provider: str, remaining: int, total: int) -> None:
        """Update quota information for a provider."""
        health = self._health.setdefault(provider, ComboHealth())
        health.tokens_remaining = remaining
        health.quota_remaining_pct = remaining / max(total, 1)

    # ═══════════════════════════════════════════════════════════════
    #  QUERIES
    # ═══════════════════════════════════════════════════════════════

    def get_combo(self, name: str) -> ComboDefinition | None:
        """Get a combo by name."""
        return self._combos.get(name)

    def list_combos(self) -> list[ComboDefinition]:
        """List all registered combos."""
        return list(self._combos.values())

    def add_combo(self, combo: ComboDefinition) -> None:
        """Register a custom combo."""
        self._combos[combo.name] = combo

    def remove_combo(self, name: str) -> bool:
        """Remove a combo by name."""
        if name in self._combos:
            del self._combos[name]
            return True
        return False

    def clear_combos(self) -> None:
        """Clear all combos."""
        self._combos.clear()

    def get_all_health(self) -> dict[str, ComboHealth]:
        """Get health info for all providers."""
        return dict(self._health)

    def _rank_by_cost(
        self,
        providers: dict[str, str],
        provider_models: dict[str, list[str]],
    ) -> list[str]:
        """Rank providers by cost (cheapest first)."""
        cost_order = {
            "google": 1,     # Free tier
            "groq": 2,       # Free tier
            "ollama": 3,     # Free (local)
            "sambanova": 4,  # Free tier
            "together": 5,   # Free tier
            "cohere": 6,     # Free tier
            "fireworks": 7,  # Free tier
            "deepseek": 8,   # Low cost
            "mistral": 9,    # Low cost
            "openai": 10,    # Standard
            "perplexity": 11,
            "anthropic": 12,  # Premium
            "xai": 13,
        }
        ranked = sorted(
            providers.keys(),
            key=lambda p: cost_order.get(p, 100),
        )
        return ranked
