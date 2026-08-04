"""Compatibility bridge for ``wren.sdk.settings.model``.

Re-exports the settings sub-models from their actual location in
:mod:`wren.settings.model`.
"""

from __future__ import annotations

from wren.settings.model import (
    AGENT_SETTINGS_SCHEMA_VERSION,
    CondenserSettings,
    VerificationSettings,
)

__all__ = [
    'AGENT_SETTINGS_SCHEMA_VERSION',
    'CondenserSettings',
    'VerificationSettings',
]
