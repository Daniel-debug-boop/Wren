"""Simple circuit breaker — trips on N consecutive failures.

Extracted from meta_orchestrator.py for better modularity.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any


class CircuitState(str, Enum):
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'


class CircuitBreaker:
    """Simple circuit breaker — trips on N consecutive failures.

    After trip, stays open for recovery_timeout_s, then half-opens.
    If a call succeeds in half-open state, resets to closed.
    """

    def __init__(self, name: str, threshold: int = 3, recovery_timeout_s: float = 30.0):
        self._name = name
        self._threshold = threshold
        self._recovery_timeout_s = recovery_timeout_s
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._last_failure_time = 0.0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time > self._recovery_timeout_s:
                self._state = CircuitState.HALF_OPEN
        return self._state

    async def call(self, fn, *args, **kw) -> Any:
        from wren.harness.telemetry import T

        if self.state == CircuitState.OPEN:
            raise RuntimeError(f'Circuit [{self._name}] is OPEN')
        try:
            result = await fn(*args, **kw)
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                self._failures = 0
                T.info('circuit.closed', f'{self._name} recovered')
            return result
        except Exception as e:
            self._failures += 1
            self._last_failure_time = time.time()
            if self._failures >= self._threshold:
                self._state = CircuitState.OPEN
                T.warn(
                    'circuit.open', f'{self._name} tripped ({self._failures} failures)'
                )
            raise e

    def stats(self) -> dict[str, Any]:
        return {
            'name': self._name,
            'state': self.state.value,
            'failures': self._failures,
            'threshold': self._threshold,
        }
