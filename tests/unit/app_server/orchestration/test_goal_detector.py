"""Tests for GoalDetector — pre-start goal analysis and auto-decomposition."""

import os
import tempfile

import pytest

from wren.app_server.orchestration.goal_detector import GoalDetector


@pytest.fixture
def gd():
    """Create a GoalDetector instance."""
    return GoalDetector()


class TestGoalDetector:
    def test_simple_message_not_complex(self, gd):
        """Test that a simple message is not detected as a complex goal."""
        result = gd.analyze('Can you help me fix a bug in my Python script?')
        assert result['is_complex_goal'] is False
        assert result['auto_decomposition'] is None

    def test_short_query_not_complex(self, gd):
        """Test that a very short query is not complex."""
        result = gd.analyze('Hello, how are you?')
        assert result['is_complex_goal'] is False

    def test_complex_full_stack_triggers(self, gd):
        """Test that a full-stack project description triggers manager mode."""
        result = gd.analyze(
            'Build a complete full-stack web application with React frontend, '
            'PostgreSQL database, Docker containers, and user authentication '
            'using JWT tokens. Deploy it with a CI/CD pipeline.'
        )
        assert result['is_complex_goal'] is True
        assert result['score'] >= 3
        assert result['trigger_count'] >= 2
        assert result['auto_decomposition'] is not None
        assert len(result['auto_decomposition']) >= 4

    def test_decomposition_contains_infrastructure(self, gd):
        """Test decomposition includes infrastructure tasks."""
        result = gd.analyze(
            'Build a complete web app with Docker deployment and PostgreSQL database'
        )
        assert result['is_complex_goal']
        tasks = [t['name'] for t in result['auto_decomposition']]
        assert 'Setup infrastructure' in tasks
        assert 'Setup database' in tasks

    def test_decomposition_contains_backend(self, gd):
        """Test decomposition includes backend API task."""
        result = gd.analyze(
            'Build a full REST API backend with Express and PostgreSQL'
        )
        assert result['is_complex_goal']
        tasks = [t['name'] for t in result['auto_decomposition']]
        assert 'Implement backend API' in tasks

    def test_decomposition_contains_frontend(self, gd):
        """Test decomposition includes frontend UI task."""
        result = gd.analyze(
            'Build a complete web app with React frontend and Node.js backend'
        )
        assert result['is_complex_goal']
        tasks = [t['name'] for t in result['auto_decomposition']]
        assert 'Implement frontend UI' in tasks

    def test_decomposition_contains_auth(self, gd):
        """Test decomposition includes auth task."""
        result = gd.analyze(
            'Build a full application with user login and JWT authentication'
        )
        assert result['is_complex_goal']
        tasks = [t['name'] for t in result['auto_decomposition']]
        assert 'Implement authentication & authorization' in tasks

    def test_decomposition_always_contains_testing(self, gd):
        """Test decomposition always includes testing task."""
        result = gd.analyze(
            'Build a complete microservices platform with Docker'
        )
        assert result['is_complex_goal']
        tasks = [t['name'] for t in result['auto_decomposition']]
        assert 'Write tests & verify' in tasks
        assert 'Integration & final review' in tasks

    def test_dependency_ordering(self, gd):
        """Test that tasks are properly ordered by dependencies."""
        result = gd.analyze(
            'Build a complete full-stack app with React, Node.js, PostgreSQL, and Docker'
        )
        assert result['is_complex_goal']
        tasks = result['auto_decomposition']

        # Find backend and frontend tasks
        backend = None
        frontend = None
        for t in tasks:
            if 'backend' in t['name'].lower():
                backend = t
            if 'frontend' in t['name'].lower():
                frontend = t

        if backend and frontend:
            assert 'Setup infrastructure' in frontend['depends_on']

    def test_system_instruction_format(self, gd):
        """Test that system instruction is properly formatted."""
        result = gd.analyze(
            'Build a complete full-stack application with microservices architecture'
        )
        assert result['is_complex_goal']
        instruction = result['system_instruction']
        assert instruction is not None
        assert 'MANAGER MODE AUTO-ACTIVATED' in instruction
        assert 'complex project goal' in instruction.lower()
        assert 'sub-task' in instruction.lower()
        assert 'working memory' in instruction.lower()

    def test_injectable_context(self, gd):
        """Test injectable_context returns instruction for complex goals."""
        instruction = gd.injectable_context(
            'Build a complete enterprise platform with microservices'
        )
        assert instruction is not None
        assert 'MANAGER MODE' in instruction

    def test_injectable_context_simple_message(self, gd):
        """Test injectable_context returns None for simple messages."""
        instruction = gd.injectable_context('Fix this bug')
        assert instruction is None

    def test_microservice_trigger(self, gd):
        """Test that microservices-related language triggers detection."""
        result = gd.analyze(
            'Design the whole architecture for a microservices system'
        )
        assert result['is_complex_goal']
        assert result['trigger_count'] >= 2

    def test_multi_phase_trigger(self, gd):
        """Test that phase/milestone language triggers detection."""
        result = gd.analyze(
            'Phase 1: Setup. Phase 2: Build. This is a major project milestone'
        )
        assert result['is_complex_goal']

    def test_tech_triggers_alone_insufficient(self, gd):
        """Test that tech triggers alone without pattern triggers don't trigger."""
        # Only tech words, no project pattern
        result = gd.analyze(
            'Postgres, Redis, Docker, Kubernetes, React, REST API'
        )
        assert result['is_complex_goal'] is False

    def test_score_calculation(self, gd):
        """Test score calculation is correct."""
        result = gd.analyze(
            'Build a complete full-stack app with Docker, Auth, and a database'
        )
        assert result['score'] > 0
        assert result['trigger_count'] > 0
        assert result['tech_count'] > 0

    def test_decomposition_writes_to_working_memory(self, gd, tmp_path):
        """Test that auto-decomposition writes to working memory file."""
        # Change to temp dir so working memory is written there
        orig_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        try:
            result = gd.analyze(
                'Build a complete web application with Docker and PostgreSQL'
            )
            assert result['is_complex_goal']

            # Check working memory file was created
            wm_file = tmp_path / '.wren' / 'working_memory.json'
            assert wm_file.exists()

            import json
            data = json.loads(wm_file.read_text())
            entries = data['entries']
            assert any(e['type'] == 'decision' for e in entries)
            assert any(e['type'] == 'todo' for e in entries)
        finally:
            os.chdir(orig_cwd)
