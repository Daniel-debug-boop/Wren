"""Code extraction utility for parsing LLM-generated code into workspace files.

Extracts fenced code blocks with optional filename annotations from LLM output,
writes them to the workspace directory, and returns a structured file manifest.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)

# Match fenced code blocks: ```lang\n...\n```
# Optional filename hint: ```python:path/to/file.py
_FENCE_RE = re.compile(
    r'```'
    r'(?:(?P<lang>[a-zA-Z0-9_+-]+)(?::\s*(?P<filepath>[^\s`][^`]*?))?)?'
    r'\n'
    r'(?P<code>.*?)'
    r'\n?```',
    re.DOTALL,
)

# Filename extraction from markdown headings before code blocks
_HEADING_FILE_RE = re.compile(
    r'^#+\s*(?:`([^`]+)`|([^\s:]+\.[a-zA-Z0-9]{1,10}))\s*$',
    re.MULTILINE,
)

# Common language-to-extension mapping
_LANG_EXT: dict[str, str] = {
    'python': '.py',
    'py': '.py',
    'javascript': '.js',
    'js': '.js',
    'typescript': '.ts',
    'ts': '.ts',
    'tsx': '.tsx',
    'jsx': '.jsx',
    'html': '.html',
    'css': '.css',
    'json': '.json',
    'yaml': '.yml',
    'yml': '.yml',
    'bash': '.sh',
    'shell': '.sh',
    'sh': '.sh',
    'sql': '.sql',
    'go': '.go',
    'rust': '.rs',
    'rs': '.rs',
    'java': '.java',
    'rb': '.rb',
    'ruby': '.rb',
    'toml': '.toml',
    'ini': '.ini',
    'xml': '.xml',
    'markdown': '.md',
    'md': '.md',
}

# Files that should never be written by the generator
_BLOCKED_PATTERNS = {
    '.env',
    '.env.local',
    '.env.production',
    'id_rsa',
    'id_ed25519',
    '.bash_history',
    '.ssh',
}


def extract_code_blocks(text: str) -> list[dict[str, Any]]:
    """Extract fenced code blocks from LLM output.

    Returns a list of dicts with keys: lang, filepath, code, line_number.
    """
    blocks: list[dict[str, Any]] = []
    for match in _FENCE_RE.finditer(text):
        lang = (match.group('lang') or '').strip().lower()
        filepath = (match.group('filepath') or '').strip()
        code = match.group('code')
        if not code.strip():
            continue
        blocks.append({
            'lang': lang,
            'filepath': filepath,
            'code': code,
            'line_number': text[:match.start()].count('\n') + 1,
        })
    return blocks


def _is_blocked_path(filepath: str) -> bool:
    """Check if a file path should be blocked from writing."""
    name = Path(filepath).name
    if name in _BLOCKED_PATTERNS:
        return True
    parts = Path(filepath).parts
    for part in parts:
        if part in _BLOCKED_PATTERNS:
            return True
        if part.startswith('.') and part not in {'.', '..'}:
            # Allow dotfiles like .gitignore, .dockerignore but block .env*, .ssh etc.
            if any(part.startswith(p) for p in {'.env', '.ssh', '.gnupg'}):
                return True
    return False


def _infer_filename(
    block: dict[str, Any],
    index: int,
) -> str:
    """Infer a filename for a code block that has no explicit path."""
    lang = block['lang']
    ext = _LANG_EXT.get(lang, '')
    if not ext:
        ext = '.txt'
    return f'generated/file_{index}{ext}'


def _validate_path(filepath: str) -> str:
    """Normalize and validate a file path.

    Returns the cleaned path or raises ValueError.
    """
    # Remove leading slashes and backslashes
    filepath = filepath.strip().lstrip('/\\')
    # Normalize separators
    filepath = filepath.replace('\\', '/')
    # Remove any traversal attempts
    parts = Path(filepath).parts
    safe_parts = [p for p in parts if p not in ('..', '.')]
    clean = str(Path(*safe_parts)) if safe_parts else filepath
    return clean


def extract_and_write_files(
    text: str,
    workspace_root: str | Path,
    project_subdir: str | None = None,
) -> dict[str, Any]:
    """Extract code blocks from LLM output and write them to the workspace.

    Args:
        text: The LLM-generated content (may contain fenced code blocks).
        workspace_root: Root directory of the workspace.
        project_subdir: Optional subdirectory within workspace for this project.

    Returns:
        Dict with keys: files (list of written files), errors, total_lines.
    """
    workspace_root = Path(workspace_root)
    if project_subdir:
        target_dir = workspace_root / project_subdir
    else:
        target_dir = workspace_root

    blocks = extract_code_blocks(text)
    written_files: list[dict[str, Any]] = []
    errors: list[str] = []
    total_lines = 0

    for i, block in enumerate(blocks):
        # Determine filepath
        if block['filepath']:
            try:
                filepath = _validate_path(block['filepath'])
            except (ValueError, OSError) as e:
                errors.append(f'Invalid path "{block["filepath"]}": {e}')
                continue
        else:
            filepath = _infer_filename(block, i)

        # Security check
        if _is_blocked_path(filepath):
            _logger.warning('Blocked write to sensitive path: %s', filepath)
            errors.append(f'Blocked write to sensitive path: {filepath}')
            continue

        full_path = target_dir / filepath

        # Prevent writing outside workspace
        try:
            full_path.resolve().relative_to(target_dir.resolve())
        except ValueError:
            errors.append(f'Path escapes target directory: {filepath}')
            continue

        # Write the file
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(block['code'], encoding='utf-8')
            line_count = block['code'].count('\n') + 1
            total_lines += line_count
            written_files.append({
                'path': filepath,
                'language': block['lang'],
                'lines': line_count,
                'size_bytes': len(block['code'].encode('utf-8')),
            })
            _logger.info('Wrote file: %s (%d lines)', filepath, line_count)
        except OSError as e:
            errors.append(f'Failed to write {filepath}: {e}')
            _logger.error('Failed to write %s: %s', filepath, e)

    return {
        'files': written_files,
        'errors': errors,
        'total_files': len(written_files),
        'total_lines': total_lines,
    }
