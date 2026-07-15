"""Context budget — token tracking, auto-summarization, and hard cap enforcement.

The ContextBudget monitors token consumption across conversation turns and
automatically prunes or summarizes older context when the active window
approaches the model's context limit. This prevents:
  - "Lost in the middle" degradation (models ignoring relevant context)
  - Hard context window exceed errors
  - Exploding API costs from ever-growing conversation history

Architecture:
  - Each turn records input/output tokens via the ResourceBudget
  - When the rolling window exceeds a configurable threshold, older turns
    are summarized into a compressed representation
  - A hard cap prevents the conversation from exceeding the model's limit
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_logger = logging.getLogger(__name__)


class PruningStrategy(str, Enum):
    """Strategy used when context exceeds the active window."""

    NONE = 'none'  # No pruning — let it grow
    SUMMARIZE_OLDEST = 'summarize_oldest'  # Summarize oldest turns into a compressed form
    DROP_OLDEST = 'drop_oldest'  # Drop oldest turns entirely
    SUMMARIZE_AGENT_TURNS = 'summarize_agent_turns'  # Only summarize agent responses, keep user messages


@dataclass
class TurnRecord:
    """Record of a single conversation turn with token counts."""

    turn_index: int
    role: str  # 'user', 'agent_planner', 'agent_writer', 'agent_reviewer', etc.
    input_tokens: int = 0
    output_tokens: int = 0
    content_preview: str = ''  # First 100 chars
    summary: str = ''  # Summarized version (populated after pruning)
    timestamp: float = field(default_factory=time.time)
    model_used: str = ''
    estimated_cost_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def is_summarized(self) -> bool:
        return bool(self.summary) and len(self.summary) < len(self.content_preview)


@dataclass
class ContextBudgetConfig:
    """Configuration for context budget enforcement."""

    # The "active window" — tokens within this limit are kept in full detail
    active_window_tokens: int = 32_000

    # When total exceeds this, pruning kicks in
    pruning_threshold_tokens: int = 64_000

    # Hard cap — no conversation may exceed this (model's context limit)
    hard_cap_tokens: int = 128_000

    # Which pruning strategy to use
    strategy: PruningStrategy = PruningStrategy.SUMMARIZE_OLDEST

    # Number of most recent turns to always keep in full (never summarize)
    preserve_recent_turns: int = 5

    # Whether to track cost estimates alongside token counts
    track_cost: bool = True


@dataclass
class CostSummary:
    """Per-session cost tracking."""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_api_calls: int = 0
    estimated_cost_usd: float = 0.0
    by_model: dict[str, int] = field(default_factory=dict)  # model -> total_tokens
    by_agent: dict[str, int] = field(default_factory=dict)  # agent_type -> total_tokens

    def to_dict(self) -> dict[str, Any]:
        return {
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'total_api_calls': self.total_api_calls,
            'estimated_cost_usd': round(self.estimated_cost_usd, 4),
            'by_model': dict(self.by_model),
            'by_agent': dict(self.by_agent),
        }


class ContextBudget:
    """Manages token budget and context pruning for a conversation.

    Usage:
        budget = ContextBudget()
        budget.record_turn('user', input_tokens=1500, role='user')
        budget.record_turn('assistant', input_tokens=500, output_tokens=2000, role='agent_writer', model_used='deepseek-chat')
        if budget.needs_pruning():
            budget.prune()  # Summarize oldest turns
        print(budget.cost.to_dict())  # Total cost so far
    """

    def __init__(self, config: ContextBudgetConfig | None = None) -> None:
        self._config = config or ContextBudgetConfig()
        self._turns: list[TurnRecord] = []
        self._cost = CostSummary()
        self._next_turn = 0
        self._total_tokens_current: int = 0  # Rolling total of active (non-summarized) tokens

    # ── Recording turns ──────────────────────────────────────────

    def record_turn(
        self,
        role: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        content_preview: str = '',
        model_used: str = '',
        estimated_cost_usd: float = 0.0,
    ) -> TurnRecord:
        """Record a conversation turn and update cost tracking."""
        turn = TurnRecord(
            turn_index=self._next_turn,
            role=role,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            content_preview=content_preview[:200],
            model_used=model_used,
            estimated_cost_usd=estimated_cost_usd,
        )
        self._turns.append(turn)
        self._next_turn += 1

        # Update rolling token count (only non-summarized tokens count)
        if not turn.is_summarized:
            self._total_tokens_current += turn.total_tokens

        # Update cost tracking
        self._cost.total_input_tokens += input_tokens
        self._cost.total_output_tokens += output_tokens
        self._cost.total_api_calls += 1
        self._cost.estimated_cost_usd += estimated_cost_usd
        if model_used:
            self._cost.by_model[model_used] = (
                self._cost.by_model.get(model_used, 0) + turn.total_tokens
            )
        agent_type = role.replace('agent_', '') if role.startswith('agent_') else role
        self._cost.by_agent[agent_type] = (
            self._cost.by_agent.get(agent_type, 0) + turn.total_tokens
        )

        _logger.debug(
            'ContextBudget: turn %d role=%s in=%d out=%d total=%d cost=$%.4f',
            turn.turn_index,
            role,
            input_tokens,
            output_tokens,
            self._total_tokens_current,
            turn.estimated_cost_usd,
        )

        return turn

    # ── Pruning ──────────────────────────────────────────────────

    def needs_pruning(self) -> bool:
        """Check if the active context exceeds the pruning threshold."""
        return self._total_tokens_current > self._config.pruning_threshold_tokens

    def at_capacity(self) -> bool:
        """Check if the hard cap is reached — further turns should be blocked."""
        return self._total_tokens_current >= self._config.hard_cap_tokens

    def prune(self) -> list[TurnRecord]:
        """Prune old turns to bring context back within the active window.

        Returns the list of turns that were pruned/summarized.
        """
        if not self.needs_pruning():
            return []

        strategy = self._config.strategy
        preserve = self._config.preserve_recent_turns
        pruned: list[TurnRecord] = []

        # Identify which turns to keep in full (most recent N)
        keep_indices = set()
        for i in range(max(0, len(self._turns) - preserve), len(self._turns)):
            keep_indices.add(i)

        # Process older turns
        for i, turn in enumerate(self._turns):
            if i in keep_indices:
                continue
            if turn.is_summarized:
                continue  # Already pruned

            if strategy == PruningStrategy.DROP_OLDEST:
                # Mark as summarized with empty content (effectively dropped)
                turn.summary = '[dropped]'
                self._total_tokens_current -= turn.total_tokens
                pruned.append(turn)

            elif strategy == PruningStrategy.SUMMARIZE_OLDEST:
                # Compress the content preview into a short summary
                raw = turn.content_preview
                if len(raw) > 50:
                    # Create a compressed representation
                    summary = self._auto_summarize(raw, turn.role)
                else:
                    summary = raw

                old_tokens = turn.total_tokens
                turn.summary = summary
                # After summarization, the token cost of this turn is much lower
                summarized_tokens = max(20, len(summary))
                self._total_tokens_current -= (old_tokens - summarized_tokens)
                pruned.append(turn)

            elif strategy == PruningStrategy.SUMMARIZE_AGENT_TURNS:
                # Only summarize agent turns, keep user messages intact
                if turn.role.startswith('agent_'):
                    raw = turn.content_preview
                    summary = self._auto_summarize(raw, turn.role) if len(raw) > 50 else raw
                    old_tokens = turn.total_tokens
                    turn.summary = summary
                    summarized_tokens = max(20, len(summary))
                    self._total_tokens_current -= (old_tokens - summarized_tokens)
                    pruned.append(turn)

            # Check if we're back within the active window
            if self._total_tokens_current <= self._config.active_window_tokens:
                break

        _logger.info(
            'ContextBudget: pruned %d turns, active tokens now %d',
            len(pruned),
            self._total_tokens_current,
        )
        return pruned

    # ── Queries ──────────────────────────────────────────────────

    def current_tokens(self) -> int:
        """Current number of active (non-summarized) tokens."""
        return self._total_tokens_current

    def usage_pct(self) -> float:
        """Percentage of hard cap used (0.0 to 1.0)."""
        if self._config.hard_cap_tokens <= 0:
            return 0.0
        return self._total_tokens_current / self._config.hard_cap_tokens

    def turn_count(self) -> int:
        return len(self._turns)

    def recent_turns(self, n: int = 5) -> list[TurnRecord]:
        """Get the N most recent turns."""
        return self._turns[-n:]

    def all_turns(self) -> list[TurnRecord]:
        return list(self._turns)

    @property
    def cost(self) -> CostSummary:
        return self._cost

    @property
    def config(self) -> ContextBudgetConfig:
        return self._config

    def to_dict(self) -> dict[str, Any]:
        return {
            'total_tokens': self._total_tokens_current,
            'turns': self.turn_count(),
            'usage_pct': round(self.usage_pct() * 100, 1),
            'needs_pruning': self.needs_pruning(),
            'at_capacity': self.at_capacity(),
            'cost': self._cost.to_dict(),
            'config': {
                'active_window': self._config.active_window_tokens,
                'pruning_threshold': self._config.pruning_threshold_tokens,
                'hard_cap': self._config.hard_cap_tokens,
                'strategy': self._config.strategy.value,
            },
        }

    # ── Internal ─────────────────────────────────────────────────

    @staticmethod
    def _auto_summarize(content: str, role: str) -> str:
        """Create a compressed summary of a turn's content.

        In a production system this would call a fast LLM to summarize.
        For now, uses a heuristic: extracts key information, drops boilerplate.
        """
        # Normalize line endings, split on newlines
        lines = content.replace('\r\n', '\n').split('\n')
        significant = [l for l in lines if len(l.strip()) > 20]
        if not significant:
            return content[:80]

        # Keep first and last significant lines + length info
        if len(significant) > 1:
            first = significant[0].strip()[:80]
            last = significant[-1].strip()[:80]
            omitted = len(significant) - 2
            return f"[{role} summary] {first} | [...{omitted} lines omitted...] | {last}"
        else:
            return f"[{role} summary] {significant[0].strip()[:120]}"
