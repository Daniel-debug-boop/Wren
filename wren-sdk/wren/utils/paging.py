"""Pagination utilities for API responses."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Callable, TypeVar

T = TypeVar('T')


async def page_iterator(
    fetch_page: Callable[..., Any],
    page_size: int = 100,
    max_pages: int | None = None,
    **fetch_kwargs: Any,
) -> AsyncIterator[T]:
    """Iterate over cursor-paginated API results.

    Args:
        fetch_page: An async callable that accepts ``page_id`` (plus any
            extra keyword arguments supplied via ``fetch_kwargs``) and returns
            a page object exposing ``items`` and ``next_page_id`` (or a plain
            list, in which case iteration stops after the first page).
        page_size: Kept for backward compatibility; callers that need a page
            size should pass it explicitly (e.g. ``limit=``) in
            ``fetch_kwargs``.
        max_pages: Maximum number of pages to fetch. None for unlimited.
        **fetch_kwargs: Extra keyword arguments forwarded to ``fetch_page``.

    Yields:
        Individual items from each page.
    """
    page_id: str | None = None
    pages_fetched = 0

    while True:
        if max_pages is not None and pages_fetched >= max_pages:
            break

        result = await fetch_page(page_id=page_id, **fetch_kwargs)
        if result is None:
            break

        if isinstance(result, (list, tuple)):
            items = list(result)
            next_page_id = None
        else:
            items = list(getattr(result, 'items', []) or [])
            next_page_id = getattr(result, 'next_page_id', None)

        if not items:
            break

        for item in items:
            yield item

        pages_fetched += 1
        if next_page_id is None:
            break
        page_id = next_page_id


async def async_page_iterator(
    fetch_page: Callable[..., Any],
    page_size: int = 100,
    max_pages: int | None = None,
    **fetch_kwargs: Any,
) -> AsyncIterator[T]:
    """Alias of :func:`page_iterator` for backward compatibility."""
    async for item in page_iterator(
        fetch_page,
        page_size=page_size,
        max_pages=max_pages,
        **fetch_kwargs,
    ):
        yield item
