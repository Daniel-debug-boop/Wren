"""API Keys management endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.services.storage import Storage

router = APIRouter(prefix="/api/v1", tags=["api-keys"])
storage = Storage.get_instance()


@router.get("/api-keys")
async def list_api_keys():
    return storage.get_api_keys()


@router.post("/api-keys")
async def create_api_key(body: dict[str, Any]):
    name = body.get("name", "Default Key")
    return storage.create_api_key(name)


@router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str):
    if storage.delete_api_key(key_id):
        return {"success": True}
    raise HTTPException(status_code=404, detail="API key not found")
