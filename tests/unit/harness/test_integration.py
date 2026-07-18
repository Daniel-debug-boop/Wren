"""Integration test: orchestrator → spawn → execute → verify.

Tests full child agent lifecycle end-to-end with a bus subscriber
that responds to coding harness task requests.
"""

import asyncio
import pytest
from wren.harness.meta_orchestrator import MetaOrchestrator
from wren.harness.config import HarnessConfig
from wren.harness.message_bus import (
    AgentMessage,
    MessagePriority,
    MessageType,
)


@pytest.fixture
def cfg():
    c = HarnessConfig()
    c.auto_start_bus = False
    c.auto_start_dark_factory = False
    c.enable_hitl = False
    c.child_timeout_s = 15.0
    return c


class TestOrchestratorIntegration:
    @pytest.mark.asyncio
    async def test_spawn_coding_harness_and_execute(self, cfg):
        """Spawn coding harness, register bus responder, assign task, verify result."""
        orch = MetaOrchestrator('int_test', cfg)
        await orch.start()

        # Register a bus subscriber that responds to TASK_REQUEST messages
        async def task_responder(msg: AgentMessage) -> None:
            if msg.msg_type == MessageType.TASK_REQUEST:
                await orch.bus.publish(
                    AgentMessage(
                        source='test_responder',
                        msg_type=MessageType.TASK_RESULT,
                        correlation_id=msg.id,
                        priority=MessagePriority.HIGH,
                        payload={
                            'output': '# Task completed\nprint("hello world")',
                            'files_changed': ['hello.py'],
                        },
                    )
                )

        orch.bus.subscribe(MessageType.TASK_REQUEST.value, task_responder)

        # Spawn agent
        handle = await orch.spawn_agent('coding', 'Write hello world')
        assert handle.agent_id is not None
        assert handle.status.value == 'idle'

        # Assign task
        result = await orch.assign_and_run(
            handle,
            {
                'name': 'hello_world',
                'description': 'Print hello world using Python',
                'language': 'python',
            },
            reap=False,
        )

        # Verify result
        assert result is not None
        assert result.get('success') is True
        assert 'hello world' in result.get('output', '').lower()
        assert result.get('files_changed') == ['hello.py']
        assert result.get('critique_score', 0) >= 0
        assert result.get('quality_passed') is True
        assert result.get('duration_s', 0) > 0

        # Verify handle was updated
        assert handle.status.value == 'completed'
        assert handle.result is not None

        # Verify orchestrator tracked completion
        status = orch.status()
        assert status['children']['completed'] == 1
        assert status['children']['failed'] == 0

        await orch.shutdown()

    @pytest.mark.asyncio
    async def test_spawn_research_agent_and_execute(self, cfg):
        """Spawn research agent, register bus responder, assign task."""
        orch = MetaOrchestrator('int_research', cfg)
        await orch.start()

        # Register responder that feeds research results
        async def research_responder(msg: AgentMessage) -> None:
            if msg.msg_type == MessageType.TASK_REQUEST:
                await orch.bus.publish(
                    AgentMessage(
                        source='test_responder',
                        msg_type=MessageType.TASK_RESULT,
                        correlation_id=msg.id,
                        priority=MessagePriority.HIGH,
                        payload={
                            'success': True,
                            'output': 'Found 3 relevant sources on Python async programming.',
                            'sources': [
                                'https://docs.python.org/3/library/asyncio.html',
                            ],
                        },
                    )
                )

        orch.bus.subscribe(MessageType.TASK_REQUEST.value, research_responder)

        handle = await orch.spawn_agent('research', 'Research Python async')
        assert handle.status.value == 'idle'

        result = await orch.assign_and_run(
            handle,
            {
                'name': 'research_async',
                'description': 'Research Python async/await best practices',
            },
            reap=False,
        )

        assert result is not None
        assert result.get('success') is True
        assert result.get('critique_score', 0) >= 0
        assert handle.status.value == 'completed'

        await orch.shutdown()

    @pytest.mark.asyncio
    async def test_goal_processing_pipeline(self, cfg):
        """Run full process_goal pipeline: decompose → spawn → execute → reflect."""
        orch = MetaOrchestrator('int_goal', cfg)
        await orch.start()

        # Register responder so coding/research tasks can complete
        async def generic_responder(msg: AgentMessage) -> None:
            if msg.msg_type == MessageType.TASK_REQUEST:
                await orch.bus.publish(
                    AgentMessage(
                        source='test_responder',
                        msg_type=MessageType.TASK_RESULT,
                        correlation_id=msg.id,
                        priority=MessagePriority.HIGH,
                        payload={
                            'output': 'Task completed successfully.',
                            'files_changed': [],
                        },
                    )
                )

        orch.bus.subscribe(MessageType.TASK_REQUEST.value, generic_responder)

        result = await orch.process_goal('Build a simple CLI todo app')

        assert result is not None
        assert result['goal'] == 'Build a simple CLI todo app'
        assert result['task_count'] > 0
        assert result['children_spawned'] > 0
        assert result['children_completed'] > 0
        assert len(result['results']) == result['task_count']

        # Verify all tasks in the graph completed successfully
        for r in result['results']:
            assert r['success'] is True, f'Task {r["name"]} failed'

        # Verify reflection ran
        assert 'reflection' in result
        assert result['reflection']['total_tasks'] == result['task_count']
        assert result['reflection']['passed_tasks'] == result['task_count']

        await orch.shutdown()

    @pytest.mark.asyncio
    async def test_assign_and_run_high_risk_denied(self, cfg):
        """Task with HIGH risk should be denied by ThinkPipeline before execution."""
        orch = MetaOrchestrator('int_deny', cfg)
        await orch.start()

        handle = await orch.spawn_agent('coding', 'Delete database')

        with pytest.raises(RuntimeError, match='Denied by ThinkPipeline'):
            await orch.assign_and_run(
                handle,
                {
                    'name': 'drop_db',
                    'description': 'DELETE FROM users WHERE 1=1',
                },
                reap=False,
            )

        await orch.shutdown()

    @pytest.mark.asyncio
    async def test_bus_communication_during_execution(self, cfg):
        """Verify that the agent publishes progress/result messages on the bus."""
        orch = MetaOrchestrator('int_bus', cfg)
        await orch.start()

        received_messages = []

        async def bus_logger(msg: AgentMessage) -> None:
            received_messages.append({'source': msg.source, 'type': msg.msg_type.value})

        # Subscribe to all message types
        for mt in MessageType:
            orch.bus.subscribe(mt.value, bus_logger)

        async def task_responder(msg: AgentMessage) -> None:
            if msg.msg_type == MessageType.TASK_REQUEST:
                await orch.bus.publish(
                    AgentMessage(
                        source='test_responder',
                        msg_type=MessageType.TASK_RESULT,
                        correlation_id=msg.id,
                        priority=MessagePriority.HIGH,
                        payload={
                            'output': '# Done\nresult: ok',
                            'files_changed': [],
                        },
                    )
                )

        orch.bus.subscribe(MessageType.TASK_REQUEST.value, task_responder)

        handle = await orch.spawn_agent('coding', 'Test bus comms')
        await orch.assign_and_run(
            handle,
            {'name': 'bus_test', 'description': 'Test bus communication'},
            reap=False,
        )

        # Verify messages flowed through the bus
        sources = {m['source'] for m in received_messages}
        assert 'coding_harness' in sources or any(
            'coding' in m['source'] for m in received_messages
        )

        await orch.shutdown()
