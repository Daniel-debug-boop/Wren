"""Terminal execution API endpoints.

Provides shell command execution within the workspace sandbox,
and script running for supported languages.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.terminal_service import exec_command, run_script
from backend.services.storage import Storage

router = APIRouter(prefix='/api/v1', tags=['terminal'])
storage = Storage.get_instance()


# Workspace root from env or default
def _workspace_root() -> str:
    settings = storage.get_settings()
    return settings.get('workspace_root', os.getenv('WORKSPACE_BASE', './workspace'))


class ExecRequest(BaseModel):
    command: str
    working_dir: str | None = None
    timeout: float = Field(default=30.0, ge=1, le=120)


class RunScriptRequest(BaseModel):
    language: str
    code: str
    working_dir: str | None = None
    timeout: float = Field(default=60.0, ge=1, le=300)


@router.post('/terminal/exec')
async def execute_command(req: ExecRequest) -> dict[str, Any]:
    """Execute a shell command in the workspace sandbox."""
    root = _workspace_root()
    work_dir = req.working_dir or root

    # Ensure working_dir is under workspace root
    abs_work = os.path.realpath(os.path.join(root, work_dir))
    abs_root = os.path.realpath(root)
    if not abs_work.startswith(abs_root):
        raise HTTPException(
            status_code=400,
            detail='Working directory must be within the workspace',
        )

    result = await exec_command(
        command=req.command,
        working_dir=abs_work,
        workspace_root=abs_root,
        timeout=req.timeout,
    )
    return result


@router.post('/terminal/run')
async def run_code(req: RunScriptRequest) -> dict[str, Any]:
    """Run a code snippet in the appropriate runtime."""
    root = _workspace_root()
    work_dir = req.working_dir or root

    abs_work = os.path.realpath(os.path.join(root, work_dir))
    abs_root = os.path.realpath(root)
    if not abs_work.startswith(abs_root):
        raise HTTPException(
            status_code=400,
            detail='Working directory must be within the workspace',
        )

    result = await run_script(
        language=req.language,
        code=req.code,
        working_dir=abs_work,
        workspace_root=abs_root,
        timeout=req.timeout,
    )
    return result
