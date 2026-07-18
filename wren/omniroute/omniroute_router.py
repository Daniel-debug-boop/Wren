"""FastAPI router for the OmniRoute system.

Exposes REST endpoints for managing and monitoring OmniRoute:
  GET    /api/v1/omniroute/status             — Full system status
  GET    /api/v1/omniroute/providers           — List configured providers
  GET    /api/v1/omniroute/combos              — List routing combos
  POST   /api/v1/omniroute/combos/auto-generate — Re-generate combos
  POST   /api/v1/omniroute/keys               — Add API key
  DELETE /api/v1/omniroute/keys/{provider}     — Remove API key
  GET    /api/v1/omniroute/costs              — Cost summary
  GET    /api/v1/omniroute/compression/stats  — Compression stats
  POST   /api/v1/omniroute/compress           — Compress text
  GET    /api/v1/omniroute/resilience         — Resilience status
  GET    /api/v1/omniroute/discovery          — Auto-discovery results
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from wren.omniroute import OmniRouter

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/omniroute", tags=["OmniRoute"])

# Singleton OmniRouter instance
_omnirouter: OmniRouter | None = None


def get_omnirouter() -> OmniRouter:
    """Get or create the OmniRouter singleton."""
    global _omnirouter
    if _omnirouter is None:
        _omnirouter = OmniRouter()
    return _omnirouter


# ── Request/Response Models ──────────────────────────────────────────────


class AddKeyRequest(BaseModel):
    provider: str = Field(description="Provider name (e.g., 'openai', 'anthropic')")
    api_key: str = Field(description="API key for the provider")


class CompressRequest(BaseModel):
    text: str = Field(description="Text to compress")
    aggressive: bool = Field(default=False, description="Apply aggressive compression")


class AutoGenerateRequest(BaseModel):
    api_keys: dict[str, str] = Field(
        description="Dict of provider -> api_key pairs"
    )


class StatusResponse(BaseModel):
    initialized: bool
    providers: dict[str, Any]
    combos: dict[str, Any]
    resilience: dict[str, Any]
    compression: dict[str, Any]
    cost_tracking: dict[str, Any]
    quota_sharing: dict[str, Any]
    discovery: dict[str, Any]


# ── Endpoints ────────────────────────────────────────────────────────────


@router.get("/status", response_model=StatusResponse)
async def get_status() -> dict[str, Any]:
    """Get complete OmniRoute system status."""
    router_instance = get_omnirouter()
    return router_instance.get_full_status()


@router.get("/providers")
async def list_providers() -> list[dict[str, Any]]:
    """List all configured providers with their details."""
    router_instance = get_omnirouter()
    return router_instance.get_provider_summary()


@router.get("/combos")
async def list_combos() -> list[dict[str, Any]]:
    """List all routing combos."""
    router_instance = get_omnirouter()
    return [
        {
            "name": c.name,
            "description": c.description,
            "steps": [
                {
                    "provider": s.provider,
                    "model": s.model,
                    "strategy": s.strategy.value,
                }
                for s in c.steps
            ],
            "fallback_strategy": c.fallback_strategy.value,
            "is_auto_generated": c.is_auto_generated,
        }
        for c in router_instance.combo_engine.list_combos()
    ]


@router.post("/combos/auto-generate")
async def auto_generate_combos(request: AutoGenerateRequest) -> dict[str, Any]:
    """Auto-generate routing combos from provided API keys."""
    router_instance = get_omnirouter()
    await router_instance.initialize(api_keys=request.api_keys)
    combos = router_instance.combo_engine.list_combos()
    return {
        "success": True,
        "combos_generated": len(combos),
        "combos": [c.name for c in combos],
        "providers": list(request.api_keys.keys()),
    }


@router.post("/keys")
async def add_api_key(request: AddKeyRequest) -> dict[str, Any]:
    """Add an API key and auto-configure everything.

    The system will:
    1. Detect the provider from the key prefix
    2. Auto-create routing combos
    3. Register with quota sharing

    The user just pastes the key — OmniRoute handles the rest.
    """
    router_instance = get_omnirouter()
    result = await router_instance.add_key(request.provider, request.api_key)
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to add key"),
        )
    return result


@router.delete("/keys/{provider}")
async def remove_api_key(provider: str) -> dict[str, Any]:
    """Remove an API key and rebuild combos."""
    router_instance = get_omnirouter()
    removed = await router_instance.remove_key(provider)
    if not removed:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider}' not found",
        )
    return {
        "success": True,
        "provider": provider,
        "message": f"Removed {provider} and rebuilt combos",
    }


@router.get("/costs")
async def get_costs() -> dict[str, Any]:
    """Get cost tracking summary."""
    router_instance = get_omnirouter()
    return router_instance.cost_tracker.session_summary()


@router.get("/compression/stats")
async def get_compression_stats() -> dict[str, Any]:
    """Get compression engine statistics."""
    router_instance = get_omnirouter()
    return router_instance.compression_engine.get_stats()


@router.post("/compress")
async def compress_text(request: CompressRequest) -> dict[str, Any]:
    """Compress text using OmniRoute's stacked compression engine."""
    router_instance = get_omnirouter()
    compressed = router_instance.compress(
        request.text, aggressive=request.aggressive
    )
    original_len = len(request.text)
    compressed_len = len(compressed)
    savings = ((original_len - compressed_len) / max(original_len, 1)) * 100
    return {
        "original_length": original_len,
        "compressed_length": compressed_len,
        "savings_percent": round(savings, 1),
        "compressed_text": compressed,
    }


@router.get("/resilience")
async def get_resilience_status() -> dict[str, Any]:
    """Get resilience system status."""
    router_instance = get_omnirouter()
    return {
        "stats": router_instance.resilience.stats(),
        "unavailable_providers": router_instance.resilience.get_unavailable_providers(),
        "active_lockouts": router_instance.resilience.get_active_lockouts(),
        "active_cooldowns": router_instance.resilience.get_active_cooldowns(),
    }


@router.get("/discovery")
async def get_discovery_results() -> dict[str, Any]:
    """Get auto-discovery results — what providers/keys were detected."""
    router_instance = get_omnirouter()
    return {
        "providers": router_instance.auto_discovery.get_provider_summary(),
        "keys_count": len(router_instance.auto_discovery.get_discovered_keys()),
        "combos": [
            {
                "name": c.name,
                "steps": len(c.steps),
            }
            for c in router_instance.combo_engine.list_combos()
        ],
    }


@router.post("/initialize")
async def initialize_omniroute(
    api_keys: dict[str, str] = {},
    enable_compression: bool = True,
) -> dict[str, Any]:
    """Initialize OmniRoute with API keys.

    This is the one-stop setup: pass all your API keys and the system
    auto-configures everything — routing, combos, resilience, compression.
    """
    router_instance = get_omnirouter()
    result = await router_instance.initialize(
        api_keys=api_keys or None,
        enable_compression=enable_compression,
    )
    return result
