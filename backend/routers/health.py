"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/v1/alive")
async def health_check():
    return {"status": "ok", "version": "1.0.0", "service": "wren-backend"}
