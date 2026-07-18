"""Tests for thinking pipeline — risk assessment, plan generation,
approval logic."""

import pytest
from wren.harness.thinking.pipeline import ThinkPipeline, ThinkOutput, RiskLevel


class TestThinkPipeline:
    @pytest.mark.asyncio
    async def test_think_returns_output(self):
        pipe = ThinkPipeline(agent_id='test', agent_type='coding')
        task = {
            'name': 'test_task',
            'description': 'Write a simple function',
            'language': 'python',
        }
        output = await pipe.think(task)
        assert isinstance(output, ThinkOutput)
        assert output.agent_id == 'test'
        assert output.task_name == 'test_task'

    @pytest.mark.asyncio
    async def test_think_approves_safe_task(self):
        pipe = ThinkPipeline()
        task = {'name': 'safe', 'description': 'Print hello world'}
        output = await pipe.think(task)
        assert output.approved is True

    @pytest.mark.asyncio
    async def test_think_denies_high_risk(self):
        pipe = ThinkPipeline()
        task = {'name': 'risky', 'description': 'sudo rm -rf /'}
        output = await pipe.think(task)
        assert output.approved is False

    @pytest.mark.asyncio
    async def test_think_generates_plan(self):
        pipe = ThinkPipeline()
        task = {'name': 'code', 'description': 'Build a web API'}
        output = await pipe.think(task)
        assert len(output.plan_steps) >= 3

    @pytest.mark.asyncio
    async def test_think_assesses_risks(self):
        pipe = ThinkPipeline()
        task = {'name': 'deploy', 'description': 'Deploy to production server'}
        output = await pipe.think(task)
        assert len(output.risks) >= 1
        risk_levels = [r.level for r in output.risks]
        assert any(
            rl in (RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.MEDIUM)
            for rl in risk_levels
        )

    @pytest.mark.asyncio
    async def test_think_estimates_resources(self):
        pipe = ThinkPipeline()
        task = {
            'name': 'big',
            'description': 'Implement full-stack app with docker and node deployment',
        }
        output = await pipe.think(task)
        assert output.estimated_tokens > 0
        assert output.estimated_time_s > 0
        assert len(output.estimated_tools) >= 1

    @pytest.mark.asyncio
    async def test_think_has_rollback(self):
        pipe = ThinkPipeline()
        task = {'name': 'edit', 'description': 'Edit configuration file'}
        output = await pipe.think(task)
        assert output.rollback_plan != ''
