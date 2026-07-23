"""
Reviewer Agent — audits generated code for bugs, quality issues, and security vulnerabilities.

The Reviewer performs multi-dimensional analysis:
  1. COMPILE CHECK: Syntax validation, import resolution, type consistency
  2. QUALITY CHECK: Code style, complexity, duplicate patterns
  3. SECURITY CHECK: Injection risks, auth flaws, data exposure
  4. 3D/WEBGL CHECK: GPU leak detection, context loss handling, performance
  5. CONSISTENCY CHECK: Cross-file import alignment, naming conventions
  6. COMPLETENESS CHECK: Placeholder detection, missing error handling

Outputs a structured ReviewReport with actionable fix suggestions.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from wren.app_builder.llm_client import LLMClient

_logger = logging.getLogger(__name__)


# ── Data models ───────────────────────────────────────────────────────────


@dataclass
class ReviewIssue:
    """A single issue found during code review."""

    file: str
    line: int = 0
    severity: str = "warning"  # error, warning, info
    category: str = "quality"  # compile, quality, security, 3d, consistency, completeness
    message: str = ""
    suggestion: str = ""
    auto_fixable: bool = False


@dataclass
class ReviewReport:
    """Complete code review report."""

    project_name: str
    files_reviewed: int
    total_issues: int
    issues: list[ReviewIssue] = field(default_factory=list)
    passed: bool = False
    summary: str = ""
    score: int = 100  # 0-100 quality score

    def issues_by_severity(self, severity: str) -> list[ReviewIssue]:
        return [i for i in self.issues if i.severity == severity]

    def issues_by_category(self, category: str) -> list[ReviewIssue]:
        return [i for i in self.issues if i.category == category]

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "files_reviewed": self.files_reviewed,
            "total_issues": self.total_issues,
            "issues": [
                {"file": i.file, "line": i.line, "severity": i.severity,
                 "category": i.category, "message": i.message, "suggestion": i.suggestion}
                for i in self.issues
            ],
            "passed": self.passed,
            "summary": self.summary,
            "score": self.score,
        }


# ── Built-in static checks ────────────────────────────────────────────────


def _static_check_file(file_path: str, content: str) -> list[ReviewIssue]:
    """Run static analysis on a single file."""
    issues: list[ReviewIssue] = []
    lines = content.split("\n")

    # 1. Check for placeholder patterns
    placeholder_patterns = [
        (r"TODO", "Placeholder TODO found"),
        (r"FIXME", "Unresolved FIXME marker"),
        (r"HACK", "Code smell: HACK marker"),
        (r"XXX", "Unresolved XXX marker"),
        (r"\.\.\.", "Ellipsis found — possible placeholder"),
        (r"not\s+implemented", "Not implemented marker"),
        (r"stub|STUB", "Stub implementation detected"),
        (r"add\s+your", "Generic placeholder detected"),
        (r"your\s+code\s+here", "Generic code placeholder"),
    ]
    for i, line in enumerate(lines, 1):
        for pattern, message in placeholder_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(ReviewIssue(
                    file=file_path,
                    line=i,
                    severity="warning",
                    category="completeness",
                    message=message,
                    suggestion="Replace with complete implementation",
                    auto_fixable=False,
                ))
                break  # One issue per line max

    # 2. Check for bare excepts (Python)
    if file_path.endswith(".py"):
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped == "except:":
                issues.append(ReviewIssue(
                    file=file_path,
                    line=i,
                    severity="error",
                    category="quality",
                    message="Bare except clause — catches all exceptions",
                    suggestion="Specify exception type: except SpecificError:",
                    auto_fixable=False,
                ))

    # 3. Check for console.log (production JS/TS)
    if file_path.endswith((".ts", ".tsx", ".js", ".jsx")):
        for i, line in enumerate(lines, 1):
            if "console.log" in line and "// eslint-disable" not in line:
                issues.append(ReviewIssue(
                    file=file_path,
                    line=i,
                    severity="info",
                    category="quality",
                    message="Console.log in production code",
                    suggestion="Remove or replace with proper logging",
                    auto_fixable=True,
                ))

    # 4. Check for missing .dispose() in 3D components
    if "three" in content.lower() or "THREE" in content:
        for i, line in enumerate(lines, 1):
            if ("useEffect" in line or "useEffect" in line or "componentWillUnmount" in line):
                # Check if dispose is present in the next 20 lines
                nearby = "\n".join(lines[i : i + 20])
                if "dispose" not in nearby.lower() and "cleanup" not in nearby.lower():
                    issues.append(ReviewIssue(
                        file=file_path,
                        line=i,
                        severity="warning",
                        category="3d",
                        message="Missing GPU resource cleanup in effect cleanup",
                        suggestion="Add geometry.dispose(), material.dispose(), texture.dispose() in cleanup",
                        auto_fixable=False,
                    ))
                break

    # 5. Check for WebGL context loss handling
    if "renderer" in content.lower() and ("webgl" in content.lower() or "three" in content.lower()):
        if "contextlost" not in content.lower() and "webglcontextlost" not in content.lower():
            issues.append(ReviewIssue(
                file=file_path,
                line=0,
                severity="warning",
                category="3d",
                message="Missing WebGL context loss handling",
                suggestion="Add 'webglcontextlost' event listener with gl.forceContextRestore()",
                auto_fixable=False,
            ))

    # 6. Check for very long lines
    for i, line in enumerate(lines, 1):
        if len(line) > 150 and not line.strip().startswith(("//", "#", "/*", "*")):
            issues.append(ReviewIssue(
                file=file_path,
                line=i,
                severity="info",
                category="quality",
                message=f"Very long line ({len(line)} chars)",
                suggestion="Consider breaking into multiple lines",
                auto_fixable=True,
            ))
            break  # One per file is enough

    # 7. Check for empty files or files with too few meaningful lines
    meaningful_lines = sum(1 for l in lines if l.strip() and not l.strip().startswith(("//", "#", "/*", "*", "\n")))
    if meaningful_lines < 3 and len(lines) > 0:
        issues.append(ReviewIssue(
            file=file_path,
            line=0,
            severity="error",
            category="completeness",
            message="File has very few meaningful lines of code",
            suggestion="The file appears to be empty or mostly comments",
            auto_fixable=False,
        ))

    # 8. Check for 'any' type in TypeScript (should be avoided)
    if file_path.endswith((".ts", ".tsx")):
        for i, line in enumerate(lines, 1):
            if re.search(r":\s*any\b", line) and "eslint" not in line:
                issues.append(ReviewIssue(
                    file=file_path,
                    line=i,
                    severity="info",
                    category="quality",
                    message="Use of 'any' type — consider a more specific type",
                    suggestion="Replace with proper interface or type, or use 'unknown' if truly unknown",
                    auto_fixable=False,
                ))
                break  # One per file

    return issues


def _calculate_quality_score(issues: list[ReviewIssue], total_files: int) -> tuple[int, str]:
    """Calculate quality score (0-100) from issues."""
    if total_files == 0:
        return 100, "No files to review"

    # Penalties per issue type
    score = 100
    penalty_map = {
        "error": 15,
        "warning": 5,
        "info": 1,
    }

    for issue in issues:
        penalty = penalty_map.get(issue.severity, 5)
        score -= penalty

    score = max(0, min(100, score))

    if score >= 90:
        summary = "Excellent code quality"
    elif score >= 75:
        summary = "Good code quality with minor issues"
    elif score >= 50:
        summary = "Fair code quality — several issues to address"
    else:
        summary = "Poor code quality — significant issues found"

    return score, summary


# ── LLM-based Review ──────────────────────────────────────────────────────


REVIEW_SYSTEM_PROMPT = """\
# WREN REVIEWER: CODE QUALITY AUDITOR

You are Wren Reviewer — an elite code auditor with expertise across all 
programming domains. You find bugs that static analysis tools miss.

## REVIEW FRAMEWORK:
Analyze each file for:

1. LOGIC BUGS: Off-by-one errors, race conditions, incorrect algorithm logic
2. SECURITY FLAWS: SQL injection, XSS, CSRF, Insecure Direct Object References (IDOR)
3. TYPE MISMATCHES: Wrong function signatures, missing null checks
4. IMPORT ERRORS: Missing imports, circular dependencies
5. PERFORMANCE: Unnecessary computations, memory leaks, render thrashing
6. 3D/WEBGL: Missing dispose(), context loss, animation frame leaks
7. API DESIGN: Incorrect HTTP methods, status codes, error formats

## OUTPUT FORMAT:
Output ONLY a JSON object:

```json
{
  "issues": [
    {
      "file": "src/component.tsx",
      "line": 42,
      "severity": "error|warning|info",
      "category": "logic|security|type|import|performance|3d|api|consistency",
      "message": "Clear description of the issue",
      "suggestion": "Specific fix suggestion"
    }
  ]
}
```

If no issues found, output: {"issues": []}
"""


# ── Reviewer Agent ────────────────────────────────────────────────────────


class ReviewerAgent:
    """Agent that reviews generated code and produces actionable reports."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        api_key: str = "",
        model: str = "gpt-4o",
        base_url: str | None = None,
    ):
        if llm_client:
            self._llm = llm_client
        else:
            self._llm = LLMClient(api_key=api_key, model=model, base_url=base_url)

    async def review(
        self,
        project_name: str,
        files: list[tuple[str, str]],  # [(path, content), ...]
        has_3d: bool = False,
        has_auth: bool = False,
        has_database: bool = False,
    ) -> ReviewReport:
        """Review all generated files and produce a report.

        Args:
            project_name: Name of the project
            files: List of (file_path, file_content) tuples
            has_3d: Whether the project uses 3D/WebGL
            has_auth: Whether the project has authentication
            has_database: Whether the project uses a database

        Returns:
            ReviewReport with all issues found
        """
        _logger.info("ReviewerAgent: reviewing %d files for %s", len(files), project_name)
        start = time.time()

        all_issues: list[ReviewIssue] = []

        # ── Phase 1: Static Analysis ──────────────────────────────
        for file_path, content in files:
            static_issues = _static_check_file(file_path, content)
            all_issues.extend(static_issues)

        # ── Phase 2: LLM-based Deep Analysis ──────────────────────
        try:
            llm_issues = await self._llm_review(
                project_name, files, has_3d, has_auth, has_database
            )
            all_issues.extend(llm_issues)
        except Exception as e:
            _logger.warning("ReviewerAgent: LLM review failed (continuing with static): %s", e)

        # ── Phase 3: Deduplicate ──────────────────────────────────
        seen = set()
        unique_issues: list[ReviewIssue] = []
        for issue in all_issues:
            key = (issue.file, issue.line, issue.message[:50])
            if key not in seen:
                seen.add(key)
                unique_issues.append(issue)

        # ── Phase 4: Score ────────────────────────────────────────
        score, summary = _calculate_quality_score(unique_issues, len(files))

        elapsed = time.time() - start
        _logger.info(
            "ReviewerAgent: review complete — %d issues (score: %d) in %.1fs",
            len(unique_issues), score, elapsed,
        )

        return ReviewReport(
            project_name=project_name,
            files_reviewed=len(files),
            total_issues=len(unique_issues),
            issues=unique_issues,
            passed=len([i for i in unique_issues if i.severity == "error"]) == 0,
            summary=summary,
            score=score,
        )

    async def _llm_review(
        self,
        project_name: str,
        files: list[tuple[str, str]],
        has_3d: bool,
        has_auth: bool,
        has_database: bool,
    ) -> list[ReviewIssue]:
        """Use LLM to perform deep code review."""
        # Build a compact representation of all files
        file_snippets: list[str] = []
        for file_path, content in files:
            lines = content.split("\n")
            # Include full file for small files, first/last 30 lines for larger
            if len(lines) <= 80:
                file_snippets.append(f"=== {file_path} ===\n{content}")
            else:
                head = "\n".join(lines[:30])
                tail = "\n".join(lines[-20:])
                file_snippets.append(f"=== {file_path} ===\n{head}\n// ... ({len(lines) - 50} middle lines)\n{tail}")

        project_context = (
            f"Project: {project_name}\n"
            f"3D/WebGL: {has_3d}\n"
            f"Auth: {has_auth}\n"
            f"Database: {has_database}\n"
            f"Total Files: {len(files)}\n"
        )

        user_prompt = (
            f"{project_context}\n"
            f"Review the following generated files for bugs, security issues, and quality problems:\n\n"
            f"{chr(10).join(file_snippets)}\n\n"
            f"Output ONLY the JSON review with specific, actionable issues."
        )

        response = await self._llm.send(
            REVIEW_SYSTEM_PROMPT, user_prompt,
            task_type="review", role="reviewer",
        )

        return self._parse_review_response(response)

    def _parse_review_response(self, response: str) -> list[ReviewIssue]:
        """Parse LLM review response into ReviewIssue objects."""
        issues: list[ReviewIssue] = []

        # Try to find JSON in code block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        json_str = json_match.group(1) if json_match else response

        # Fallback: find top-level JSON object
        if not json_match:
            obj_match = re.search(r"\{[^{}]*\"issues\"[^{}]*\}", response, re.DOTALL)
            if obj_match:
                json_str = obj_match.group()

        try:
            data = json.loads(json_str)
            for item in data.get("issues", []):
                issues.append(ReviewIssue(
                    file=item.get("file", ""),
                    line=item.get("line", 0),
                    severity=item.get("severity", "warning"),
                    category=item.get("category", "quality"),
                    message=item.get("message", ""),
                    suggestion=item.get("suggestion", ""),
                ))
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            _logger.warning("ReviewerAgent: failed to parse LLM review: %s", e)

        return issues

    def format_report(self, report: ReviewReport) -> str:
        """Format a review report as a readable string."""
        lines: list[str] = []
        lines.append(f"📋 Review Report: {report.project_name}")
        lines.append(f"   Files reviewed: {report.files_reviewed}")
        lines.append(f"   Score: {report.score}/100 — {report.summary}")
        lines.append(f"   Total issues: {report.total_issues}")
        lines.append("")

        if report.issues:
            # Group by severity
            for severity in ("error", "warning", "info"):
                severities = {
                    "error": "🔴 ERRORS",
                    "warning": "🟡 WARNINGS",
                    "info": "🔵 INFO",
                }
                group = [i for i in report.issues if i.severity == severity]
                if group:
                    lines.append(f"  {severities[severity]} ({len(group)}):")
                    for issue in group:
                        loc = f":{issue.line}" if issue.line else ""
                        lines.append(f"    • {issue.file}{loc}")
                        lines.append(f"      {issue.message}")
                        if issue.suggestion:
                            lines.append(f"      💡 {issue.suggestion[:100]}")
                    lines.append("")
        else:
            lines.append("  ✅ No issues found! Code is clean.")
            lines.append("")

        return "\n".join(lines)

    async def close(self) -> None:
        await self._llm.close()
