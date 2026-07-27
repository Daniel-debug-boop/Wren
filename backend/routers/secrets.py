"""Secrets management API for API keys and credentials."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.services.storage import Storage

router = APIRouter(prefix="/api/v1", tags=["secrets"])
storage = Storage.get_instance()


@router.get("/secrets")
async def list_secrets():
    """List secret names (not values)."""
    secrets = storage.get_secrets()
    return [{"name": k} for k in secrets.keys()]


@router.post("/secrets")
async def set_secret(body: dict[str, Any]):
    name = body.get("name", "")
    value = body.get("value", "")
    if not name or not value:
        raise HTTPException(status_code=400, detail="name and value required")
    storage.set_secret(name, value)
    return {"success": True, "name": name}


@router.delete("/secrets/{name}")
async def delete_secret(name: str):
    if storage.delete_secret(name):
        return {"success": True}
    raise HTTPException(status_code=404, detail="Secret not found")
