"""Auto wrapper — wraps every operation with automatic recovery.

Instead of requiring the agent (or code) to opt into error recovery,
the auto_wrapper transparently wraps any callable that the agent
invokes. If the call fails, the adaptive retry loop takes over
automatically.

Two wrappers:
  auto_retry(callable) → returns a wrapped callable
  auto_operation(name, callable) → runs + retries immediately
"""

from __future__ import annotations

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable

from wren.ohos.circuit_breaker import BREAKER
from wren.ohos.config import CONFIG

_logger = logging.getLogger(__name__)


def auto_retry(
    fn: Callable[..., Any],
    operation_name: str | None = None,
    max_retries: int | None = None,
) -> Callable[..., Any]:
    """Decorator that wraps any sync/async callable with auto-recovery.

    Usage:
        @auto_retry
        def deploy(): ...

        @auto_retry(operation_name='deploy', max_retries=3)
        async def deploy(): ...

    The wrapped function will automatically retry on failure with
    strategy mutation, circuit-breaker protection, and solution
    recording.
    """
    op_name = operation_name or fn.__name__
    max_r = max_retries or CONFIG.max_retries_per_error

    if asyncio.iscoroutinefunction(fn):

        @wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any):
            return await _run_with_retry(
                lambda: fn(*args, **kwargs),
                op_name,
                max_r,
            )

        return async_wrapper
    else:

        @wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any):
            return asyncio.run(
                _run_with_retry(
                    lambda: _maybe_async(fn(*args, **kwargs)),
                    op_name,
                    max_r,
                )
            )

        return sync_wrapper


async def auto_operation(
    name: str,
    fn: Callable[[], Any],
    max_retries: int | None = None,
) -> dict[str, Any]:
    """Run a single operation with full auto-recovery.

    Args:
        name: Human-readable name for the operation.
        fn: Sync or async callable (no arguments).
        max_retries: Override max retries.

    Returns:
        dict with status, result, attempts, strategy_used.
    """
    return await _run_with_retry(
        fn,
        name,
        max_retries or CONFIG.max_retries_per_error,
    )


# ── Internals ─────────────────────────────────────────────────────


async def _run_with_retry(
    fn: Callable[[], Any],
    name: str,
    max_r: int,
) -> dict[str, Any]:
    """Core retry loop with circuit breaker + strategy mutation."""
    # Lazy import to avoid circular dependency
    from wren.app_server.orchestration.error_recovery import (  # noqa: PLC0415
        AdaptiveRetryLoop,
    )

    operation_type = name.split(':')[0] if ':' in name else name

    if not BREAKER.allow_request(operation_type):
        _logger.warning('AutoWrapper circuit OPEN for %s', operation_type)
        return {
            'status': 'circuit_open',
            'operation': name,
            'error': f'Circuit breaker open for {operation_type}',
        }

    loop = AdaptiveRetryLoop(max_retries=max_r)

    async def wrapped_fn(_strategy: str | None = None) -> Any:
        """Execute the original function (strategy param ignored for auto-wrapper)."""
        result = fn()
        if asyncio.iscoroutine(result):
            return await result
        return result

    result = await loop.execute(name, wrapped_fn)

    if result.get('status') == 'success':
        BREAKER.record_success(operation_type)
    else:
        BREAKER.record_failure(operation_type)

    return result


async def _maybe_async(value: Any) -> Any:
    """If value is a coroutine, await it; otherwise return as-is."""
    if asyncio.iscoroutine(value):
        return await value
    return value
