"""Compatibility bridge for ``wren.sdk.workspace.remote``.

Re-exports the remote workspace implementations from their actual location
in :mod:`wren.workspace.remote`.
"""

from __future__ import annotations

from wren.workspace.remote import AsyncRemoteWorkspace, RemoteWorkspace

__all__ = ['AsyncRemoteWorkspace', 'RemoteWorkspace']
