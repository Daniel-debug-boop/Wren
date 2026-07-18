"""Remote workspace implementations for Wren."""

from __future__ import annotations

import httpx
from pathlib import Path
from typing import Any

from wren.workspace.workspace import Workspace, FileOperationResult


class RemoteWorkspace(Workspace):
    """Base remote workspace."""

    def __init__(self, host: str, api_key: str):
        self.host = host
        self.api_key = api_key
        self._client = httpx.Client(
            base_url=host,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
        )

    def get_root(self) -> Path:
        return Path("/workspace")


class AsyncRemoteWorkspace(RemoteWorkspace):
    """Async remote workspace implementation."""

    def __init__(self, host: str, api_key: str):
        super().__init__(host, api_key)
        self._aclient: httpx.AsyncClient | None = None

    @property
    def aclient(self) -> httpx.AsyncClient:
        if self._aclient is None:
            self._aclient = httpx.AsyncClient(
                base_url=self.host,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
            )
        return self._aclient

    async def reset_client(self) -> None:
        """Reset the HTTP client."""
        if self._aclient is not None:
            await self._aclient.aclose()
            self._aclient = None

    async def read_file(self, path: str) -> FileOperationResult:
        """Read a file from remote workspace."""
        try:
            response = await self.aclient.get(f"/files/{path}")
            response.raise_for_status()
            return FileOperationResult(
                success=True,
                path=path,
                content=response.text,
            )
        except Exception as e:
            return FileOperationResult(
                success=False,
                path=path,
                error=str(e),
            )

    async def write_file(self, path: str, content: str) -> FileOperationResult:
        """Write a file to remote workspace."""
        try:
            response = await self.aclient.post(f"/files/{path}", content=content)
            response.raise_for_status()
            return FileOperationResult(
                success=True,
                path=path,
                bytes_written=len(content.encode("utf-8")),
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
            response = await self.aclient.get(f"/files/{path}")
            response.raise_for_status()
            data = response.json()
            return data.get("files", [])
        except Exception:
            return []


__all__ = ["RemoteWorkspace", "AsyncRemoteWorkspace"]
