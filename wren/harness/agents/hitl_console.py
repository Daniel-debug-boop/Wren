"""Human-in-the-loop console.

When the autonomous system cannot make a decision — ambiguous
instruction, approval required, safety check — it pauses and
asks the human through this console.

Messages appear as structured approval requests. The human can
approve, reject, or provide additional input.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

_logger = logging.getLogger(__name__)


class Decision(str, Enum):
    APPROVED = 'approved'
    REJECTED = 'rejected'
    MODIFIED = 'modified'
    DELEGATED = 'delegated'
    TIMEOUT = 'timeout'


@dataclass
class ApprovalRequest:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    title: str = ''
    description: str = ''
    context: dict[str, Any] = field(default_factory=dict)
    options: list[str] = field(default_factory=lambda: ['approve', 'reject'])
    timeout_s: float = 300.0
    timestamp: float = field(default_factory=time.time)
    decision: Decision | None = None
    feedback: str = ''
    resolved_by: str = ''

    @property
    def is_resolved(self) -> bool:
        return self.decision is not None

    @property
    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.timeout_s

    @property
    def auto_resolves(self) -> bool:
        """Auto-resolve to timeout on expiry."""
        return True


class HITLConsole:
    """Human-in-the-loop decision console.

    Collects approval requests and surfaces them to the human
    through the configured callback.
    """

    def __init__(self, notify_callback: Callable | None = None) -> None:
        self._requests: dict[str, ApprovalRequest] = {}
        self._pending: dict[str, asyncio.Future] = {}
        self._callback = notify_callback

    # ── Submit ───────────────────────────────────────────────────

    async def request_approval(
        self,
        title: str,
        description: str = '',
        context: dict[str, Any] | None = None,
        options: list[str] | None = None,
        timeout_s: float = 300.0,
    ) -> ApprovalRequest:
        """Submit an approval request and wait for human response."""
        req = ApprovalRequest(
            title=title,
            description=description,
            context=context or {},
            options=options or ['approve', 'reject'],
            timeout_s=timeout_s,
        )
        self._requests[req.id] = req

        # Notify human via callback
        if self._callback:
            try:
                if asyncio.iscoroutinefunction(self._callback):
                    await self._callback(req)
                else:
                    self._callback(req)
            except Exception as e:
                _logger.warning('HITL callback error: %s', e)

        # Wait for resolution or timeout
        future: asyncio.Future[None] = asyncio.Future()
        self._pending[req.id] = future

        try:
            await asyncio.wait_for(future, timeout=timeout_s)
        except asyncio.TimeoutError:
            if req.auto_resolves and not req.is_resolved:
                req.decision = Decision.TIMEOUT
                req.resolved_by = 'auto_timeout'
            self._pending.pop(req.id, None)

        return req

    # ── Resolve ──────────────────────────────────────────────────

    def resolve(
        self,
        request_id: str,
        decision: Decision,
        feedback: str = '',
        resolved_by: str = 'human',
    ) -> bool:
        """Resolve a pending approval request."""
        req = self._requests.get(request_id)
        if not req or req.is_resolved:
            return False
        req.decision = decision
        req.feedback = feedback
        req.resolved_by = resolved_by

        future = self._pending.pop(request_id, None)
        if future and not future.done():
            future.set_result(None)
        return True

    # ── Query ────────────────────────────────────────────────────

    def get(self, request_id: str) -> ApprovalRequest | None:
        return self._requests.get(request_id)

    def pending(self) -> list[ApprovalRequest]:
        return [
            r for r in self._requests.values() if not r.is_resolved and not r.is_expired
        ]

    def history(self, limit: int = 20) -> list[ApprovalRequest]:
        resolved = [r for r in self._requests.values() if r.is_resolved]
        return sorted(resolved, key=lambda x: x.timestamp, reverse=True)[:limit]
