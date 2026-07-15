"""Tests for the MetaOrchestrator — lifecycle, child management,
circuit breaker, progress streaming."""

import asyncio
import pytest
from wren.harness.meta_orchestrator import (
    MetaOrchestrator,
    CircuitBreaker,
    CircuitState,
)
from wren.harness.config import HarnessConfig


@pytest.fixture
def cfg():
    c = HarnessConfig()
    c.auto_start_bus = False
    c.auto_start_dark_factory = False
    c.enable_hitl = False
    return c


class TestMetaOrchestrator:
    @pytest.mark.asyncio
    async def test_start_and_shutdown(self, cfg):
        orch = MetaOrchestrator('test_conv', cfg)
        await orch.start()
        assert orch._state.current_phase == 'planning'
        await orch.shutdown()
        assert orch._state.current_phase == 'done'

    @pytest.mark.asyncio
    async def test_spawn_agent(self, cfg):
        orch = MetaOrchestrator('test', cfg)
        await orch.start()
        handle = await orch.spawn_agent('research', 'Find info')
        assert handle.agent_id is not None
        assert handle.status.value == 'idle'
        assert len(orch.list_children()) == 1
        await orch.shutdown()

    @pytest.mark.asyncio
    async def test_kill_agent(self, cfg):
        orch = MetaOrchestrator('test', cfg)
        await orch.start()
        handle = await orch.spawn_agent('research', 'test task')
        await orch.kill_agent(handle.agent_id)
        assert len(orch.list_children()) == 0
        await orch.shutdown()

    @pytest.mark.asyncio
    async def test_max_children_limit(self, cfg):
        cfg.max_concurrent_children = 2
        orch = MetaOrchestrator('test', cfg)
        await orch.start()
        await orch.spawn_agent('research', 't1')
        await orch.spawn_agent('research', 't2')
        with pytest.raises(RuntimeError, match='Max children'):
            await orch.spawn_agent('research', 't3')
        await orch.shutdown()

    @pytest.mark.asyncio
    async def test_status_report(self, cfg):
        orch = MetaOrchestrator('test', cfg)
        await orch.start()
        status = orch.status()
        assert 'phase' in status
        assert 'children' in status
        assert 'bus' in status
        assert 'auth' in status
        await orch.shutdown()

    @pytest.mark.asyncio
    async def test_progress_callback(self, cfg):
        events = []
        orch = MetaOrchestrator('test', cfg)
        orch.set_progress_callback(lambda e: events.append(e))
        await orch.start()
        handle = await orch.spawn_agent('research', 'tracked task')
        await orch.kill_agent(handle.agent_id)
        assert any(e['status'] == 'spawned' for e in events)
        await orch.shutdown()

    @pytest.mark.asyncio
    async def test_health_check(self, cfg):
        orch = MetaOrchestrator('test', cfg)
        await orch.start()
        report = orch.health_check()
        assert report['status'] in ('healthy', 'degraded')
        assert 'checks' in report
        await orch.shutdown()


class TestCircuitBreaker:
    def test_initial_state(self):
        cb = CircuitBreaker('test')
        assert cb.state == CircuitState.CLOSED

    def test_trips_on_threshold(self):
        cb = CircuitBreaker('test', threshold=3, recovery_timeout_s=60)

        async def fail():
            raise ValueError('boom')

        async def run():
            for _ in range(3):
                try:
                    await cb.call(fail)
                except ValueError:
                    pass
            assert cb.state == CircuitState.OPEN

        asyncio.run(run())

    def test_half_open_after_recovery(self):
        cb = CircuitBreaker('test', threshold=1, recovery_timeout_s=0.01)

        async def fail():
            raise ValueError('boom')

        async def succeed():
            return 'ok'

        async def run():
            try:
                await cb.call(fail)
            except ValueError:
                pass
            assert cb.state == CircuitState.OPEN
            await asyncio.sleep(0.02)
            # Should be half-open
            result = await cb.call(succeed)
            assert result == 'ok'
            assert cb.state == CircuitState.CLOSED

        asyncio.run(run())

    def test_stats(self):
        cb = CircuitBreaker('test', threshold=5)
        s = cb.stats()
        assert s['name'] == 'test'
        assert s['state'] == 'closed'
        assert s['failures'] == 0
