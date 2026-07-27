"""Wren Backend — Production FastAPI Server.

Serves all API endpoints that the frontend needs.
Start with: uvicorn backend.main:app --host 0.0.0.0 --port 3000
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.routers import (
    api_keys,
    auth,
    conversations,
    generation,
    health,
    secrets,
    settings,
    skills,
    users,
)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
_logger = logging.getLogger("wren-backend")

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Wren AI Backend",
    description="Production backend for Wren AI — code generation, conversations, and LLM management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global Error Handler ─────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    _logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )

# ── Include Routers ──────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(settings.router)
app.include_router(secrets.router)
app.include_router(conversations.router)
app.include_router(generation.router)
app.include_router(auth.router)
app.include_router(api_keys.router)
app.include_router(skills.router)
app.include_router(users.router)

# ── Startup Event ────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    _logger.info("Wren backend starting on port %s", os.environ.get("PORT", "3000"))


# ── Direct Run ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "3000"))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
