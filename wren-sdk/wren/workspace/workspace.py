"""Workspace abstraction for Wren SDK.

Provides file system access for agents.
"""

from __future__ import annotations

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from wren.utils.models import WrenModel


class FileOperationResult(WrenModel):
    """Result of a file operation."""

    success: bool
    path: str
    content: str | None = None
    error: str | None = None
    bytes_written: int | None = None


class Workspace(ABC):
    """Base workspace class.

    Provides file system access for agents.
    """

    @abstractmethod
    def get_root(self) -> Path:
        """Get workspace root directory."""
        ...

    @abstractmethod
    async def read_file(self, path: str) -> FileOperationResult:
        """Read a file."""
        ...

    @abstractmethod
    async def write_file(self, path: str, content: str) -> FileOperationResult:
        """Write to a file."""
        ...

    @abstractmethod
    async def edit_file(self, path: str, old_text: str, new_text: str) -> FileOperationResult:
        """Edit a file (surgical replacement)."""
        ...

    @abstractmethod
    async def list_directory(self, path: str = ".") -> list[str]:
        """List directory contents."""
        ...

    @abstractmethod
    async def glob(self, pattern: str) -> list[str]:
        """Find files matching pattern."""
        ...

    @abstractmethod
    async def grep(self, pattern: str, path: str = ".") -> list[dict[str, Any]]:
        """Search file contents."""
        ...

    def resolve_path(self, path: str) -> Path:
        """Resolve a path relative to workspace root."""
        root = self.get_root()
        return (root / path).resolve()


class LocalWorkspace(Workspace):
    """Local file system workspace."""

    def __init__(self, root: str | Path):
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def get_root(self) -> Path:
        return self._root

    async def read_file(self, path: str) -> FileOperationResult:
        """Read a file."""
        try:
            file_path = self.resolve_path(path)
            content = file_path.read_text(encoding="utf-8")
            return FileOperationResult(
                success=True,
                path=str(file_path),
                content=content,
            )
        except Exception as e:
            return FileOperationResult(
                success=False,
                path=path,
                error=str(e),
            )

    async def write_file(self, path: str, content: str) -> FileOperationResult:
        """Write to a file."""
        try:
            file_path = self.resolve_path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return FileOperationResult(
                success=True,
                path=str(file_path),
                bytes_written=len(content.encode("utf-8")),
            )
        except Exception as e:
            return FileOperationResult(
                success=False,
                path=path,
                error=str(e),
            )

    async def edit_file(self, path: str, old_text: str, new_text: str) -> FileOperationResult:
        """Edit a file (surgical replacement)."""
        try:
            file_path = self.resolve_path(path)
            content = file_path.read_text(encoding="utf-8")

            if old_text not in content:
                return FileOperationResult(
                    success=False,
                    path=str(file_path),
                    error="Old text not found in file",
                )

            new_content = content.replace(old_text, new_text, 1)
            file_path.write_text(new_content, encoding="utf-8")

            return FileOperationResult(
                success=True,
                path=str(file_path),
                bytes_written=len(new_content.encode("utf-8")),
            )
        except Exception as e:
            return FileOperationResult(
                success=False,
                path=path,
                error=str(e),
            )

    async def list_directory(self, path: str = ".") -> list[str]:
        """List directory contents."""
        try:
            dir_path = self.resolve_path(path)
            return [entry.name + ("/" if entry.is_dir() else "") for entry in dir_path.iterdir()]
        except Exception as e:
            return []

    async def glob(self, pattern: str) -> list[str]:
        """Find files matching pattern."""
        try:
            root = self.get_root()
            return [str(p.relative_to(root)) for p in root.glob(pattern) if p.is_file()]
        except Exception as e:
            return []

    async def grep(self, pattern: str, path: str = ".") -> list[dict[str, Any]]:
        """Search file contents."""
        import re

        results = []
        try:
            dir_path = self.resolve_path(path)
            regex = re.compile(pattern)

            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        for i, line in enumerate(content.splitlines(), 1):
                            if regex.search(line):
                                results.append(
                                    {
                                        "file": str(file_path.relative_to(self.get_root())),
                                        "line": i,
                                        "content": line.strip(),
                                    }
                                )
                    except (UnicodeDecodeError, PermissionError):
                        continue

            return results
        except Exception as e:
            return []
