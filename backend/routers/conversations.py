"""Conversations API for managing chat conversations."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.services.storage import Storage

router = APIRouter(prefix="/api/v1", tags=["conversations"])
storage = Storage.get_instance()


@router.get("/conversations")
async def list_conversations():
    return storage.get_conversations()


@router.post("/conversations")
async def create_conversation(body: dict[str, Any] | None = None):
    title = body.get("title") if body else None
    return storage.create_conversation(title)


@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    conv = storage.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    if storage.delete_conversation(conv_id):
        return {"success": True}
    raise HTTPException(status_code=404, detail="Conversation not found")


@router.get("/conversations/{conv_id}/messages")
async def get_messages(conv_id: str):
    if not storage.get_conversation(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return storage.get_messages(conv_id)


@router.post("/conversations/{conv_id}/messages")
async def send_message(conv_id: str, body: dict[str, Any]):
    if not storage.get_conversation(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    content = body.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    return storage.add_message(conv_id, "user", content)
