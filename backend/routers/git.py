"""Git integration API endpoints.

Provides git operations for the workspace repository.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services import git_service
from backend.services.storage import Storage

router = APIRouter(prefix='/api/v1', tags=['git'])
storage = Storage.get_instance()


# Workspace root from env or default
def _workspace_root() -> str:
    settings = storage.get_settings()
    return settings.get('workspace_root', os.getenv('WORKSPACE_BASE', './workspace'))


# ── Status ─────────────────────────────────────────────────────────────────
@router.get('/git/status')
async def get_status() -> dict[str, Any]:
    """Get git status of the workspace."""
    return await git_service.git_status(_workspace_root())


# ── Init ──────────────────────────────────────────────────────────────────
@router.post('/git/init')
async def init_repo() -> dict[str, Any]:
    """Initialize a git repository in the workspace."""
    return await git_service.git_init(_workspace_root())


# ── Clone ─────────────────────────────────────────────────────────────────
class CloneRequest(BaseModel):
    url: str
    target_dir: str | None = None


@router.post('/git/clone')
async def clone_repo(req: CloneRequest) -> dict[str, Any]:
    """Clone a git repository into the workspace."""
    target = req.target_dir or req.url.rstrip('/').split('/')[-1].replace('.git', '')
    result = await git_service.git_clone(req.url, target, _workspace_root())
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error', 'Clone failed'))
    return result


# ── Commit ────────────────────────────────────────────────────────────────
class CommitRequest(BaseModel):
    message: str
    files: list[str] | None = None


@router.post('/git/commit')
async def commit_changes(req: CommitRequest) -> dict[str, Any]:
    """Stage files and create a commit."""
    result = await git_service.git_commit(req.message, _workspace_root(), req.files)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error', 'Commit failed'))
    return result


# ── Log ───────────────────────────────────────────────────────────────────
@router.get('/git/log')
async def get_log(limit: int = 20) -> list[dict[str, str]]:
    """Get recent git log."""
    return await git_service.git_log(_workspace_root(), limit)


# ── Branches ──────────────────────────────────────────────────────────────
@router.get('/git/branches')
async def get_branches() -> dict[str, Any]:
    """List branches and show current branch."""
    return await git_service.git_branches(_workspace_root())


# ── Diff ──────────────────────────────────────────────────────────────────
@router.get('/git/diff')
async def get_diff(file_path: str | None = None) -> str:
    """Get git diff."""
    return await git_service.git_diff(_workspace_root(), file_path)
