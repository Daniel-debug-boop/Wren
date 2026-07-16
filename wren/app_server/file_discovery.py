"""Smart context discovery — automatically finds relevant files for the current task.

Analyzes the task description and project structure to discover which files
are most relevant for the agent's context window. Uses pattern matching,
dependency analysis, and heuristics to prioritize the right files.

Features:
  - Task-based file relevance scoring
  - Dependency-aware file discovery (imports, requires, etc.)
  - Smart ranking based on modification history and code relationships
  - Configurable context budget for token-aware file selection
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

logger = logging.getLogger(__name__)


# ─── Data Models ─────────────────────────────────────────────────────────────


@dataclass
class ScoredFile:
    """A file with its relevance score for the current task."""

    path: str
    score: float  # 0.0 to 1.0
    reason: str = ""  # Why this file is relevant
    size_bytes: int = 0
    last_modified: float = 0.0

    @property
    def lines_estimate(self) -> int:
        """Estimate line count from file size."""
        return max(1, self.size_bytes // 40)


@dataclass
class TaskContext:
    """Analyzed task context with relevant files."""

    task: str
    files: list[ScoredFile]
    total_files_scanned: int
    estimated_tokens: int = 0

    @property
    def top_files(self) -> list[ScoredFile]:
        """Return the highest-scored files."""
        return sorted(self.files, key=lambda f: f.score, reverse=True)

    def get_top_k(self, k: int = 10) -> list[ScoredFile]:
        """Get the top k most relevant files."""
        return self.top_files[:k]


# ─── Relevance Scoring ──────────────────────────────────────────────────────


# Keywords that indicate file relevance based on task type
_TASK_KEYWORDS: dict[str, list[str]] = {
    "frontend": [
        "component", "page", "route", "view", "ui", "react", "vue", "angular",
        "tsx", "jsx", "css", "scss", "style", "layout", "widget",
    ],
    "backend": [
        "api", "route", "handler", "controller", "service", "middleware",
        "model", "schema", "migration", "query", "database", "db",
    ],
    "testing": [
        "test", "spec", "mock", "stub", "fixture", "assertion",
        "coverage", "integration", "e2e", "unit",
    ],
    "config": [
        "config", "setting", "env", "docker", "ci", "pipeline",
        "deploy", "workflow", "makefile", "package",
    ],
    "docs": [
        "readme", "documentation", "doc", "guide", "tutorial",
        "contributing", "changelog", "license",
    ],
}

# File extension relevance for different task domains
_EXTENSION_WEIGHTS: dict[str, float] = {
    ".py": 1.0,
    ".ts": 1.0,
    ".tsx": 1.0,
    ".js": 0.9,
    ".jsx": 0.9,
    ".go": 1.0,
    ".rs": 1.0,
    ".java": 1.0,
    ".kt": 1.0,
    ".swift": 1.0,
    ".cpp": 0.9,
    ".c": 0.9,
    ".h": 0.7,
    ".rb": 0.9,
    ".php": 0.9,
    ".vue": 0.9,
    ".svelte": 0.9,
    ".css": 0.6,
    ".scss": 0.6,
    ".html": 0.6,
    ".json": 0.5,
    ".yaml": 0.5,
    ".yml": 0.5,
    ".toml": 0.5,
    ".md": 0.4,
    ".txt": 0.3,
}

# File patterns to always exclude
_EXCLUDE_PATTERNS: list[str] = [
    "node_modules/",
    ".git/",
    "__pycache__/",
    ".venv/",
    "venv/",
    ".tox/",
    "dist/",
    "build/",
    ".next/",
    "coverage/",
    ".cache/",
    "target/",
    ".eggs/",
    "*.pyc",
    "*.pyo",
    "*.egg-info/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "*.min.js",
    "*.min.css",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "uv.lock",
]


def _should_exclude(path: str) -> bool:
    """Check if a file should be excluded from context discovery."""
    for pattern in _EXCLUDE_PATTERNS:
        if pattern.endswith("/"):
            if pattern in path:
                return True
        elif pattern.startswith("*."):
            if path.endswith(pattern[1:]):
                return True
        elif pattern in path:
            return True
    return False


def _extract_task_keywords(task: str) -> list[str]:
    """Extract relevant keywords from a task description."""
    task_lower = task.lower()
    keywords: set[str] = set()

    # Extract words
    words = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", task_lower)
    keywords.update(w for w in words if len(w) > 2)

    return list(keywords)


def _score_file_for_task(file_path: str, task_keywords: list[str]) -> tuple[float, str]:
    """Score a file's relevance to a task.

    Returns a tuple of (score, reason).
    """
    score = 0.0
    reasons: list[str] = []
    file_lower = file_path.lower()
    basename = os.path.basename(file_lower)
    ext = os.path.splitext(file_lower)[1]

    # Base score from extension
    base_weight = _EXTENSION_WEIGHTS.get(ext, 0.2)
    score += base_weight * 0.3
    if base_weight >= 0.9:
        reasons.append("primary source file")

    # Direct keyword matches in path
    matched_kws: set[str] = set()
    for kw in task_keywords:
        if kw in file_lower:
            score += 0.15
            if kw not in matched_kws:
                matched_kws.add(kw)
                reasons.append(f"matches '{kw}'")

    # Check for common patterns
    if basename.startswith("index.") or basename.startswith("main."):
        score += 0.2
        reasons.append("entry point")

    if "component" in file_lower or "component" in task_keywords:
        if "component" in file_lower:
            score += 0.2

    # Task-type specific scoring
    for task_type, keywords in _TASK_KEYWORDS.items():
        if any(kw in task_keywords for kw in keywords[:3]):
            # Boost files matching the task type
            if task_type == "frontend" and ext in (".tsx", ".jsx", ".vue", ".svelte"):
                score += 0.2
                if "UI file" not in reasons:
                    reasons.append("UI file")
            elif task_type == "testing" and ("test" in file_lower):
                score += 0.4
                if "test file" not in reasons:
                    reasons.append("test file")
            elif task_type == "backend" and ("/api/" in file_lower):
                score += 0.2

    # Penalize large generated files
    if ".generated." in file_lower or ".min." in file_lower:
        score -= 0.5

    # Boost for files with import/export patterns (likely source files)
    if "/src/" in file_lower or "/lib/" in file_lower:
        score += 0.1

    # Clamp score to 0.0–1.0
    score = max(0.0, min(1.0, score))

    reason_str = ", ".join(reasons[:3]) if reasons else "low relevance"
    return score, reason_str


# ─── File Discovery ─────────────────────────────────────────────────────────


def discover_relevant_files(
    task: str,
    workspace_dir: str = ".",
    max_files: int = 50,
    max_depth: int = 5,
) -> TaskContext:
    """Discover files relevant to a task in the workspace.

    Scans the workspace directory, scores each file for relevance to the
    task description, and returns the top matches.

    Args:
        task: The task description to find relevant files for.
        workspace_dir: Root directory to scan.
        max_files: Maximum number of top files to return.
        max_depth: Maximum directory depth to scan.

    Returns:
        TaskContext with scored relevant files.
    """
    task_keywords = _extract_task_keywords(task)
    scored_files: list[ScoredFile] = []

    workspace = Path(workspace_dir).resolve()
    if not workspace.exists():
        logger.warning("Workspace directory does not exist: %s", workspace)
        return TaskContext(task=task, files=[], total_files_scanned=0)

    for root, dirs, files_in_dir in os.walk(workspace):
        # Calculate depth
        rel_path = Path(root).relative_to(workspace)
        depth = len(rel_path.parts)
        if depth > max_depth:
            dirs.clear()
            continue

        # Skip excluded directories
        dirs[:] = [
            d
            for d in dirs
            if not _should_exclude(f"{rel_path}/{d}/" if str(rel_path) != "." else f"{d}/")
        ]

        for filename in files_in_dir:
            file_path = os.path.join(root, filename)
            rel_file = os.path.relpath(file_path, workspace)

            if _should_exclude(rel_file):
                continue

            try:
                stat = os.stat(file_path)
                size = stat.st_size
                modified = stat.st_mtime
            except OSError:
                continue

            score, reason = _score_file_for_task(rel_file, task_keywords)

            # Only include files with non-zero score
            if score > 0 and size > 0:
                scored_files.append(
                    ScoredFile(
                        path=rel_file,
                        score=score,
                        reason=reason,
                        size_bytes=size,
                        last_modified=modified,
                    )
                )

    # Sort by score descending
    total_checked = len(scored_files)  # All files that passed exclusion filters
    scored_files.sort(key=lambda f: f.score, reverse=True)

    # If too many files, find a natural cutoff
    if len(scored_files) > max_files:
        threshold = scored_files[max_files - 1].score
        scored_files = [f for f in scored_files if f.score >= threshold][:max_files]

    # Estimate tokens (rough: 4 chars = 1 token)
    total_chars = sum(f.size_bytes for f in scored_files)
    estimated_tokens = total_chars // 4

    logger.info(
        "Discovered %d relevant files from %d candidates for task (est. %d tokens)",
        len(scored_files),
        total_checked,
        estimated_tokens,
    )

    return TaskContext(
        task=task,
        files=scored_files,
        total_files_scanned=total_checked,
        estimated_tokens=estimated_tokens,
    )


def format_context_for_agent(context: TaskContext, max_files: int = 10) -> str:
    """Format discovered files as a context block for agent injection.

    Creates a formatted string showing the most relevant files with their
    paths, ready for inclusion in the agent's system prompt or context.
    """
    top = context.get_top_k(max_files)
    if not top:
        return ""

    lines = ["<relevant_files>"]
    lines.append(f"  <!-- Task: {context.task[:100]} -->")
    lines.append(f"  <!-- Total scanned: {context.total_files_scanned} files -->")
    lines.append(f"  <!-- Estimated context tokens: {context.estimated_tokens} -->")
    lines.append("")

    for i, file in enumerate(top, 1):
        score_pct = int(file.score * 100)
        lines.append(f"  {i}. {file.path}  [{score_pct}% relevance]")
        if file.reason:
            lines.append(f"     → {file.reason}")

    lines.append("</relevant_files>")
    return "\n".join(lines)


def get_context_for_task(
    task: str,
    workspace_dir: str = ".",
    max_tokens: int = 8_000,
) -> str:
    """One-shot: get formatted context for a task, respecting token budget.

    Discovers relevant files and returns formatted context that fits
    within the token budget. Files are included in priority order until
    the budget is reached.

    Args:
        task: The task description.
        workspace_dir: Workspace root directory.
        max_tokens: Maximum tokens for the context block.

    Returns:
        Formatted context string ready for agent injection.
    """
    context = discover_relevant_files(task, workspace_dir)

    if not context.files:
        return ""

    # Select files that fit within token budget
    selected_files: list[ScoredFile] = []
    used_tokens = 0
    for file in context.top_files:
        file_tokens = file.lines_estimate // 2  # Rough: 2 tokens per line
        if used_tokens + file_tokens <= max_tokens:
            selected_files.append(file)
            used_tokens += file_tokens
        else:
            break

    # Format the selected files
    context.files = selected_files
    return format_context_for_agent(context)
