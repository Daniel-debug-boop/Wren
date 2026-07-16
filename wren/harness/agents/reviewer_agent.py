"""Reviewer Agent — runs automated checks on generated code.

The Reviewer takes output from the WriterAgent and:
  1. Runs static analysis checks (linting, type checking)
  2. Verifies acceptance criteria from the plan are met
  3. Checks for common bugs and anti-patterns
  4. Generates a review report with pass/fail status per file
  5. Provides fix suggestions for failed checks

Can use fast models (GPT-4o-mini, Gemini Flash) for quick reviews
or premium models for deep analysis.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

from wren.harness.agents.base import ChildAgent
from wren.harness.message_bus import AgentMessage, MessagePriority, MessageType

_logger = logging.getLogger(__name__)


@dataclass
class ReviewCheck:
    """A single review check result."""

    check_name: str
    passed: bool
    severity: str = 'info'  # 'info', 'warning', 'error', 'blocker'
    message: str = ''
    suggestion: str = ''
    file_path: str = ''
    line_number: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            'check_name': self.check_name,
            'passed': self.passed,
            'severity': self.severity,
            'message': self.message,
            'suggestion': self.suggestion,
            'file_path': self.file_path,
            'line_number': self.line_number,
        }


@dataclass
class FileReview:
    """Review result for a single file."""

    file_path: str
    overall_passed: bool
    checks: list[ReviewCheck] = field(default_factory=list)
    summary: str = ''
    score: float = 1.0  # 0.0-1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            'file_path': self.file_path,
            'overall_passed': self.overall_passed,
            'checks': [c.to_dict() for c in self.checks],
            'summary': self.summary,
            'score': self.score,
        }


@dataclass
class ReviewReport:
    """Complete review report for all files."""

    files: list[FileReview] = field(default_factory=list)
    overall_passed: bool = False
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    blocker_count: int = 0
    summary: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {
            'files': [f.to_dict() for f in self.files],
            'overall_passed': self.overall_passed,
            'total_checks': self.total_checks,
            'passed_checks': self.passed_checks,
            'failed_checks': self.failed_checks,
            'blocker_count': self.blocker_count,
            'summary': self.summary,
        }


class ReviewerAgent(ChildAgent):
    """Child agent that reviews and verifies generated code.

    The Reviewer:
      1. Receives file contents and their planned acceptance criteria
      2. Runs static analysis checks on each file
      3. Verifies acceptance criteria are met
      4. Generates a structured review report
      5. Flags critical issues (blockers) that must be fixed

    Uses lightweight models for quick checks by default.
    """

    # Patterns to check for common issues
    _PATTERNS: dict[str, list[tuple[str, str, str]]] = {
        'security': [
            (r'(api_key|password|secret|token)\s*=\s*["\'](?![*])', 'hardcoded_secret', 'error'),
            (r'eval\s*\(', 'eval_call', 'warning'),
            (r'exec\s*\(', 'exec_call', 'warning'),
        ],
        'quality': [
            (r'except\s*:', 'bare_except', 'warning'),
            (r'(TODO|FIXME|HACK|XXX)', 'unresolved_todo', 'info'),
            (r'print\s*\(', 'stray_print', 'info'),
        ],
        'correctness': [
            (r'import\s+\*', 'wildcard_import', 'warning'),
            (r'raise\s+NotImplementedError', 'not_implemented', 'error'),
        ],
    }

    def __init__(self, agent_id: str = '') -> None:
        super().__init__(agent_id or 'reviewer_agent', 'reviewer')

    async def _on_init(self) -> None:
        _logger.debug('ReviewerAgent: init')

    async def _execute(self, task: dict[str, Any]) -> dict[str, Any]:
        description = task.get('description', task.get('task', ''))
        files = task.get('files', [])
        plan = task.get('plan', {})
        write_result = task.get('write_result', {})
        acceptance_criteria = task.get('acceptance_criteria', [])
        language = task.get('language', 'python')

        _logger.info('ReviewerAgent: reviewing %d files', len(files))

        start = time.time()

        # Collect file-content pairs from the write result
        file_contents: list[tuple[str, str]] = []
        results = write_result.get('results', [])
        for r in results:
            file_path = r.get('file_path', '')
            content = r.get('content_preview', '')
            if file_path:
                file_contents.append((file_path, content))

        # Also include files from the task
        for f in files:
            if not any(fc[0] == f for fc in file_contents):
                file_contents.append((f, ''))

        # Run reviews
        plan_changes = plan.get('changes', [])
        reviews = await self._review_files(
            file_contents, plan_changes, acceptance_criteria, language
        )

        report = self._build_report(reviews)

        report_dict = report.to_dict()
        report_dict['duration_s'] = round(time.time() - start, 2)

        if self._bus:
            await self._bus.publish(
                AgentMessage(
                    source=self.agent_id,
                    msg_type=MessageType.TASK_RESULT,
                    payload={'review': report_dict},
                ),
                token=self._token,
            )

        _logger.info(
            'ReviewerAgent: done passed=%s checks=%d/%d',
            report.overall_passed,
            report.passed_checks,
            report.total_checks,
        )
        return report_dict

    async def _review_files(
        self,
        file_contents: list[tuple[str, str]],
        plan_changes: list[dict[str, Any]],
        acceptance_criteria: list[str],
        language: str,
    ) -> list[FileReview]:
        """Review all files, both via bus (LLM) and local static analysis."""
        reviews: list[FileReview] = []

        for file_path, content in file_contents:
            checks: list[ReviewCheck] = []

            # 1. Run local pattern-based checks
            checks.extend(self._static_analysis(file_path, content, language))

            # 2. Verify acceptance criteria
            planned_criteria = self._get_criteria_for_file(file_path, plan_changes)
            checks.extend(
                self._check_acceptance_criteria(
                    file_path, content, planned_criteria + acceptance_criteria
                )
            )

            # 3. Try LLM-based review via bus
            if self._bus and content:
                try:
                    llm_checks = await self._llm_review(file_path, content, language)
                    checks.extend(llm_checks)
                except Exception as e:
                    _logger.debug('ReviewerAgent: LLM review failed: %s', e)

            # Build file review
            passed_checks = sum(1 for c in checks if c.passed)
            score = passed_checks / max(len(checks), 1)
            blockers = [c for c in checks if c.severity == 'blocker']

            reviews.append(
                FileReview(
                    file_path=file_path,
                    overall_passed=len(blockers) == 0,
                    checks=checks,
                    summary=(
                        f'{passed_checks}/{len(checks)} checks passed'
                        if checks
                        else 'No checks performed'
                    ),
                    score=score,
                )
            )

        return reviews

    def _static_analysis(
        self, file_path: str, content: str, language: str
    ) -> list[ReviewCheck]:
        """Run local pattern-based static analysis."""
        checks: list[ReviewCheck] = []

        if not content:
            return checks

        for category, patterns in self._PATTERNS.items():
            for pattern, name, severity in patterns:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                if matches:
                    for match in matches[:3]:  # Limit per pattern
                        line_num = content[: match.start()].count('\n') + 1
                        checks.append(
                            ReviewCheck(
                                check_name=name,
                                passed=False,
                                severity=severity,
                                message=f'{category}: {name} found',
                                suggestion=self._get_suggestion(name),
                                file_path=file_path,
                                line_number=line_num,
                            )
                        )

        # Language-specific checks
        if language == 'python':
            checks.extend(self._check_python(file_path, content))
        elif language in ('javascript', 'typescript'):
            checks.extend(self._check_typescript(file_path, content))

        return checks

    def _check_python(self, file_path: str, content: str) -> list[ReviewCheck]:
        """Python-specific checks."""
        checks: list[ReviewCheck] = []
        lines = content.split('\n')

        # Check for missing docstrings in functions
        for i, line in enumerate(lines):
            if re.match(r'^def\s+\w+\s*\(', line):
                # Scan past decorators to find the first non-decorator, non-empty line
                for j in range(i + 1, min(i + 8, len(lines))):  # Allow up to 7 decorators
                    next_line = lines[j].strip()
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        break  # Has docstring — good
                    if next_line.startswith('@'):
                        continue  # Skip decorators
                    if next_line:
                        # Non-empty, non-decorator, non-docstring line found
                        checks.append(
                            ReviewCheck(
                                check_name='missing_docstring',
                                passed=False,
                                severity='info',
                                message=f'Function at line {i + 1} is missing a docstring',
                                suggestion='Add a docstring describing the function purpose',
                                file_path=file_path,
                                line_number=i + 1,
                            )
                        )
                        break

        # Check line length
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                checks.append(
                    ReviewCheck(
                        check_name='line_too_long',
                        passed=False,
                        severity='info',
                        message=f'Line {i} exceeds 120 characters ({len(line)})',
                        suggestion='Consider breaking into multiple lines',
                        file_path=file_path,
                        line_number=i,
                    )
                )
                break  # One warning is enough

        return checks

    def _check_typescript(self, file_path: str, content: str) -> list[ReviewCheck]:
        """TypeScript/JavaScript-specific checks."""
        checks: list[ReviewCheck] = []

        if 'any' in content and ': any' in content:
            checks.append(
                ReviewCheck(
                    check_name='any_type_usage',
                    passed=False,
                    severity='warning',
                    message='Using `any` type suppresses type checking',
                    suggestion='Replace `any` with a proper type or `unknown`',
                    file_path=file_path,
                )
            )

        return checks

    @staticmethod
    def _extract_keywords(criterion: str) -> list[str]:
        """Extract meaningful keywords from a criterion, filtering out stopwords."""
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'has', 'have', 'had',
            'be', 'been', 'being', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'shall', 'this', 'that', 'these',
            'those', 'with', 'without', 'for', 'and', 'nor', 'but', 'or', 'yet',
            'so', 'i', 'then', 'else', 'when', 'than', 'too', 'very', 'just',
            'not', 'no', 'its', 'it\'s', 'their', 'them', 'they', 'all', 'each',
        }
        return [
            w for w in criterion.lower().split()
            if len(w) > 3 and w not in stopwords
        ]

    def _check_acceptance_criteria(
        self,
        file_path: str,
        content: str,
        criteria: list[str],
    ) -> list[ReviewCheck]:
        """Check if acceptance criteria are met using keyword matching."""
        checks: list[ReviewCheck] = []

        for criterion in criteria:
            keywords = self._extract_keywords(criterion)
            if not keywords:
                continue
            meaningful_matches = sum(
                1 for kw in keywords if kw in content.lower()
            )
            found = meaningful_matches >= max(1, len(keywords) // 2)

            checks.append(
                ReviewCheck(
                    check_name='acceptance_criterion',
                    passed=found,
                    severity='error' if not found else 'info',
                    message=f"Acceptance criterion: {criterion}",
                    suggestion='Ensure this requirement is addressed',
                    file_path=file_path,
                )
            )

        return checks

    async def _llm_review(
        self, file_path: str, content: str, language: str
    ) -> list[ReviewCheck]:
        """Use LLM via bus for deeper review."""
        req = AgentMessage(
            source=self.agent_id,
            msg_type=MessageType.TASK_REQUEST,
            priority=MessagePriority.MEDIUM,
            payload={
                'action': 'review',
                'file_path': file_path,
                'content': content[:4000],  # Limit content
                'language': language,
            },
        )
        resp = await self._bus.publish_and_wait(
            req, token=self._token, timeout_s=30.0
        )
        if resp and 'checks' in resp.payload:
            return [
                ReviewCheck(
                    check_name=c.get('check_name', 'llm_review'),
                    passed=c.get('passed', False),
                    severity=c.get('severity', 'info'),
                    message=c.get('message', ''),
                    suggestion=c.get('suggestion', ''),
                    file_path=c.get('file_path', file_path),
                    line_number=c.get('line_number', 0),
                )
                for c in resp.payload['checks']
            ]
        return []

    def _build_report(self, reviews: list[FileReview]) -> ReviewReport:
        """Build a complete review report from individual file reviews."""
        total_checks = sum(len(r.checks) for r in reviews)
        passed_checks = sum(len([c for c in r.checks if c.passed]) for r in reviews)
        blocker_count = sum(
            len([c for c in r.checks if c.severity == 'blocker']) for r in reviews
        )

        return ReviewReport(
            files=reviews,
            overall_passed=all(r.overall_passed for r in reviews),
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=total_checks - passed_checks,
            blocker_count=blocker_count,
            summary=(
                f'Reviewed {len(reviews)} files: {passed_checks}/{total_checks} checks '
                f'passed ({blocker_count} blockers)'
            ),
        )

    @staticmethod
    def _get_criteria_for_file(
        file_path: str, changes: list[dict[str, Any]]
    ) -> list[str]:
        """Get acceptance criteria for a specific file from the plan."""
        for change in changes:
            if change.get('file_path') == file_path:
                return change.get('acceptance_criteria', [])
        return []

    @staticmethod
    def _get_suggestion(name: str) -> str:
        suggestions = {
            'hardcoded_secret': 'Use environment variables or a secrets manager',
            'eval_call': 'Avoid eval; use safer alternatives like ast.literal_eval',
            'bare_except': 'Specify the exception type (e.g., except ValueError:)',
            'unresolved_todo': 'Complete the implementation before shipping',
            'stray_print': 'Use logging instead of print for production code',
            'wildcard_import': 'Import specific names instead of the entire module',
            'not_implemented': 'Implement the function or mark it as explicitly WIP',
            'missing_docstring': 'Add a docstring describing the function purpose',
            'line_too_long': 'Break long lines for better readability',
            'any_type_usage': 'Use proper TypeScript types instead of any',
        }
        return suggestions.get(name, f'Review and fix: {name}')

    async def _on_shutdown(self) -> None:
        _logger.debug('ReviewerAgent: shutdown')
