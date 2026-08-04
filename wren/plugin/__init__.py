"""Plugin system for Wren."""

from __future__ import annotations

import urllib.parse

from pydantic import BaseModel, Field, field_serializer


def redact_source_credentials(source: str) -> str:
    """Redact URL userinfo credentials (``user:pass@``) from a plugin source.

    Only URLs that carry userinfo are touched; non-URL sources
    (``github:owner/repo``, local paths) and clean URLs pass through
    unchanged. The raw value stays available via ``PluginSource.source`` —
    only serialization (``model_dump`` / ``model_dump_json``) is redacted so
    credentials never leak into logs or API responses.
    """
    try:
        parts = urllib.parse.urlsplit(source)
    except ValueError:
        return source

    if parts.username is None and parts.password is None:
        return source

    netloc = '****'
    if parts.hostname:
        netloc = f'****@{parts.hostname}'
        if parts.port:
            netloc += f':{parts.port}'

    return urllib.parse.urlunsplit(
        (parts.scheme, netloc, parts.path, parts.query, parts.fragment)
    )


class PluginSource(BaseModel):
    """Source specification for loading a plugin.

    ``PluginSpec`` in the app server extends this type with user-provided
    configuration parameters. Kept as a plain pydantic model (not an enum)
    because a plugin source is an arbitrary string like
    ``github:owner/repo`` or a local path, and Python 3.12 forbids
    subclassing an enum that already has members.
    """

    source: str
    ref: str | None = Field(
        default=None,
        description='Optional git ref/tag/commit to load the plugin from.',
    )
    repo_path: str | None = Field(
        default=None,
        description='Optional local path to the plugin repository.',
    )

    @field_serializer('source')
    def _serialize_source(self, source: str) -> str:
        """Serialize ``source`` with URL credentials redacted."""
        return redact_source_credentials(source)


__all__ = ['PluginSource']
