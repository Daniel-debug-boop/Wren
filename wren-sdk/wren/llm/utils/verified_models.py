"""Verified models for Wren LLM.

These are the single source of truth for which models/prompts/providers
are considered verified/known-good.  Imported by the app server,
hosted-mode model discovery, and the CLI model selector.

Structure mirrors the old ``openhands.sdk.llm.utils.verified_models``
module to keep the migration zero-touch.
"""

from __future__ import annotations

# ── Provider-keyed groups (used for bare-name pre assignment in llm.py) ──

VERIFIED_OPENAI_MODELS: list[str] = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
    "o1",
    "o1-mini",
    "o3-mini",
]

VERIFIED_ANTHROPIC_MODELS: list[str] = [
    "claude-3-5-sonnet-20240620",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
]

VERIFIED_MISTRAL_MODELS: list[str] = [
    "mistral-large-latest",
    "mistral-small-latest",
    "open-mistral-7b",
]

VERIFIED_WREN_MODELS: list[str] = [
    "claude-sonnet-4-20250514",
    "gpt-5.2",
    "gpt-5.1",
    "gpt-5-mini-3.1",
    "gemini-2.5-flash-8b",
    "gemini-2.5-pro-0325",
    "minimax-m2.7",
    "amazon-nova-lite-v1.0",
]

# ── Flat verified model list (for UI / CLI) ──

VERIFIED_MODELS: dict[str, list[str]] = {
    "openai": VERIFIED_OPENAI_MODELS,
    "anthropic": VERIFIED_ANTHROPIC_MODELS,
    "mistral": VERIFIED_MISTRAL_MODELS,
    "wren": VERIFIED_WREN_MODELS,
}


__all__ = [
    "VERIFIED_MODELS",
    "VERIFIED_OPENAI_MODELS",
    "VERIFIED_ANTHROPIC_MODELS",
    "VERIFIED_MISTRAL_MODELS",
    "VERIFIED_WREN_MODELS",
]
