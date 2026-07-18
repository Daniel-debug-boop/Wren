"""Resource/token budget controller.

Tracks token spend, memory usage, and execution time across all
agents. Enforces per-agent and global budgets. Raises BudgetExceeded
when limits hit.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

_logger = logging.getLogger(__name__)


class BudgetExceeded(Exception):
    """Raised when a resource budget is exhausted."""

    def __init__(self, resource: str, limit: float, actual: float) -> None:
        self.resource = resource
        self.limit = limit
        self.actual = actual
        super().__init__(f'{resource} budget exceeded: {actual:.1f} > {limit:.1f}')


@dataclass
class BudgetLimit:
    """Per-resource budget limits."""

    max_tokens_input: int = 1_000_000
    max_tokens_output: int = 200_000
    max_memory_mb: int = 1024
    max_execution_time_s: int = 3600  # 1 hour
    max_sub_tasks: int = 50
    max_api_calls: int = 500


@dataclass
class ResourceUsage:
    """Snapshot of current resource consumption."""

    tokens_input: int = 0
    tokens_output: int = 0
    memory_mb: float = 0.0
    execution_time_s: float = 0.0
    sub_task_count: int = 0
    api_call_count: int = 0
    started_at: float = field(default_factory=time.time)

    def elapsed(self) -> float:
        return time.time() - self.started_at

    def to_dict(self) -> dict[str, Any]:
        return {
            'tokens_input': self.tokens_input,
            'tokens_output': self.tokens_output,
            'memory_mb': round(self.memory_mb, 1),
            'execution_time_s': round(self.elapsed(), 1),
            'sub_task_count': self.sub_task_count,
            'api_call_count': self.api_call_count,
        }


class ResourceBudget:
    """Central budget controller.

    One instance per conversation. Agents register spend via the
    consume_* methods, which raise BudgetExceeded on violation.
    """

    def __init__(self, limits: BudgetLimit | None = None) -> None:
        self._limits = limits or BudgetLimit()
        self._usage = ResourceUsage()
        self._per_agent: dict[str, ResourceUsage] = {}
        _logger.info('ResourceBudget: limits=%s', self._limits)

    # ── Consumption ──────────────────────────────────────────────

    def consume_tokens(self, agent: str, inp: int = 0, out: int = 0) -> None:
        self._usage.tokens_input += inp
        self._usage.tokens_output += out
        self._get_agent(agent).tokens_input += inp
        self._get_agent(agent).tokens_output += out
        self._check(
            'tokens_input', self._usage.tokens_input, self._limits.max_tokens_input
        )
        self._check(
            'tokens_output', self._usage.tokens_output, self._limits.max_tokens_output
        )

    def consume_memory(self, agent: str, mb: float) -> None:
        self._usage.memory_mb += mb
        self._get_agent(agent).memory_mb += mb
        self._check('memory', self._usage.memory_mb, self._limits.max_memory_mb)

    def consume_api_call(self, agent: str) -> None:
        self._usage.api_call_count += 1
        self._get_agent(agent).api_call_count += 1
        self._check('api_calls', self._usage.api_call_count, self._limits.max_api_calls)

    def consume_sub_task(self) -> None:
        self._usage.sub_task_count += 1
        self._check('sub_tasks', self._usage.sub_task_count, self._limits.max_sub_tasks)

    # ── Checks ───────────────────────────────────────────────────

    def check_timeout(self) -> None:
        """Raise if global execution time exceeded."""
        self._check(
            'execution_time', self._usage.elapsed(), self._limits.max_execution_time_s
        )

    def within_limit(self, resource: str, agent: str | None = None) -> bool:
        """Check if still within budget without raising."""
        try:
            self._check_impl(resource, self._usage, self._limits)
            return True
        except BudgetExceeded:
            return False

    def agent_usage(self, agent: str) -> dict[str, Any]:
        u = self._per_agent.get(agent)
        return u.to_dict() if u else {}

    def global_usage(self) -> dict[str, Any]:
        return self._usage.to_dict()

    # ── Internals ────────────────────────────────────────────────

    def _get_agent(self, name: str) -> ResourceUsage:
        if name not in self._per_agent:
            self._per_agent[name] = ResourceUsage()
        return self._per_agent[name]

    def _check(self, resource: str, actual: float, limit: float) -> None:
        if actual > limit:
            raise BudgetExceeded(resource, limit, actual)

    def _check_impl(
        self, resource: str, usage: ResourceUsage, limits: BudgetLimit
    ) -> None:
        mapping = {
            'tokens_input': (usage.tokens_input, limits.max_tokens_input),
            'tokens_output': (usage.tokens_output, limits.max_tokens_output),
            'memory': (usage.memory_mb, limits.max_memory_mb),
            'execution_time': (usage.elapsed(), limits.max_execution_time_s),
            'sub_tasks': (usage.sub_task_count, limits.max_sub_tasks),
            'api_calls': (usage.api_call_count, limits.max_api_calls),
        }
        actual, limit = mapping.get(resource, (0, 1))
        if actual > limit:
            raise BudgetExceeded(resource, limit, actual)

    def __repr__(self) -> str:
        return f'ResourceBudget(usage={self._usage.to_dict()})'
