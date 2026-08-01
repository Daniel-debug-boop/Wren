"""Workspace file API — browse, read, and write project files.

Lets the Monaco editor in the frontend work against real files on disk.
Paths are validated against the workspace root to prevent traversal.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix='/api/v1', tags=['workspace'])

# Workspace root: repo root by default, overridable via env
WORKSPACE_ROOT = Path(
    os.getenv('WREN_WORKSPACE', str(Path(__file__).resolve().parents[2]))
).resolve()

# Directories/files that should never appear in the tree
_EXCLUDED = {
    '.git',
    'node_modules',
    'build',
    'dist',
    '__pycache__',
    '.react-router',
    '.gradle',
    '.kotlin',
    '.venv',
    'venv',
    '.next',
    '.parcel-cache',
    '.wren',
    'coverage',
    '.husky',
    '.pytest_cache',
    '.mypy_cache',
    '.ruff_cache',
    '.gitignore',
    '.github',
}


def _safe_path(relative: str) -> Path:
    """Resolve a workspace-relative path, guarding against traversal."""
    target = (WORKSPACE_ROOT / relative).resolve()
    try:
        target.relative_to(WORKSPACE_ROOT)
    except ValueError:
        raise HTTPException(status_code=400, detail='Path escapes workspace root')
    return target


def _build_tree(path: Path, depth: int = 0, max_depth: int = 5) -> dict | None:
    if depth > max_depth:
        return None
    if path.is_file():
        return {
            'name': path.name,
            'path': str(path.relative_to(WORKSPACE_ROOT)),
            'type': 'file',
        }
    if path.is_dir():
        children = []
        for entry in sorted(
            path.iterdir(), key=lambda e: (e.is_file(), e.name.lower())
        ):
            if entry.name in _EXCLUDED:
                continue
            if entry.name.startswith('.') and entry.is_file():
                continue
            child = _build_tree(entry, depth + 1, max_depth)
            if child is not None:
                children.append(child)
        return {
            'name': path.name or WORKSPACE_ROOT.name,
            'path': str(path.relative_to(WORKSPACE_ROOT)),
            'type': 'directory',
            'children': children,
        }
    return None


@router.get('/workspace/tree')
async def workspace_tree():
    tree = _build_tree(WORKSPACE_ROOT)
    return {'root': WORKSPACE_ROOT.name, 'tree': tree}


@router.get('/workspace/file')
async def workspace_read(path: str):
    target = _safe_path(path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail=f'File not found: {path}')
    try:
        content = target.read_text(encoding='utf-8', errors='replace')
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f'Failed to read file: {exc}'
        ) from exc
    return {'path': path, 'content': content}


class FileWriteRequest(BaseModel):
    path: str
    content: str


@router.put('/workspace/file')
async def workspace_write(req: FileWriteRequest):
    target = _safe_path(req.path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text(req.content, encoding='utf-8')
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f'Failed to write file: {exc}'
        ) from exc
    return {'status': 'saved', 'path': req.path}
