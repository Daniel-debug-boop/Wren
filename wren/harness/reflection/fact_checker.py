"""Fact-checking and validation engine.

Verifies agent claims against known facts, working memory, and
external sources. Flags contradictions, unsupported claims, and
outdated information.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_logger = logging.getLogger(__name__)


class FactCheckResult(str, Enum):
    CONFIRMED = 'confirmed'
    CONTRADICTED = 'contradicted'
    UNSUPPORTED = 'unsupported'
    UNCERTAIN = 'uncertain'


@dataclass
class FactCheck:
    claim: str = ''
    result: FactCheckResult = FactCheckResult.UNCERTAIN
    evidence: str = ''
    confidence: float = 0.0
    source: str = ''


@dataclass
class FactCheckReport:
    checks: list[FactCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        bad = {FactCheckResult.CONTRADICTED, FactCheckResult.UNSUPPORTED}
        return not any(c.result in bad for c in self.checks)

    def summary(self) -> str:
        counts: dict[str, int] = {}
        for c in self.checks:
            counts[c.result.value] = counts.get(c.result.value, 0) + 1
        return ' '.join(f'{k}={v}' for k, v in counts.items())


class FactChecker:
    """Validates agent claims against stored knowledge.

    Uses keyword overlap and pattern matching. For production,
    replace with an LLM-based verifier.
    """

    def __init__(self) -> None:
        self._known_facts: dict[str, dict[str, Any]] = {}
        self._contradictions: list[tuple[str, str]] = []  # (fact1, fact2)

    def register_fact(
        self, claim: str, source: str = '', confidence: float = 1.0
    ) -> None:
        """Register a fact as ground truth."""
        key = self._normalise(claim)
        self._known_facts[key] = {
            'claim': claim,
            'source': source,
            'confidence': confidence,
        }

    def register_contradiction(self, a: str, b: str) -> None:
        """Two claims that cannot both be true."""
        self._contradictions.append((self._normalise(a), self._normalise(b)))

    def check(self, claim: str) -> FactCheck:
        """Check a single claim against known facts."""
        key = self._normalise(claim)

        # Exact match
        if key in self._known_facts:
            f = self._known_facts[key]
            return FactCheck(
                claim=claim,
                result=FactCheckResult.CONFIRMED,
                evidence=f['claim'],
                confidence=f['confidence'],
                source=f['source'],
            )

        # Contradiction check
        for a, b in self._contradictions:
            if key == a and b in self._known_facts:
                return FactCheck(
                    claim=claim,
                    result=FactCheckResult.CONTRADICTED,
                    evidence=f'Contradicts: {self._known_facts[b]["claim"]}',
                    confidence=0.9,
                    source=self._known_facts[b]['source'],
                )

        # Partial match
        matched: list[str] = []
        for kf, f in self._known_facts.items():
            overlap = self._keyword_overlap(key, kf)
            if overlap > 0.4:
                matched.append(f['claim'])

        if matched:
            return FactCheck(
                claim=claim,
                result=FactCheckResult.CONFIRMED,
                evidence='; '.join(matched[:2]),
                confidence=0.5,
            )

        return FactCheck(
            claim=claim,
            result=FactCheckResult.UNSUPPORTED,
            confidence=0.0,
        )

    def check_many(self, claims: list[str]) -> FactCheckReport:
        return FactCheckReport(checks=[self.check(c) for c in claims])

    def extract_claims(self, text: str) -> list[str]:
        """Extract factual-sounding statements from text."""
        patterns = [
            r'(?:is|are|was|were|has|have|contains?)\s+\w+\s+\w+',
            r'(?:runs?\s+on|built?\s+(?:with|using)|powered\s+by)\s+\w+',
            r'(?:version|v)\d+[.\d]*',
            r'\d+\s*(?:MB|GB|TB|ms|s|req/s|users|rows)',
        ]
        claims = set()
        for pat in patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                claims.add(match.group().strip())
        return list(claims)[:20]

    def validate_response(
        self, response: str, source: str = 'agent'
    ) -> FactCheckReport:
        """Extract and validate all claims in a response."""
        claims = self.extract_claims(response)
        report = self.check_many(claims)
        for c in report.checks:
            c.source = source
        return report

    def clear(self) -> None:
        self._known_facts.clear()
        self._contradictions.clear()

    # ── Internal ─────────────────────────────────────────────────

    @staticmethod
    def _normalise(text: str) -> str:
        return re.sub(r'\s+', ' ', text.lower().strip())

    @staticmethod
    def _keyword_overlap(a: str, b: str) -> float:
        words_a = set(a.split())
        words_b = set(b.split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        return len(intersection) / max(len(words_a), len(words_b))
