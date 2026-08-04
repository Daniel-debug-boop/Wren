"""Compatibility bridge for ``wren.sdk.secret``.

Re-exports the secret-source abstractions from their actual location in
:mod:`wren.secret`.
"""

from __future__ import annotations

from wren.secret import LookupSecret, SecretSource, SecretValue, StaticSecret

__all__ = ['LookupSecret', 'SecretSource', 'SecretValue', 'StaticSecret']
