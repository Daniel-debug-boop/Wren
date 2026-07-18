"""Runtime quality gates.

Enforce quality standards at key lifecycle checkpoints:
  - Pre-commit gate: code must pass critique score threshold
  - Pre-deploy gate: all fact checks must pass
  - Post-completion gate: reflection report must be clean
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

_logger = logging.getLogger(__name__)


class GateVerdict(str, Enum):
    PASS = 'pass'
    WARN = 'warn'
    FAIL = 'fail'
    SKIP = 'skip'


@dataclass
class GateResult:
    name: str = ''
    verdict: GateVerdict = GateVerdict.PASS
    score: float = 1.0
    message: str = ''
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.verdict in (GateVerdict.PASS, GateVerdict.WARN)


@dataclass
class QualityGatesReport:
    gates: list[GateResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(g.passed for g in self.gates)

    @property
    def failures(self) -> list[GateResult]:
        return [g for g in self.gates if g.verdict == GateVerdict.FAIL]

    def summary(self) -> str:
        parts = [f'{g.name}={g.verdict.value}' for g in self.gates]
        return f'gates: {", ".join(parts)}'


class QualityGates:
    """Pipeline of quality gates that agent output must pass.

    Each gate is a callable that receives context and returns
    a GateResult.
    """

    def __init__(self) -> None:
        self._gates: list[tuple[str, Callable, float]] = []
        # Built-in gates
        self.register(
            'critique_threshold', self._gate_critique_threshold, min_score=0.6
        )
        self.register('response_nonempty', self._gate_nonempty, min_score=0.5)
        self.register('no_blockers', self._gate_no_blockers, min_score=0.8)

    def register(
        self,
        name: str,
        gate_fn: Callable,
        min_score: float = 0.0,
    ) -> None:
        self._gates.append((name, gate_fn, min_score))

    def unregister(self, name: str) -> None:
        self._gates = [(n, fn, s) for n, fn, s in self._gates if n != name]

    async def run_all(self, context: dict[str, Any]) -> QualityGatesReport:
        report = QualityGatesReport()
        for name, gate_fn, min_score in self._gates:
            try:
                result = gate_fn(context, min_score)
                if asyncio.iscoroutine(result):
                    result = await result
                report.gates.append(result)
            except Exception as e:
                report.gates.append(
                    GateResult(
                        name=name,
                        verdict=GateVerdict.FAIL,
                        message=str(e),
                    )
                )
        return report

    # ── Built-in gates ───────────────────────────────────────────

    @staticmethod
    def _gate_critique_threshold(ctx: dict[str, Any], min_score: float) -> GateResult:
        score = ctx.get('critique_score', 1.0)
        if score >= min_score:
            return GateResult(
                name='critique_threshold', verdict=GateVerdict.PASS, score=score
            )
        return GateResult(
            name='critique_threshold',
            verdict=GateVerdict.FAIL,
            score=score,
            message=f'Critique score {score:.2f} < {min_score:.2f}',
        )

    @staticmethod
    def _gate_nonempty(ctx: dict[str, Any], _min: float) -> GateResult:
        text = ctx.get('response', '')
        if text.strip():
            return GateResult(
                name='response_nonempty',
                verdict=GateVerdict.PASS,
                score=1.0,
                details={'length': len(text)},
            )
        return GateResult(
            name='response_nonempty',
            verdict=GateVerdict.FAIL,
            score=0.0,
            message='Response is empty',
        )

    @staticmethod
    def _gate_no_blockers(ctx: dict[str, Any], _min: float) -> GateResult:
        blockers = ctx.get('blockers', [])
        if not blockers:
            return GateResult(name='no_blockers', verdict=GateVerdict.PASS, score=1.0)
        return GateResult(
            name='no_blockers',
            verdict=GateVerdict.FAIL,
            score=0.0,
            message=f'{len(blockers)} blocker(s) found',
            details={'blockers': blockers},
        )

    def __repr__(self) -> str:
        return f'QualityGates(gates={len(self._gates)})'
