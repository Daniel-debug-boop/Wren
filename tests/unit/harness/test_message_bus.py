"""Tests for message bus — publish, subscribe, auth, rate limit,
dead-letter queue."""

import asyncio
import pytest
from wren.harness.message_bus import (
    MessageBus,
    AgentMessage,
    MessageType,
    MessagePriority,
)
from wren.harness.auth import BusAuth


@pytest.fixture
def bus():
    return MessageBus()


@pytest.fixture
def authed_bus():
    auth = BusAuth(secret='test_secret')
    return MessageBus(auth=auth), auth


class TestMessageBus:
    @pytest.mark.asyncio
    async def test_publish_and_receive(self, bus):
        received = []
        bus.subscribe('event', lambda msg: received.append(msg))
        msg = AgentMessage(source='test', msg_type=MessageType.EVENT, payload={'x': 1})
        await bus.publish(msg)
        await bus.flush()
        assert len(received) >= 1
        assert received[0].payload['x'] == 1

    @pytest.mark.asyncio
    async def test_publish_and_wait(self, bus):
        async def responder():
            async def cb(msg):
                resp = AgentMessage(
                    source='responder',
                    msg_type=MessageType.RESPONSE,
                    payload={'ok': True},
                    correlation_id=msg.correlation_id,
                )
                await bus.publish(resp)

            bus.subscribe('task_request', cb)

        asyncio.create_task(responder())
        await asyncio.sleep(0.05)

        req = AgentMessage(
            source='client',
            msg_type=MessageType.TASK_REQUEST,
            payload={'action': 'ping'},
        )
        resp = await bus.publish_and_wait(req, timeout_s=2.0)
        assert resp is not None
        assert resp.payload.get('ok') is True

    @pytest.mark.asyncio
    async def test_priority_ordering(self, bus):
        order = []
        bus.subscribe('*', lambda msg: order.append(msg.priority))

        low = AgentMessage(
            source='t',
            msg_type=MessageType.EVENT,
            priority=MessagePriority.LOW,
            payload={},
        )
        high = AgentMessage(
            source='t',
            msg_type=MessageType.EVENT,
            priority=MessagePriority.HIGH,
            payload={},
        )

        await bus.publish(low)
        await bus.publish(high)
        await bus.flush()

        if len(order) >= 2:
            assert order[0] == MessagePriority.HIGH

    @pytest.mark.asyncio
    async def test_auth_valid(self, authed_bus):
        bus, auth = authed_bus
        token = auth.issue_token('agent1', 'coding')
        msg = AgentMessage(source='agent1', msg_type=MessageType.EVENT, payload={})
        # Should not raise
        await bus.publish(msg, token=token)

    @pytest.mark.asyncio
    async def test_auth_invalid(self, authed_bus):
        bus, auth = authed_bus
        msg = AgentMessage(source='agent1', msg_type=MessageType.EVENT, payload={})
        with pytest.raises(Exception):
            await bus.publish(msg, token='bad_token')

    @pytest.mark.asyncio
    async def test_rate_limit(self):
        bus = MessageBus()
        bus._rate_limit = 2  # 2 per window
        bus._rate_window_s = 1.0

        msg = AgentMessage(source='flooder', msg_type=MessageType.EVENT, payload={})
        await bus.publish(msg)  # 1 — OK
        await bus.publish(msg)  # 2 — OK
        await bus.publish(msg)  # 3 — should be rate-limited

        assert len(bus.dead_letter_queue()) >= 1
        assert bus.dead_letter_queue()[-1]['reason'] == 'rate_limited'

    @pytest.mark.asyncio
    async def test_dead_letter_expired(self, bus):
        msg = AgentMessage(
            source='test', msg_type=MessageType.EVENT, payload={}, ttl_s=0.0
        )
        await asyncio.sleep(0.01)
        await bus.publish(msg)
        dlq = bus.dead_letter_queue()
        assert any(e['reason'] == 'expired' for e in dlq)

    @pytest.mark.asyncio
    async def test_retry_dead_letter(self, bus):
        msg = AgentMessage(
            source='test', msg_type=MessageType.EVENT, payload={}, ttl_s=0.0
        )
        await asyncio.sleep(0.01)
        await bus.publish(msg)
        dlq = bus.dead_letter_queue()
        assert len(dlq) >= 1
        msg_id = dlq[-1]['msg_id']
        ok = bus.retry_dead_letter(msg_id)
        assert ok

    def test_recent_filter(self, bus):
        import time

        m1 = AgentMessage(source='s1', msg_type=MessageType.EVENT, payload={'a': 1})
        m2 = AgentMessage(source='s2', msg_type=MessageType.COMMAND, payload={'b': 2})
        bus._history = [m1, m2]
        assert len(bus.recent(source='s1')) == 1
        assert len(bus.recent(msg_type='command')) == 1
        assert len(bus.recent(limit=1)) == 1

    def test_stats(self, bus):
        s = bus.stats()
        assert 'total_messages' in s
        assert 'subscribers' in s
        assert 'queue_size' in s
        assert 'dead_letter_count' in s
