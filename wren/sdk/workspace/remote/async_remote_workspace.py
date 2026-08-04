"""Compatibility bridge for ``wren.sdk.workspace.remote.async_remote_workspace``.

Re-exports :class:`AsyncRemoteWorkspace` from its actual location in
:mod:`wren.workspace.remote`.
"""

from __future__ import annotations

from wren.workspace.remote import AsyncRemoteWorkspace

__all__ = ['AsyncRemoteWorkspace']
