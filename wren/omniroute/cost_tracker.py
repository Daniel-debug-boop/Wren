"""Cost Tracker — transparent per-request cost analytics.

Tracks every API call with token counts, costs, and provider usage.
Provides real-time cost summaries and alerts. All costs are estimated
based on published pricing; actual charges may vary.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

_logger = logging.getLogger(__name__)


@dataclass
class CostRecord:
    """A single cost record for one API call."""
    provider: str
    model: str
    role: str  # 'planner', 'researcher', 'writer', 'reviewer'
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    timestamp: float = 0.0
    duration_ms: float = 0.0
    success: bool = True


class CostTracker:
    """Tracks costs across all model calls.

    Provides:
    - Per-request cost tracking
    - Per-session cost summaries
    - Per-role cost breakdowns
    - Budget alerts
    - Cost projections
    """

    def __init__(self) -> None:
        self._records: list[CostRecord] = []
        self._session_start = time.time()

        # Per-model pricing (cost per 1K tokens)
        # These are updated as we get real usage data
        self._model_pricing: dict[str, tuple[float, float]] = {
            # model -> (input_cost_per_1k, output_cost_per_1k)
            "gpt-4o": (0.005, 0.015),
            "gpt-4o-mini": (0.00015, 0.0006),
            "gpt-4-turbo": (0.01, 0.03),
            "o1": (0.015, 0.06),
            "o3-mini": (0.0011, 0.0044),
            "claude-sonnet-4-20250514": (0.015, 0.075),
            "claude-3-5-sonnet-v2": (0.003, 0.015),
            "claude-3-5-sonnet": (0.003, 0.015),
            "claude-3-haiku": (0.00025, 0.00125),
            "gemini-2.0-flash": (0.0, 0.0),  # Free
            "gemini-1.5-flash": (0.0, 0.0),  # Free
            "gemini-1.5-pro": (0.0035, 0.0105),
            "deepseek-chat": (0.00027, 0.0011),
            "deepseek-reasoner": (0.00055, 0.00219),
            "mistral-large": (0.002, 0.006),
            "mistral-small": (0.001, 0.003),
        }

        self._budget_alerts: list[dict[str, Any]] = []

    def record_call(
        self,
        provider: str = "",
        model: str = "",
        role: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration_ms: float = 0.0,
        success: bool = True,
    ) -> CostRecord:
        """Record an API call for cost tracking.

        Calculates cost based on model pricing if available.
        Returns the CostRecord for inspection.
        """
        cost = self._calculate_cost(model, input_tokens, output_tokens)

        record = CostRecord(
            provider=provider,
            model=model,
            role=role,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            timestamp=time.time(),
            duration_ms=duration_ms,
            success=success,
        )
        self._records.append(record)

        # Check budget alerts
        if cost > 0.1:
            self._budget_alerts.append({
                "message": f"High cost call: ${cost:.4f} for {model}",
                "cost": cost,
                "model": model,
                "timestamp": record.timestamp,
            })

        return record

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost for a model call."""
        pricing = self._model_pricing.get(model)
        if not pricing:
            return 0.0  # Unknown model — can't estimate

        input_cost, output_cost = pricing
        return (input_tokens / 1000 * input_cost) + (output_tokens / 1000 * output_cost)

    # ═══════════════════════════════════════════════════════════════
    #  SUMMARY REPORTS
    # ═══════════════════════════════════════════════════════════════

    def total_cost(self) -> float:
        """Total accumulated cost."""
        return sum(r.cost_usd for r in self._records)

    def total_tokens(self) -> dict[str, int]:
        """Total token usage across all calls."""
        return {
            "input": sum(r.input_tokens for r in self._records),
            "output": sum(r.output_tokens for r in self._records),
            "total": sum(r.input_tokens + r.output_tokens for r in self._records),
        }

    def total_calls(self) -> int:
        """Total number of API calls."""
        return len(self._records)

    def cost_by_model(self) -> dict[str, float]:
        """Cost broken down by model."""
        breakdown: dict[str, float] = {}
        for r in self._records:
            breakdown[r.model] = breakdown.get(r.model, 0.0) + r.cost_usd
        return breakdown

    def cost_by_role(self) -> dict[str, float]:
        """Cost broken down by agent role."""
        breakdown: dict[str, float] = {}
        for r in self._records:
            breakdown[r.role] = breakdown.get(r.role, 0.0) + r.cost_usd
        return breakdown

    def cost_by_provider(self) -> dict[str, float]:
        """Cost broken down by provider."""
        breakdown: dict[str, float] = {}
        for r in self._records:
            breakdown[r.provider] = breakdown.get(r.provider, 0.0) + r.cost_usd
        return breakdown

    def tokens_by_role(self) -> dict[str, dict[str, int]]:
        """Token usage broken down by role."""
        breakdown: dict[str, dict[str, int]] = {}
        for r in self._records:
            if r.role not in breakdown:
                breakdown[r.role] = {"input": 0, "output": 0, "total": 0}
            breakdown[r.role]["input"] += r.input_tokens
            breakdown[r.role]["output"] += r.output_tokens
            breakdown[r.role]["total"] += r.input_tokens + r.output_tokens
        return breakdown

    def usage_by_model(self, limit: int = 10) -> list[dict[str, Any]]:
        """Most-used models with usage stats."""
        model_stats: dict[str, dict[str, Any]] = {}
        for r in self._records:
            if r.model not in model_stats:
                model_stats[r.model] = {
                    "model": r.model,
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0,
                }
            stats = model_stats[r.model]
            stats["calls"] += 1
            stats["input_tokens"] += r.input_tokens
            stats["output_tokens"] += r.output_tokens
            stats["cost"] += r.cost_usd

        sorted_models = sorted(
            model_stats.values(),
            key=lambda x: x["calls"],
            reverse=True,
        )
        return sorted_models[:limit]

    def session_summary(self) -> dict[str, Any]:
        """Full session cost summary."""
        return {
            "total_cost_usd": round(self.total_cost(), 4),
            "total_calls": self.total_calls(),
            "tokens": self.total_tokens(),
            "avg_cost_per_call": round(self.total_cost() / max(self.total_calls(), 1), 6),
            "session_duration_s": round(time.time() - self._session_start, 1),
            "by_model": self.cost_by_model(),
            "by_role": self.cost_by_role(),
            "by_provider": self.cost_by_provider(),
            "budget_alerts": self._budget_alerts[-10:],  # Last 10 alerts
            "estimated_monthly_projected": round(
                self._project_monthly(), 2
            ),
        }

    def _project_monthly(self) -> float:
        """Project monthly cost based on current usage."""
        elapsed_hours = (time.time() - self._session_start) / 3600
        if elapsed_hours < 0.01:
            return 0.0
        hourly_rate = self.total_cost() / elapsed_hours
        return hourly_rate * 730  # Average hours in a month

    def top_providers_by_tokens(self, limit: int = 5) -> list[dict[str, Any]]:
        """Top providers by token usage."""
        provider_stats: dict[str, dict[str, Any]] = {}
        for r in self._records:
            if r.provider not in provider_stats:
                provider_stats[r.provider] = {
                    "provider": r.provider,
                    "calls": 0,
                    "tokens": 0,
                    "cost": 0.0,
                }
            stats = provider_stats[r.provider]
            stats["calls"] += 1
            stats["tokens"] += r.input_tokens + r.output_tokens
            stats["cost"] += r.cost_usd

        sorted_providers = sorted(
            provider_stats.values(),
            key=lambda x: x["tokens"],
            reverse=True,
        )
        return sorted_providers[:limit]

    def get_budget_alerts(self) -> list[dict[str, Any]]:
        """Get all budget alerts."""
        return list(self._budget_alerts)

    def register_pricing(self, model: str, input_cost: float, output_cost: float) -> None:
        """Register or update pricing for a model."""
        self._model_pricing[model] = (input_cost, output_cost)

    def reset(self) -> None:
        """Reset all tracking data."""
        self._records.clear()
        self._budget_alerts.clear()
        self._session_start = time.time()
