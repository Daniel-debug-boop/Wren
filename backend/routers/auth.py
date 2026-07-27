"""Authentication API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from backend.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1", tags=["auth"])
auth_service = AuthService()


@router.post("/auth/login")
async def login(body: dict[str, Any]):
    username = body.get("username", "")
    password = body.get("password", "")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    result = auth_service.login(username, password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return result


@router.post("/auth/register")
async def register(body: dict[str, Any]):
    username = body.get("username", "")
    password = body.get("password", "")
    email = body.get("email")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    result = auth_service.register(username, password, email)
    if not result:
        raise HTTPException(status_code=409, detail="Username already taken")
    return result


@router.post("/auth/logout")
async def logout():
    return {"success": True, "message": "Logged out"}
