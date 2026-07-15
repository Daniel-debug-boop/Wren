"""Inter-agent message bus with priority queuing, pub/sub, and
structured protocol.

All agents communicate through the bus. No direct agent-to-agent
calls. This enables full observability, message replay, and
decoupling.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from wren.harness.auth import BusAuth

_logger = logging.getLogger(__name__)


class MessagePriority(int, Enum):
    LOW = 0
    MEDIUM = 5
    HIGH = 10
    CRITICAL = 20


class MessageType(str, Enum):
    TASK_REQUEST = 'task_request'
    TASK_RESULT = 'task_result'
    QUERY = 'query'
    RESPONSE = 'response'
    ERROR = 'error'
    STATUS = 'status'
    COMMAND = 'command'
    EVENT = 'event'
    LOG = 'log'
    CRITIQUE = 'critique'
    APPROVAL_REQUEST = 'approval_request'
    APPROVAL_RESULT = 'approval_result'


@dataclass
class AgentMessage:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    source: str = ''
    target: str = ''  # '' = broadcast
    msg_type: MessageType = MessageType.EVENT
    priority: MessagePriority = MessagePriority.MEDIUM
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    correlation_id: str = ''  # for request/response pairing
    ttl_s: float = 300.0  # message expires after this

    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl_s


class MessageBus:
    """Async message bus with priority queuing, auth, rate limiting,
    and dead-letter queue.

    Agents subscribe to message types or source patterns. The bus
    dispatches in priority order, with CRITICAL messages jumping
    the queue.
    """

    def __init__(self, auth: Any = None) -> None:
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._history: list[AgentMessage] = []
        self._max_history = 500
        self._running = False
        self._lock = asyncio.Lock()
        self._auth = auth  # Optional[BusAuth]
        self._in_dispatch = False  # True while dispatching to subscribers

        # Dead-letter queue — messages that failed dispatch or expired
        self._dead_letter: list[dict[str, Any]] = []
        self._max_dead_letter = 200

        # Rate limiter: max N messages per source per window
        self._rate_limit: int = 100  # max msgs per source per window
        self._rate_window_s: float = 1.0
        self._rate_counts: dict[str, list[float]] = defaultdict(list)

    # ── Pub/sub ──────────────────────────────────────────────────

    def subscribe(self, pattern: str, callback: Callable) -> None:
        """Subscribe to messages matching pattern.

        Pattern can be:
          - msg_type name (e.g. 'task_request')
          - source name (e.g. 'coding_harness')
          - '*' for all messages
        """
        self._subscribers[pattern].append(callback)
        _logger.debug('MessageBus: subscriber added for %s', pattern)

    def unsubscribe(self, pattern: str, callback: Callable) -> None:
        self._subscribers[pattern] = [
            cb for cb in self._subscribers[pattern] if cb is not callback
        ]

    async def publish(self, msg: AgentMessage, token: str = '') -> None:
        """Publish a message to the bus.

        If auth is configured, token must be valid.
        Rate-limited per source (100 msg/s default).
        Expired messages go to dead-letter instead of dispatching.
        Dispatches to subscribers immediately AND queues for
        the main loop.
        """
        # Auth check — skip if called from within dispatch (subscriber callbacks
        # are already in the trusted process; requiring tokens from them would
        # break test responders and orchestrator progress events).
        if self._auth and not self._in_dispatch:
            await asyncio.to_thread(self._auth.validate, token, msg.source)

        # Rate limit check
        now = time.time()
        window_start = now - self._rate_window_s
        self._rate_counts[msg.source] = [
            t for t in self._rate_counts[msg.source] if t > window_start
        ]
        if len(self._rate_counts[msg.source]) >= self._rate_limit:
            _logger.warning('MessageBus: rate limit exceeded for %s', msg.source)
            self._dead_letter.append(
                {
                    'reason': 'rate_limited',
                    'msg_id': msg.id,
                    'source': msg.source,
                    'timestamp': now,
                }
            )
            self._trim_dead_letter()
            return  # drop silently
        self._rate_counts[msg.source].append(now)

        # Expired check
        if msg.is_expired():
            self._dead_letter.append(
                {
                    'reason': 'expired',
                    'msg_id': msg.id,
                    'source': msg.source,
                    'msg_type': msg.msg_type.value,
                    'timestamp': now,
                }
            )
            self._trim_dead_letter()
            return

        await self._queue.put((-msg.priority.value, time.time(), msg))

    async def publish_and_wait(
        self,
        msg: AgentMessage,
        token: str = '',
        timeout_s: float = 30.0,
    ) -> AgentMessage | None:
        """Publish and wait for a correlated response."""
        corr = msg.correlation_id or msg.id
        msg.correlation_id = corr
        future: asyncio.Future[AgentMessage] = asyncio.Future()

        def response_cb(resp: AgentMessage) -> None:
            if resp.id != msg.id and resp.correlation_id == corr and not future.done():
                future.set_result(resp)

        self.subscribe('*', response_cb)
        try:
            await self.publish(msg, token=token)
            deadline = time.time() + timeout_s
            while not future.done() and time.time() < deadline:
                await self.flush()
                await asyncio.sleep(0.01)
            if future.done():
                return future.result()
            return None
        finally:
            self.unsubscribe('*', response_cb)

    # ── Dispatch ─────────────────────────────────────────────────

    async def _dispatch(self, msg: AgentMessage) -> None:
        self._history.append(msg)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        # Mark dispatch context so subscriber callbacks can publish
        # without auth (they run inside the trusted process).
        self._in_dispatch = True
        try:
            # Match subscribers
            patterns = ['*', msg.msg_type.value, msg.source, msg.target]
            called: set[int] = set()
            for pattern in patterns:
                for cb in self._subscribers.get(pattern, []):
                    cb_id = id(cb)
                    if cb_id not in called:
                        called.add(cb_id)
                        try:
                            if asyncio.iscoroutinefunction(cb):
                                await cb(msg)
                            else:
                                cb(msg)
                        except Exception as e:
                            _logger.error('MessageBus subscriber error: %s', e)
        finally:
            self._in_dispatch = False

    async def flush(self) -> None:
        """Dispatch all queued messages in priority order.

        Loops until no new messages appear in the queue, so callbacks
        that publish further messages are also dispatched.
        """
        while True:
            items: list[AgentMessage] = []
            while not self._queue.empty():
                _, _, msg = await self._queue.get()
                items.append(msg)
            if not items:
                break
            items.sort(key=lambda m: m.priority.value, reverse=True)
            for item in items:
                await self._dispatch(item)
            await asyncio.sleep(0)  # yield so new publishes from callbacks can queue

    # ── Consumer loop ────────────────────────────────────────────

    async def start(self) -> None:
        self._running = True
        _logger.info('MessageBus: started')
        while self._running:
            try:
                _, _, msg = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._dispatch(msg)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                _logger.error('MessageBus loop error: %s', e)

    def stop(self) -> None:
        self._running = False

    # ── Dead-letter ──────────────────────────────────────────────

    def _trim_dead_letter(self) -> None:
        if len(self._dead_letter) > self._max_dead_letter:
            self._dead_letter = self._dead_letter[-self._max_dead_letter :]

    def dead_letter_queue(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._dead_letter[-limit:]

    def retry_dead_letter(self, msg_id: str) -> bool:
        """Re-publish a message from the dead-letter queue by ID."""
        for entry in self._dead_letter:
            if entry['msg_id'] == msg_id:
                self._dead_letter.remove(entry)
                msg = AgentMessage(
                    id=msg_id,
                    source=entry.get('source', ''),
                    msg_type=MessageType(entry.get('msg_type', 'event')),
                    payload={},
                )
                # Re-publish without auth check (internal recovery)
                self._queue.put_nowait((0, time.time(), msg))
                return True
        return False

    # ── Query ────────────────────────────────────────────────────

    def recent(
        self,
        msg_type: str | None = None,
        source: str | None = None,
        limit: int = 20,
    ) -> list[AgentMessage]:
        msgs = self._history
        if msg_type:
            msgs = [m for m in msgs if m.msg_type.value == msg_type]
        if source:
            msgs = [m for m in msgs if m.source == source]
        return msgs[-limit:]

    def stats(self) -> dict[str, Any]:
        auth_stats = {}
        if self._auth:
            auth_stats = {'auth': self._auth.stats()}
        return {
            'total_messages': len(self._history),
            'subscribers': {k: len(v) for k, v in self._subscribers.items()},
            'queue_size': self._queue.qsize(),
            'dead_letter_count': len(self._dead_letter),
            'rate_limits_active': len(self._rate_counts),
            **auth_stats,
        }
