"""Self-critique agent that reviews agent output for quality,
correctness, and completeness before it reaches the user.

Runs as a lightweight evaluator in the reflection pipeline.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum

_logger = logging.getLogger(__name__)


class CritiqueSeverity(str, Enum):
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    BLOCKER = 'blocker'


@dataclass
class CritiqueFinding:
    severity: CritiqueSeverity = CritiqueSeverity.INFO
    category: str = ''
    message: str = ''
    suggestion: str = ''
    location: str = ''  # file/line reference


@dataclass
class CritiqueReport:
    findings: list[CritiqueFinding] = field(default_factory=list)
    score: float = 1.0  # 0.0-1.0 quality score

    @property
    def blockers(self) -> list[CritiqueFinding]:
        return [f for f in self.findings if f.severity == CritiqueSeverity.BLOCKER]

    @property
    def errors(self) -> list[CritiqueFinding]:
        return [f for f in self.findings if f.severity == CritiqueSeverity.ERROR]

    @property
    def warnings(self) -> list[CritiqueFinding]:
        return [f for f in self.findings if f.severity == CritiqueSeverity.WARNING]

    def passed(self) -> bool:
        return not self.blockers and len(self.errors) <= 3

    def summary(self) -> str:
        parts = []
        for s in (
            CritiqueSeverity.BLOCKER,
            CritiqueSeverity.ERROR,
            CritiqueSeverity.WARNING,
        ):
            count = len([f for f in self.findings if f.severity == s])
            if count:
                parts.append(f'{s.value}={count}')
        return (
            f'score={self.score:.2f} {"|".join(parts)}'
            if parts
            else f'score={self.score:.2f}'
        )


class SelfCritiqueAgent:
    """Lightweight static-analysis-style critique agent.

    Performs pattern-based checks on code and text output.
    No external model required — runs inline.
    """

    def __init__(self) -> None:
        self._patterns: dict[str, list[tuple[str, str, CritiqueSeverity]]] = {
            'security': [
                (
                    r'(api_key|password|secret|token)\s*=\s*["\'](?![*])',
                    'hardcoded_secret',
                    CritiqueSeverity.ERROR,
                ),
                (r'eval\s*\(', 'eval_call', CritiqueSeverity.WARNING),
                (r'exec\s*\(', 'exec_call', CritiqueSeverity.WARNING),
                (r'(sudo|chmod\s+777)', 'overly_permissive', CritiqueSeverity.WARNING),
            ],
            'quality': [
                (r'except\s*:', 'bare_except', CritiqueSeverity.WARNING),
                (r'(TODO|FIXME|HACK|XXX)', 'unresolved_todo', CritiqueSeverity.INFO),
                (r'print\s*\(', 'stray_print', CritiqueSeverity.INFO),
                (r'pass\s*#', 'stub_implementation', CritiqueSeverity.WARNING),
            ],
            'correctness': [
                (r'import\s+\*', 'wildcard_import', CritiqueSeverity.WARNING),
                (r'\.git\s*=\s*["\']', 'git_in_code', CritiqueSeverity.INFO),
            ],
            'completeness': [
                (
                    r'raise\s+NotImplementedError',
                    'not_implemented',
                    CritiqueSeverity.ERROR,
                ),
            ],
        }

    def critique_text(self, text: str, source: str = 'agent_output') -> CritiqueReport:
        """Run pattern-based critique on arbitrary text."""
        report = CritiqueReport()
        for category, patterns in self._patterns.items():
            for pattern, name, severity in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    report.findings.append(
                        CritiqueFinding(
                            severity=severity,
                            category=category,
                            message=name,
                            suggestion=self._suggestion(name),
                            location=f'{source}:{self._line_number(text, match.start())}',
                        )
                    )
        # Compute score
        weights = {
            CritiqueSeverity.BLOCKER: 0.5,
            CritiqueSeverity.ERROR: 0.2,
            CritiqueSeverity.WARNING: 0.1,
            CritiqueSeverity.INFO: 0.02,
        }
        penalty = sum(weights.get(f.severity, 0) for f in report.findings)
        report.score = max(0.0, min(1.0, 1.0 - penalty))
        return report

    def critique_code(self, code: str, language: str = 'python') -> CritiqueReport:
        """Run code-specific critique."""
        report = self.critique_text(code, source=f'code.{language}')
        if language == 'python':
            # Indentation consistency
            lines = code.split('\n')
            for i, line in enumerate(lines, 1):
                if line.startswith('\t') and any(l.startswith('    ') for l in lines):
                    report.findings.append(
                        CritiqueFinding(
                            severity=CritiqueSeverity.WARNING,
                            category='quality',
                            message='mixed_indentation',
                            suggestion='Use 4 spaces consistently',
                            location=f'code.{language}:{i}',
                        )
                    )
                    break
        return report

    def critique_response(self, response: str) -> CritiqueReport:
        """Critique agent response text."""
        report = self.critique_text(response, source='response')
        # Check for empty/truncated responses
        if len(response.strip()) < 20:
            report.findings.append(
                CritiqueFinding(
                    severity=CritiqueSeverity.WARNING,
                    category='completeness',
                    message='response_too_short',
                    suggestion='Provide a more detailed response',
                )
            )
        return report

    @staticmethod
    def _suggestion(name: str) -> str:
        suggestions = {
            'hardcoded_secret': 'Use env vars or secret store',
            'eval_call': 'Avoid eval; use safer alternatives',
            'bare_except': 'Specify exception type',
            'unresolved_todo': 'Complete before shipping',
            'stray_print': 'Use logging instead',
            'stub_implementation': 'Implement or raise NotImplementedError',
            'wildcard_import': 'Import specific names',
            'not_implemented': 'Implement or document as WIP',
        }
        return suggestions.get(name, f'Review: {name}')

    @staticmethod
    def _line_number(text: str, pos: int) -> int:
        return text[:pos].count('\n') + 1
