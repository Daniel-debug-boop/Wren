"""AI Generation Pipeline API.

Implements the Architect -> Planner -> Writer -> Reviewer pipeline
using OpenRouter API for LLM-powered code generation.

Now writes extracted files to the workspace directory.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from backend.services.storage import Storage
from backend.services.llm_service import LLMService
from backend.services.code_extractor import extract_and_write_files

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["generation"])
storage = Storage.get_instance()

# In-memory task store (could be persisted)
_tasks: dict[str, dict[str, Any]] = {}


def _get_llm_service() -> LLMService:
    """Get LLM service with configured API key."""
    secrets = storage.get_secrets()
    api_key = secrets.get("OPENROUTER_API_KEY", "") or secrets.get("api_key", "")
    settings = storage.get_settings()
    llm_config = settings.get("llm_config", {})
    base_url = llm_config.get("base_url") or "https://openrouter.ai/api/v1"
    return LLMService(api_key=api_key, base_url=base_url)


def _workspace_root() -> str:
    """Get the workspace root directory."""
    settings = storage.get_settings()
    return settings.get('workspace_root', os.getenv('WORKSPACE_BASE', './workspace'))


@router.get("/auto-generations")
async def list_generations() -> list[dict[str, Any]]:
    """List all generation tasks."""
    return [
        {
            'task_id': t['task_id'],
            'status': t['status'],
            'prompt': t.get('prompt', ''),
            'created_at': t.get('created_at', ''),
            'model': t.get('model', ''),
        }
        for t in _tasks.values()
    ]


@router.post("/auto-generations")
async def start_generation(req: dict[str, Any]):
    """Start an AI generation task."""
    prompt = req.get("prompt", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    model = req.get("model") or storage.get_settings().get("llm_config", {}).get(
        "model", "openai/gpt-4o-mini"
    )
    validate = req.get("validate", True)

    task_id = uuid4().hex[:12]
    task = {
        "task_id": task_id,
        "status": "queued",
        "prompt": prompt,
        "model": model,
        "validate": validate,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "stages": [],
        "error": None,
    }
    _tasks[task_id] = task

    # Launch background processing
    asyncio.create_task(_run_pipeline(task_id, prompt, model, validate))

    return {"task_id": task_id, "status": "queued"}


async def _run_pipeline(
    task_id: str, prompt: str, model: str, validate: bool
) -> None:
    """Run the full generation pipeline in the background."""
    llm = _get_llm_service()

    if not llm.is_configured():
        _tasks[task_id]["status"] = "error"
        _tasks[task_id]["error"] = (
            "No OpenRouter API key configured. "
            "Add your key in Settings > API Keys or as OPENROUTER_API_KEY secret."
        )
        return

    try:
        # Stage 1: Architect
        _update_task(task_id, "architect", "Designing system architecture...")
        arch_result = await llm.architect(prompt, model)
        if not arch_result.get("success"):
            _fail_task(task_id, arch_result.get("error", "Architect stage failed"))
            return
        _update_task(task_id, "architect", "Architecture complete", 25)

        # Stage 2: Planner
        _update_task(task_id, "planner", "Creating implementation plan...")
        plan_result = await llm.planner(arch_result["content"], model)
        if not plan_result.get("success"):
            _fail_task(task_id, plan_result.get("error", "Planner stage failed"))
            return
        _update_task(task_id, "planner", "Implementation plan ready", 50)

        # Stage 3: Writer
        _update_task(task_id, "writer", "Generating code...")
        code_result = await llm.writer(plan_result["content"], model)
        if not code_result.get("success"):
            _fail_task(task_id, code_result.get("error", "Writer stage failed"))
            return
        _update_task(task_id, "writer", "Code generation complete", 75)

        # Stage 4: Reviewer (optional)
        review_result = None
        if validate:
            _update_task(task_id, "reviewer", "Reviewing generated code...")
            review_result = await llm.reviewer(code_result["content"], model)
            _update_task(task_id, "reviewer", "Code review complete", 100)
        else:
            _update_task(task_id, "reviewer", "Skipped (validation off)", 100)

        # Stage 5: Write files to workspace
        code_content = code_result.get("content", "")
        _update_task(task_id, "writer", "Writing files to workspace...")
        write_result = extract_and_write_files(
            text=code_content,
            workspace_root=_workspace_root(),
            project_subdir=f"generated/{task_id}",
        )
        _logger.info(
            'Pipeline wrote %d files (%d lines) for task %s',
            write_result['total_files'],
            write_result['total_lines'], task_id,
        )

        # Finalize
        _tasks[task_id]["status"] = "completed"
        _tasks[task_id]["result"] = {
            "success": True,
            "architecture": arch_result.get("content", ""),
            "plan": plan_result.get("content", ""),
            "code": code_result.get("content", ""),
            "review": review_result.get("content") if review_result else None,
            "model": model,
            "files": write_result.get("files", []),
            "total_files": write_result.get("total_files", 0),
            "total_lines": write_result.get("total_lines", 0),
            "project_path": f"generated/{task_id}",
            "write_errors": write_result.get("errors", []),
        }

    except Exception as e:
        _logger.exception(f"Pipeline failed for task {task_id}")
        _fail_task(task_id, str(e))


def _update_task(
    task_id: str, stage: str, message: str, progress: int = 0
) -> None:
    if task_id not in _tasks:
        return
    _tasks[task_id]["status"] = "running"
    _tasks[task_id]["current_stage"] = stage
    _tasks[task_id]["progress"] = progress
    _tasks[task_id]["message"] = message
    _tasks[task_id]["stages"].append(
        {
            "stage": stage,
            "message": message,
            "progress": progress,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


def _fail_task(task_id: str, error: str) -> None:
    if task_id not in _tasks:
        return
    _tasks[task_id]["status"] = "error"
    _tasks[task_id]["error"] = error
    _tasks[task_id]["progress"] = 0


@router.get("/auto-generations/{task_id}/status")
async def get_generation_status(task_id: str):
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task["task_id"],
        "status": task["status"],
        "progress": task.get("progress", 0),
        "message": task.get("message", ""),
        "stage": task.get("current_stage", ""),
        "error": task.get("error"),
    }


@router.get("/auto-generations/{task_id}/result")
async def get_generation_result(task_id: str):
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Task is {task['status']}, not completed yet",
        )
    result = task.get("result", {})
    return {
        "success": result.get("success", False),
        "files": result.get("files", []),
        "total_files": result.get("total_files", 0),
        "total_lines": result.get("total_lines", 0),
        "project_path": result.get("project_path"),
        "error": result.get("error"),
        "write_errors": result.get("write_errors", []),
        "architecture": result.get("architecture", ""),
        "plan": result.get("plan", ""),
        "code": result.get("code", ""),
        "review": result.get("review"),
    }
