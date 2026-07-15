"""API router for LLM provider configuration (Model Router integration).

These endpoints allow the frontend to manage LLM provider API keys and
model selections, which are then used by the ModelRouter to auto-select
the best model for each agent role (Planner → Researcher → Writer → Reviewer).

Endpoints:
  GET    /api/v1/settings/llm-providers          — List all configured providers
  PUT    /api/v1/settings/llm-providers           — Save/replace all providers
  DELETE /api/v1/settings/llm-providers/{provider} — Remove a provider
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status

from wren.app_server.settings.provider_store import LLMProviderStore

_logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/settings/llm-providers',
    tags=['LLM Providers'],
)


def _get_provider_store() -> LLMProviderStore:
    """Get the default provider store instance."""
    from wren.app_server.config import get_default_persistence_dir

    return LLMProviderStore.get_instance(get_default_persistence_dir())


@router.get('')
async def list_providers() -> list[dict[str, Any]]:
    """List all configured LLM providers.

    Returns a list of provider configs with API keys **masked** (first 8 chars
    shown, rest replaced with '...').

    Example response:
    ```json
    [
        {
            "provider": "openai",
            "model": "gpt-4o",
            "api_key": "sk-abc123...",
            "base_url": null,
            "updated_at": 1700000000
        }
    ]
    ```
    """
    store = _get_provider_store()
    data = await store.load()

    results = []
    for prov, cfg in data.items():
        entry = dict(cfg)
        api_key = entry.get('api_key', '')
        if api_key and len(api_key) > 12:
            entry['api_key'] = api_key[:8] + '...'
        elif api_key:
            entry['api_key'] = '***'
        results.append(entry)

    return results


@router.put('')
async def save_providers(
    providers: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Save all LLM provider configurations (replaces existing).

    Accepts a dict keyed by provider name:
    ```json
    {
        "openai": {
            "provider": "openai",
            "model": "gpt-4o",
            "api_key": "sk-...",
            "base_url": null
        }
    }
    ```

    Returns the count of providers saved.
    """
    store = _get_provider_store()

    # Validate minimal structure
    for provider, cfg in providers.items():
        if 'api_key' not in cfg and provider != 'ollama':
            continue  # Allow keyless configs for local providers

    await store.save_all(providers)
    count = len(providers)
    _logger.info('Saved %d LLM provider configs', count)

    return {
        'message': f'{count} provider(s) saved',
        'count': count,
    }


@router.delete('/{provider}')
async def delete_provider(provider: str) -> dict[str, Any]:
    """Remove a single provider configuration.

    Returns 404 if the provider was not configured.
    """
    store = _get_provider_store()
    existed = await store.delete(provider)

    if not existed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider}' not found",
        )

    _logger.info('Removed LLM provider config: %s', provider)
    return {
        'message': f"Provider '{provider}' removed",
        'provider': provider,
    }


@router.get('/api-keys')
async def get_api_keys() -> dict[str, str]:
    """Get the provider → API key mapping for the Model Router.

    Returns the raw API keys (needed by the MetaOrchestrator to configure
    the ModelRouter). This endpoint is intentionally separate from the
    list endpoint so it can be called by backend services without exposing
    full provider configs to the frontend.

    Example response:
    ```json
    {
        "openai": "sk-abc123...",
        "anthropic": "sk-ant-..."
    }
    ```
    """
    store = _get_provider_store()
    return await store.get_api_keys_map()
