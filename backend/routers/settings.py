"""Settings and LLM profile management API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.services.storage import Storage

router = APIRouter(prefix="/api/v1", tags=["settings"])
storage = Storage.get_instance()


@router.get("/settings")
async def get_settings():
    return storage.get_settings()


@router.post("/settings")
async def update_settings(settings: dict[str, Any]):
    return storage.save_settings(settings)


@router.put("/settings")
async def put_settings(settings: dict[str, Any]):
    return storage.save_settings(settings)


@router.get("/settings/profiles")
async def get_profiles():
    return storage.get_profiles()


@router.post("/settings/profiles/{name}")
async def create_profile(name: str, config: dict[str, Any]):
    return storage.create_profile(name, config)


@router.delete("/settings/profiles/{name}")
async def delete_profile(name: str):
    if storage.delete_profile(name):
        return {"success": True}
    raise HTTPException(status_code=404, detail="Profile not found")


@router.post("/settings/profiles/{name}/activate")
async def activate_profile(name: str):
    if storage.activate_profile(name):
        return {"success": True, "active_profile": name}
    raise HTTPException(status_code=404, detail="Profile not found")
