"""Pagination utilities for API responses."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any, Callable, TypeVar

T = TypeVar('T')


def page_iterator(
    fetch_page: Callable[[int], list[T] | Any],
    page_size: int = 50,
    max_pages: int | None = None,
) -> Iterator[T]:
    """Iterate over paginated API results.

    Args:
        fetch_page: A callable that takes a page number (1-indexed) and
            returns a list of items. Should return an empty list when
            there are no more pages.
        page_size: Number of items per page.
        max_pages: Maximum number of pages to fetch. None for unlimited.

    Yields:
        Individual items from each page.
    """
    page = 1
    pages_fetched = 0

    while True:
        if max_pages is not None and pages_fetched >= max_pages:
            break

        items = fetch_page(page)
        if not items:
            break

        yield from items
        page += 1
        pages_fetched += 1


async def async_page_iterator(
    fetch_page: Callable[[int], Any],
    page_size: int = 50,
    max_pages: int | None = None,
) -> AsyncIterator[T]:
    """Async version of page_iterator.

    Args:
        fetch_page: An async callable that takes a page number (1-indexed)
            and returns a list of items. Should return an empty list when
            there are no more pages.
        page_size: Number of items per page.
        max_pages: Maximum number of pages to fetch. None for unlimited.

    Yields:
        Individual items from each page.
    """
    page = 1
    pages_fetched = 0

    while True:
        if max_pages is not None and pages_fetched >= max_pages:
            break

        items = await fetch_page(page)
        if not items:
            break

        for item in items:
            yield item

        page += 1
        pages_fetched += 1
