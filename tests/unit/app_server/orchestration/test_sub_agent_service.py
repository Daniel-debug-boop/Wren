"""Tests for SubAgentService and SubAgentResult — sub-conversation management."""

import pytest

from wren.app_server.orchestration.sub_agent_service import SubAgentResult, SubAgentService


class TestSubAgentResult:
    def test_create_default(self):
        """Test SubAgentResult creation with defaults."""
        r = SubAgentResult(
            sub_conversation_id='conv_123',
            task_name='Setup Docker',
        )
        assert r.sub_conversation_id == 'conv_123'
        assert r.task_name == 'Setup Docker'
        assert r.status == 'pending'
        assert r.result_summary is None
        assert r.error is None
        assert r.events_count == 0
        assert r.created_at is not None
        assert r.completed_at is None

    def test_create_with_values(self):
        """Test SubAgentResult with all values."""
        import time
        now = time.time()
        r = SubAgentResult(
            sub_conversation_id='conv_456',
            task_name='Build API',
            status='completed',
            result_summary='API built successfully',
            error=None,
            events_count=15,
        )
        r.completed_at = now
        assert r.status == 'completed'
        assert r.result_summary == 'API built successfully'
        assert r.events_count == 15
        assert r.completed_at == now

    def test_create_failed(self):
        """Test SubAgentResult with failure."""
        r = SubAgentResult(
            sub_conversation_id='',
            task_name='Failed Task',
            status='failed',
            error='HTTP 500: Server Error',
        )
        assert r.status == 'failed'
        assert r.error == 'HTTP 500: Server Error'

    def test_to_dict(self):
        """Test serialization to dict."""
        r = SubAgentResult(
            sub_conversation_id='conv_789',
            task_name='Test Task',
            status='completed',
            result_summary='Done',
        )
        d = r.to_dict()
        assert d['sub_conversation_id'] == 'conv_789'
        assert d['task_name'] == 'Test Task'
        assert d['status'] == 'completed'
        assert d['result_summary'] == 'Done'
        assert d['events_count'] == 0
        assert d['created_at'] == r.created_at

    def test_to_dict_failed(self):
        """Test serialization of a failed result."""
        r = SubAgentResult(
            sub_conversation_id='',
            task_name='Fail',
            status='failed',
            error='Broke',
        )
        d = r.to_dict()
        assert d['status'] == 'failed'
        assert d['error'] == 'Broke'


class TestSubAgentService:
    def test_build_sub_task_prompt(self):
        """Test that task prompt is properly formatted."""
        svc = SubAgentService()
        prompt = svc._build_sub_task_prompt(
            name='Setup Docker',
            description='Install Docker and configure containers',
            acceptance_criteria=[
                'Docker is installed',
                'Containers can run',
            ],
        )
        assert '# Task: Setup Docker' in prompt
        assert 'Install Docker and configure containers' in prompt
        assert '## Acceptance Criteria' in prompt
        assert 'Docker is installed' in prompt
        assert 'Containers can run' in prompt
        assert 'Complete this task autonomously' in prompt

    def test_build_sub_task_prompt_no_criteria(self):
        """Test task prompt without acceptance criteria."""
        svc = SubAgentService()
        prompt = svc._build_sub_task_prompt(
            name='Simple Task',
            description='Just do it',
        )
        assert '# Task: Simple Task' in prompt
        assert 'Just do it' in prompt
        assert '## Acceptance Criteria' not in prompt
        assert 'Complete this task autonomously' in prompt

    def test_build_sub_task_prompt_empty_criteria(self):
        """Test task prompt with empty acceptance criteria list."""
        svc = SubAgentService()
        prompt = svc._build_sub_task_prompt(
            name='Task',
            description='Desc',
            acceptance_criteria=[],
        )
        assert '## Acceptance Criteria' not in prompt

    def test_headers_no_key(self):
        """Test headers without session API key."""
        svc = SubAgentService()
        headers = svc._headers()
        assert headers['Content-Type'] == 'application/json'
        assert 'X-Session-API-Key' not in headers

    def test_headers_with_key(self):
        """Test headers with session API key."""
        svc = SubAgentService(session_api_key='sk-test')
        headers = svc._headers()
        assert headers['Content-Type'] == 'application/json'
        assert headers['X-Session-API-Key'] == 'sk-test'

    def test_default_url(self):
        """Test default app server URL."""
        svc = SubAgentService()
        assert svc._app_server_url == 'http://localhost:3000'

    def test_custom_url(self):
        """Test custom app server URL."""
        svc = SubAgentService(app_server_url='http://custom:8080')
        assert svc._app_server_url == 'http://custom:8080'

    def test_custom_poll_settings(self):
        """Test custom poll settings."""
        svc = SubAgentService(poll_interval=5.0, max_poll_time=120.0)
        assert svc._poll_interval == 5.0
        assert svc._max_poll_time == 120.0
