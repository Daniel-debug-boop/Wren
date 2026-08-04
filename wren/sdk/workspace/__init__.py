"""Compatibility bridge for ``wren.sdk.workspace``.

Re-exports the workspace abstractions from their actual location in
:mod:`wren.workspace.workspace`.
"""

from __future__ import annotations

from wren.workspace.workspace import (
    FileOperationResult,
    LocalWorkspace,
    Workspace,
)

__all__ = ['FileOperationResult', 'LocalWorkspace', 'Workspace']
