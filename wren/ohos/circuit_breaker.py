"""Circuit breaker for operation types.

Prevents cascading failures by tripping after N consecutive failures
for the same operation type. After timeout, transitions to half-open
and allows one test request.
"""

import time
from collections import defaultdict

from wren.ohos.config import CONFIG

State = str
CLOSED: State = 'CLOSED'  # normal operation
OPEN: State = 'OPEN'  # failing — fast-fail
HALF_OPEN: State = 'HALF_OPEN'  # test request permitted


class _BreakerState:
    __slots__ = ('state', 'failure_count', 'last_failure_time')

    def __init__(self) -> None:
        self.state: State = CLOSED
        self.failure_count: int = 0
        self.last_failure_time: float = 0.0


class CircuitBreakerRegistry:
    """Global registry of per-operation-type circuit breakers."""

    def __init__(self) -> None:
        self._breakers: dict[str, _BreakerState] = defaultdict(_BreakerState)

    def allow_request(self, operation_type: str) -> bool:
        """Check if a request is allowed for the given operation type."""
        b = self._breakers[operation_type]

        if b.state == CLOSED:
            return True

        if b.state == OPEN:
            elapsed = time.time() - b.last_failure_time
            if elapsed >= CONFIG.circuit_breaker_reset_timeout_s:
                b.state = HALF_OPEN
                return True
            return False

        # HALF_OPEN — allow exactly one
        return True

    def record_success(self, operation_type: str) -> None:
        """Reset failure count on success."""
        b = self._breakers[operation_type]
        b.state = CLOSED
        b.failure_count = 0

    def record_failure(self, operation_type: str) -> State:
        """Increment failure count; trip if threshold exceeded."""
        b = self._breakers[operation_type]
        b.failure_count += 1
        b.last_failure_time = time.time()
        if b.failure_count >= CONFIG.circuit_breaker_failure_threshold:
            b.state = OPEN
        return b.state

    def status(self, operation_type: str) -> dict:
        b = self._breakers[operation_type]
        return {
            'operation_type': operation_type,
            'state': b.state,
            'failure_count': b.failure_count,
            'allowed': self.allow_request(operation_type),
        }

    def all_status(self) -> dict[str, dict]:
        return {k: self.status(k) for k in self._breakers}


# Module-level singleton
BREAKER: CircuitBreakerRegistry = CircuitBreakerRegistry()
"""Import this directly instead of instantiating."""
