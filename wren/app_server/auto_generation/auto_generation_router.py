"""
REST API routes for the Automated Multi-File Generation Pipeline.

Wraps the AutomatedProjectGenerator (3-stage pipeline) as a background
task service with polling endpoints for real-time frontend progress.

Endpoints:
    POST   /api/v1/auto-generation/start        — Start a new generation pipeline
    GET    /api/v1/auto-generation/{task_id}/status  — Poll generation progress
    POST   /api/v1/auto-generation/{task_id}/cancel   — Cancel a running generation
    GET    /api/v1/auto-generation/projects          — List completed projects
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from wren.app_builder.automated_runner import (
    AutomatedProjectGenerator,
    ProjectResult,
    DEFAULT_MODEL,
    DEFAULT_OUTPUT_DIR,
)
from wren.app_server.config import get_default_persistence_dir
from wren.app_server.settings.provider_store import LLMProviderStore

_logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/auto-generation",
    tags=["auto-generation"],
)


# ── Request/Response Models ─────────────────────────────────────────────


class StartGenerationRequest(BaseModel):
    prompt: str = Field(description="High-level project directive")
    model: str = Field(default=DEFAULT_MODEL, description="LLM model name")
    base_url: str | None = Field(default=None, description="Custom API base URL")
    output_dir: str = Field(default=DEFAULT_OUTPUT_DIR, description="Output directory")
    max_tokens: int = Field(default=16384, description="Max tokens per LLM call")
    temperature: float = Field(default=0.2, description="LLM temperature")
    validate: bool = Field(default=True, description="Run validation & correction stage")
    resume: bool = Field(default=True, description="Resume from saved state if available")


class StartGenerationResponse(BaseModel):
    task_id: str
    project_name: str
    status: str


class GenerationProgress(BaseModel):
    stage: int
    stage_name: str
    status: str
    detail: str = ""
    file_index: int = 0
    file_total: int = 0
    file_path: str = ""


class GenerationStatusResponse(BaseModel):
    status: str
    progress: GenerationProgress | None = None
    result: dict[str, Any] | None = None
    error: str = ""


class CancelResponse(BaseModel):
    success: bool


class ProjectListItem(BaseModel):
    project_name: str
    output_dir: str
    created_at: str
    file_count: int
    success: bool


class ProjectListResponse(BaseModel):
    items: list[ProjectListItem]


# ── In-memory task store ────────────────────────────────────────────────


@dataclass
class GenerationTask:
    """Represents a running or completed generation task."""

    task_id: str
    prompt: str
    project_name: str
    model: str
    status: str  # "queued" | "running" | "done" | "error" | "cancelled"
    created_at: float
    progress: GenerationProgress | None = None
    result: dict[str, Any] | None = None
    error: str = ""
    api_key: str = ""
    base_url: str | None = None
    output_dir: str = DEFAULT_OUTPUT_DIR
    max_tokens: int = 16384
    temperature: float = 0.2
    validate: bool = True
    resume: bool = True
    _cancel_event: asyncio.Event = field(default_factory=asyncio.Event)


class TaskStore:
    """Thread-safe in-memory store for generation tasks."""

    def __init__(self) -> None:
        self._tasks: dict[str, GenerationTask] = {}
        self._lock = asyncio.Lock()

    async def add(self, task: GenerationTask) -> None:
        async with self._lock:
            self._tasks[task.task_id] = task

    async def get(self, task_id: str) -> GenerationTask | None:
        async with self._lock:
            return self._tasks.get(task_id)

    async def update_status(
        self, task_id: str, status: str, error: str = ""
    ) -> None:
        async with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = status
                if error:
                    self._tasks[task_id].error = error

    async def update_progress(self, task_id: str, progress: GenerationProgress) -> None:
        async with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].progress = progress

    async def update_result(self, task_id: str, result: dict[str, Any]) -> None:
        async with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].result = result
                self._tasks[task_id].status = "done"

    async def cancel(self, task_id: str) -> bool:
        async with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status in ("queued", "running"):
                task._cancel_event.set()
                task.status = "cancelled"
                return True
            return False

    async def list_completed(self) -> list[ProjectListItem]:
        async with self._lock:
            items = []
            for task in self._tasks.values():
                if task.status in ("done", "error", "cancelled"):
                    items.append(
                        ProjectListItem(
                            project_name=task.project_name,
                            output_dir=Path(task.output_dir, task.project_name).as_posix(),
                            created_at=time.strftime(
                                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(task.created_at)
                            ),
                            file_count=len(task.result.get("files", []))
                            if task.result
                            else 0,
                            success=task.status == "done",
                        )
                    )
            return sorted(items, key=lambda x: x.created_at, reverse=True)


_store = TaskStore()


# ── Background runner ───────────────────────────────────────────────────


async def _run_generation(task_id: str) -> None:
    """Execute the 3-stage pipeline in the background with progress tracking."""
    task = await _store.get(task_id)
    if not task:
        return

    try:
        await _store.update_status(task_id, "running")

        # Create progress callback that writes to the task store
        async def _progress_callback(
            stage_index: int,
            stage_name: str,
            status: str,
            detail: str = "",
            file_index: int = 0,
            file_total: int = 0,
            file_path: str = "",
        ) -> None:
            # Check if cancelled
            if task._cancel_event.is_set():
                raise asyncio.CancelledError("Task cancelled by user")

            progress = GenerationProgress(
                stage=stage_index,
                stage_name=stage_name,
                status=status,
                detail=detail,
                file_index=file_index,
                file_total=file_total,
                file_path=file_path,
            )
            await _store.update_progress(task_id, progress)

        # Build a runner that reports progress via callback to our store
        runner = AutomatedProjectGenerator(
            api_key=task.api_key,
            model=task.model,
            base_url=task.base_url,
            output_dir=task.output_dir,
            max_tokens=task.max_tokens,
            temperature=task.temperature,
            validate=task.validate,
            resume=task.resume,
            progress_callback=_progress_callback,
        )

        result = await runner.run(task.prompt)
        await runner.close()

        # Convert result to dict for JSON serialization
        result_dict = {
            "success": result.success,
            "prompt": result.prompt,
            "project_name": result.project_name,
            "output_dir": result.output_dir,
            "files": [
                {
                    "path": f.path,
                    "success": f.success,
                    "error": f.error,
                }
                for f in result.files
            ],
            "stages": [
                {
                    "name": s.name,
                    "index": i + 1,
                    "total": len(result.stages),
                    "status": "done" if s.success else "error",
                    "detail": s.detail,
                    "duration_s": s.duration_s,
                    "success": s.success,
                }
                for i, s in enumerate(result.stages)
            ],
            "total_duration_s": result.total_duration_s,
            "error": result.error,
        }

        await _store.update_result(task_id, result_dict)

        # Update progress one last time as done
        await _store.update_progress(
            task_id,
            GenerationProgress(
                stage=3,
                stage_name="Complete",
                status="done",
                detail=f"Generated {len(result.files)} files in {result.total_duration_s:.1f}s",
                file_total=len(result.files),
            ),
        )

    except asyncio.CancelledError:
        await _store.update_status(task_id, "cancelled")
    except Exception as e:
        _logger.exception("Generation task %s failed", task_id)
        await _store.update_status(task_id, "error", str(e))
        await _store.update_progress(
            task_id,
            GenerationProgress(
                stage=0,
                stage_name="Error",
                status="error",
                detail=str(e)[:200],
            ),
        )


# ── Routes ──────────────────────────────────────────────────────────────


@router.post("/start", response_model=StartGenerationResponse)
async def start_generation(request: StartGenerationRequest) -> StartGenerationResponse:
    """
    Start a new automated multi-file generation pipeline.

    Returns a task_id immediately. Progress can be polled via GET /status.
    """
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    # Read API key from LLMProviderStore (same pattern as harness_router.py)
    api_key = ""
    try:
        store = LLMProviderStore.get_instance(get_default_persistence_dir())
        api_keys = await store.get_api_keys_map()
        if api_keys:
            # Use the first available API key
            api_key = next(iter(api_keys.values()), "")
    except Exception:
        _logger.warning("Could not load API keys from provider store")

    task_id = f"gen-{uuid.uuid4().hex[:12]}"
    project_name = request.prompt.split()[0].strip(".,!?").capitalize() if request.prompt.split() else "Project"

    task = GenerationTask(
        task_id=task_id,
        prompt=request.prompt,
        project_name=project_name,
        model=request.model,
        status="queued",
        created_at=time.time(),
        api_key=api_key,
        base_url=request.base_url,
        output_dir=request.output_dir,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        validate=request.validate,
        resume=request.resume,
    )

    await _store.add(task)

    # Launch background task
    asyncio.create_task(_run_generation(task_id))

    _logger.info("Generation task %s started: %.80s", task_id, request.prompt)

    return StartGenerationResponse(
        task_id=task_id,
        project_name=project_name,
        status="queued",
    )


@router.get("/{task_id}/status", response_model=GenerationStatusResponse)
async def get_generation_status(task_id: str) -> GenerationStatusResponse:
    """Poll generation progress for a given task."""
    task = await _store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return GenerationStatusResponse(
        status=task.status,
        progress=task.progress,
        result=task.result,
        error=task.error,
    )


@router.post("/{task_id}/cancel", response_model=CancelResponse)
async def cancel_generation(task_id: str) -> CancelResponse:
    """Cancel a running or queued generation task."""
    success = await _store.cancel(task_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found or already completed",
        )
    return CancelResponse(success=True)


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects() -> ProjectListResponse:
    """List all completed generation projects."""
    items = await _store.list_completed()
    return ProjectListResponse(items=items)
