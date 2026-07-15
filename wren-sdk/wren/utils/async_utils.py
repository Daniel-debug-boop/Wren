"""Async utilities for Wren SDK."""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger('wren')

F = TypeVar('F', bound=Callable[..., Any])


def run_sync(coro):
    """Run an async function from sync context.

    Usage:
        result = run_sync(my_async_func(arg1, arg2))
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already in an async context, can't block
        raise RuntimeError(
            'Cannot call run_sync() from within an async context. '
            "Use 'await' directly instead."
        )

    return asyncio.run(coro)


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator for retrying async functions with exponential backoff."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f'Attempt {attempt + 1}/{max_attempts} failed: {e}. '
                            f'Retrying in {current_delay:.1f}s...'
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff

            raise last_exception  # type: ignore[misc]

        return wrapper  # type: ignore[return-value]

    return decorator


async def gather_with_limit(
    *coros,
    limit: int = 10,
) -> list[Any]:
    """Run coroutines with concurrency limit.

    Args:
        *coros: Coroutines to run.
        limit: Maximum concurrent operations.

    Returns:
        List of results in order.
    """
    semaphore = asyncio.Semaphore(limit)

    async def limited(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*(limited(c) for c in coros))


def create_task(coro, name: str | None = None) -> asyncio.Task:
    """Create an async task safely.

    Use this instead of asyncio.create_task() to ensure proper error handling.
    """
    task = asyncio.create_task(coro, name=name)

    def _handle_exception(task: asyncio.Task):
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            logger.error(f'Task {task.get_name()} failed: {exc}', exc_info=exc)

    task.add_done_callback(_handle_exception)
    return task
