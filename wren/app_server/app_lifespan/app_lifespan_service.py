from __future__ import annotations

from abc import ABC, abstractmethod

from fastapi import FastAPI

from wren.utils.models import DiscriminatedUnionMixin


class AppLifespanService(DiscriminatedUnionMixin, ABC):
    def lifespan(self, api: FastAPI) -> Any:
        """Return lifespan wrapper."""
        return self

    @abstractmethod
    async def __aenter__(self) -> None:
        """Open lifespan."""

    @abstractmethod
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Close lifespan."""
