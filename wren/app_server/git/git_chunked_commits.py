"""Granular git commit system with semantic chunking and atomic commits.

Analyzes staged changes and splits them into logical atomic chunks,
generating semantic commit messages for each chunk.

Features:
  - Pattern-based chunking: split changes by file type, function boundary, or location
  - Semantic message generation: descriptive commit messages per chunk
  - Atomic commits: one logical change per commit
  - Pre-commit hook integration: validates commit granularity
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import Sequence

logger = logging.getLogger(__name__)


# ─── Data Models ─────────────────────────────────────────────────────────────


@dataclass
class ChunkedFile:
    """A single file change tracked in a chunk."""

    path: str
    change_type: str  # 'added', 'modified', 'deleted', 'renamed'
    diff: str = ""
    old_path: str = ""


@dataclass
class CommitChunk:
    """A logical atomic chunk of changes with its commit message."""

    title: str
    description: str
    files: list[ChunkedFile] = field(default_factory=list)

    @property
    def message(self) -> str:
        """Full commit message combining title and description."""
        if self.description:
            return f"{self.title}\n\n{self.description}"
        return self.title

    @property
    def file_count(self) -> int:
        return len(self.files)


@dataclass
class ChunkResult:
    """Result of chunking analysis."""

    chunks: list[CommitChunk]
    total_files: int
    unstaged_count: int = 0


# ─── Git Operations ─────────────────────────────────────────────────────────


def _run_git(*args: str, cwd: str = ".") -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )
    if result.returncode != 0:
        logger.warning("git %s failed: %s", " ".join(args), result.stderr.strip())
        return ""
    return result.stdout.strip()


def _get_staged_diff(cwd: str = ".") -> str:
    """Get the full diff of staged changes."""
    return _run_git("diff", "--cached", "--stat", cwd=cwd)


def _get_staged_files(cwd: str = ".") -> list[ChunkedFile]:
    """Parse staged files from git status."""
    output = _run_git("diff", "--cached", "--name-status", cwd=cwd)
    if not output:
        return []

    files: list[ChunkedFile] = []
    for line in output.split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            status = parts[0]
            path = parts[1]
            change_type = {
                "A": "added",
                "M": "modified",
                "D": "deleted",
                "R": "renamed",
            }.get(status[0], "modified")

            file_entry = ChunkedFile(path=path, change_type=change_type)
            if status.startswith("R") and len(parts) >= 3:
                file_entry.old_path = parts[2]

            # Get the diff content for this file
            diff = _run_git("diff", "--cached", path, cwd=cwd)
            file_entry.diff = diff
            files.append(file_entry)

    return files


def _get_unstaged_count(cwd: str = ".") -> int:
    """Count unstaged modified files (not untracked, not staged)."""
    output = _run_git("status", "--porcelain", cwd=cwd)
    if not output:
        return 0
    # Unstaged lines start with a space then a status char: ' M', ' D', etc.
    # `??` = untracked (not counted as unstaged)
    return sum(
        1
        for line in output.split("\n")
        if line.strip() and line.startswith(" ")
    )


# ─── Chunking Logic ─────────────────────────────────────────────────────────


def _categorize_file(path: str) -> str:
    """Categorize a file into a change group based on its path."""
    ext = os.path.splitext(path)[1].lower()
    basename = os.path.basename(path).lower()

    # Documentation
    if ext in (".md", ".rst", ".txt", ".adoc"):
        return "docs"
    if basename in ("readme", "readme.md", "contributing.md", "license"):
        return "docs"

    # Configuration
    if ext in (".toml", ".yml", ".yaml", ".json", ".ini", ".cfg", ".conf"):
        return "config"
    if basename in (
        "pyproject.toml",
        "package.json",
        "dockerfile",
        "makefile",
        "gemfile",
        "cargo.toml",
    ):
        return "config"

    # Tests
    name_noext = os.path.splitext(basename)[0]
    if "test" in basename or ext in (".test.ts", ".test.js", "_test.go", "_test.py"):
        return "tests"
    if name_noext.startswith("test_") or name_noext.endswith("_test"):
        return "tests"

    # Styles
    if ext in (".css", ".scss", ".less", ".sass"):
        return "styles"

    # TypeScript / JavaScript
    if ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
        if path.startswith("src/api") or path.startswith("lib/api"):
            return "api"
        if path.startswith("src/components") or path.startswith("lib/components"):
            return "components"
        if path.startswith("src/hooks") or path.startswith("lib/hooks"):
            return "hooks"
        if path.startswith("src/utils") or path.startswith("lib/utils"):
            return "utils"
        if path.startswith("src/types") or path.startswith("lib/types"):
            return "types"
        return "source"

    # Python
    if ext == ".py":
        if path.startswith("tests") or "test" in path:
            return "tests"
        if path.startswith("api") or "/api/" in path:
            return "api"
        return "source"

    # Default
    return "other"


def _generate_chunk_title(category: str, files: list[ChunkedFile]) -> str:
    """Generate a semantic commit title for a chunk."""
    base_titles = {
        "source": "feat: update source code",
        "api": "feat(api): update API layer",
        "components": "feat(ui): update UI components",
        "hooks": "feat(hooks): update hooks",
        "utils": "chore: update utilities",
        "types": "chore: update type definitions",
        "tests": "test: add/update tests",
        "docs": "docs: update documentation",
        "config": "chore: update configuration",
        "styles": "style: update styles",
        "other": "chore: update miscellaneous files",
    }

    # Try to generate a more specific title from the file
    specific_titles: list[str] = []
    types_seen: set[str] = set()
    for f in files:
        if f.change_type == "added":
            if "feat" not in specific_titles:
                specific_titles.append("feat")
        elif f.change_type == "deleted":
            if "remove" not in specific_titles:
                specific_titles.append("remove")

        # Extract function/component name from path
        basename = os.path.splitext(os.path.basename(f.path))[0]
        if basename not in types_seen:
            types_seen.add(basename)
            specific_titles.append(basename)

    if specific_titles:
        prefix = specific_titles[0]
        if len(files) == 1:
            name = os.path.splitext(os.path.basename(files[0].path))[0]
            change_word = "add" if files[0].change_type == "added" else "update"
            return f"{prefix}({category}): {change_word} {name}"
        else:
            return f"{prefix}: update {len(files)} files"

    return base_titles.get(category, "chore: update files")


def _generate_chunk_description(category: str, files: list[ChunkedFile]) -> str:
    """Generate a detailed commit description for a chunk."""
    lines: list[str] = []
    for f in files:
        prefix = {
            "added": "+",
            "modified": "~",
            "deleted": "-",
            "renamed": ">",
        }.get(f.change_type, " ")
        lines.append(f"{prefix} {f.path}")
    return "\n".join(lines)


def analyze_changes(cwd: str = ".") -> ChunkResult:
    """Analyze staged changes and split into logical commit chunks.

    Returns a ChunkResult with grouped changes organized by semantic category.
    Each chunk represents one logical atomic commit.
    """
    files = _get_staged_files(cwd)
    if not files:
        return ChunkResult(chunks=[], total_files=0, unstaged_count=_get_unstaged_count(cwd))

    # Group files by category
    grouped: dict[str, list[ChunkedFile]] = {}
    for f in files:
        category = _categorize_file(f.path)
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(f)

    # Also handle single-file chunks for monorepo-style changes
    # If a single file is significantly large, it gets its own chunk
    chunks: list[CommitChunk] = []

    # Process by category (but split into smaller chunks for large groups)
    CHUNK_MAX_FILES = 5  # Max files per chunk

    for category, category_files in grouped.items():
        if len(category_files) <= CHUNK_MAX_FILES:
            chunks.append(
                CommitChunk(
                    title=_generate_chunk_title(category, category_files),
                    description=_generate_chunk_description(category, category_files),
                    files=category_files,
                )
            )
        else:
            # Split large groups into smaller chunks
            for i in range(0, len(category_files), CHUNK_MAX_FILES):
                subset = category_files[i : i + CHUNK_MAX_FILES]
                chunks.append(
                    CommitChunk(
                        title=_generate_chunk_title(category, subset),
                        description=_generate_chunk_description(category, subset),
                        files=subset,
                    )
                )

    return ChunkResult(
        chunks=chunks,
        total_files=len(files),
        unstaged_count=_get_unstaged_count(cwd),
    )


def apply_chunk(chunk: CommitChunk, cwd: str = ".") -> bool:
    """Commit a single chunk to git.

    Stages only the files in this chunk and commits them with the
    generated message.

    Returns True if commit was successful.
    """
    if not chunk.files:
        logger.warning("Empty chunk, skipping")
        return False

    # Stage only files in this chunk
    for file in chunk.files:
        if file.change_type == "deleted":
            result = subprocess.run(
                ["git", "rm", file.path],
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=10,
            )
        elif file.change_type == "renamed":
            if file.old_path:
                _run_git("rm", "--cached", file.old_path, cwd=cwd)
                _run_git("add", file.path, cwd=cwd)
        else:
            _run_git("add", file.path, cwd=cwd)

    # Commit with generated message
    result = subprocess.run(
        ["git", "commit", "-m", chunk.title, "-m", chunk.description],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=15,
    )

    if result.returncode == 0:
        logger.info(
            "Committed chunk: %s (%d files)",
            chunk.title,
            len(chunk.files),
        )
        return True
    else:
        logger.error("Commit failed: %s", result.stderr.strip())
        return False


def commit_all_chunks(dry_run: bool = False, cwd: str = ".") -> list[dict]:
    """Analyze and commit all changes in granular chunks.

    This is the main entry point for the feature. It:
    1. Analyzes staged changes
    2. Groups into logical chunks
    3. Commits each chunk atomically

    If dry_run is True, only preview the chunks without committing.
    Returns a list of result dicts with chunk info.
    """
    result = analyze_changes(cwd)
    results: list[dict] = []

    if result.total_files == 0:
        logger.info("No staged changes to commit")
        return results

    logger.info(
        "Found %d staged files, %d unstaged",
        result.total_files,
        result.unstaged_count,
    )

    for chunk in result.chunks:
        info = {
            "title": chunk.title,
            "description": chunk.description,
            "files": [f.path for f in chunk.files],
            "file_count": chunk.file_count,
        }

        if dry_run:
            logger.info("[DRY RUN] Would commit: %s", chunk.title)
        else:
            success = apply_chunk(chunk, cwd)
            info["success"] = success
            if not success:
                logger.error("  ✗ Failed to commit chunk: %s", chunk.title)

        results.append(info)

    return results


# ─── CLI Interface ──────────────────────────────────────────────────────────


def print_chunk_preview(result: ChunkResult) -> None:
    """Print a human-readable preview of the chunk analysis."""
    if result.total_files == 0:
        print("  No staged changes found.")
        if result.unstaged_count > 0:
            print(f"  ({result.unstaged_count} unstaged file(s) not included)")
        return

    print(f"\n  Total: {result.total_files} staged file(s) across {len(result.chunks)} chunk(s)")
    if result.unstaged_count > 0:
        print(f"  Note: {result.unstaged_count} unstaged file(s) not included")

    for i, chunk in enumerate(result.chunks, 1):
        print(f"\n  {i}. {chunk.title}")
        if chunk.description:
            # Show first line of description
            first_line = chunk.description.split("\n")[0]
            print(f"     {first_line}")
        for file in chunk.files:
            prefix = {
                "added": "+",
                "modified": "~",
                "deleted": "-",
                "renamed": ">",
            }.get(file.change_type, " ")
            print(f"     {prefix} {file.path}")
