"""User information API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1", tags=["users"])
auth_service = AuthService()


def _get_token(request: Request) -> str | None:
    """Extract Bearer token from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


@router.get("/users/me")
async def get_current_user(request: Request):
    token = _get_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = auth_service.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user
