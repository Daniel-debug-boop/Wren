"""Skills management API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.services.storage import Storage

router = APIRouter(prefix="/api/v1", tags=["skills"])
storage = Storage.get_instance()


@router.get("/skills")
async def list_skills():
    return storage.get_skills()


@router.post("/skills/{name}/toggle")
async def toggle_skill(name: str, body: dict[str, Any]):
    enabled = body.get("enabled", True)
    result = storage.toggle_skill(name, enabled)
    if not result:
        raise HTTPException(status_code=404, detail="Skill not found")
    return result
