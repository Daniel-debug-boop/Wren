"""Tests for SelfMemoryLoop — post-task reflection and lesson extraction."""

import pytest

from wren.app_server.orchestration.self_memory_loop import SelfMemoryLoop


class TestSelfMemoryLoop:
    @pytest.mark.asyncio
    async def test_reflect_success(self, tmp_path):
        """Test reflection on a successful outcome."""
        sml = SelfMemoryLoop(project_root=str(tmp_path))
        result = await sml.reflect(
            task_description='Deploy PostgreSQL',
            outcome='success',
            observations='Used docker-compose, worked first try. Docker works well.',
            tags=['deploy', 'docker'],
        )
        assert result['outcome'] == 'success'
        assert 'summary' in result
        assert len(result['lessons']) > 0
        assert 'summary' in result

    @pytest.mark.asyncio
    async def test_reflect_failure(self, tmp_path):
        """Test reflection on a failure outcome."""
        sml = SelfMemoryLoop(project_root=str(tmp_path))
        result = await sml.reflect(
            task_description='Install package',
            outcome='failure',
            observations='Package not found in repository. Missing dependency.',
            tags=['install'],
        )
        assert result['outcome'] == 'failure'
        assert len(result['lessons']) > 0

    @pytest.mark.asyncio
    async def test_reflect_stores_in_working_memory(self, tmp_path):
        """Test that reflections are stored in working memory."""
        sml = SelfMemoryLoop(project_root=str(tmp_path))
        await sml.reflect(
            task_description='Setup CI',
            outcome='success',
            observations='CI pipeline configured with GitHub Actions.',
            tags=['ci', 'github'],
        )

        lessons = sml.recent_lessons(limit=5)
        assert len(lessons) >= 1
        assert any('Setup CI' in l for l in lessons)

    @pytest.mark.asyncio
    async def test_reflect_extracts_docker_lesson(self, tmp_path):
        """Test lesson extraction for docker-related success."""
        sml = SelfMemoryLoop(project_root=str(tmp_path))
        result = await sml.reflect(
            task_description='Setup containers',
            outcome='success',
            observations='Docker containers running smoothly with docker-compose.',
            tags=['docker'],
        )
        docker_lessons = [l for l in result['lessons'] if 'docker' in l.lower()]
        assert len(docker_lessons) > 0

    @pytest.mark.asyncio
    async def test_reflect_extracts_missing_dependency_lesson(self, tmp_path):
        """Test lesson extraction for missing dependency errors."""
        sml = SelfMemoryLoop(project_root=str(tmp_path))
        result = await sml.reflect(
            task_description='Install tool',
            outcome='failure',
            observations='Tool not found in repository. Missing required dependency.',
            tags=['install'],
        )
        assert len(result['lessons']) > 0
        assert any('not found' in l.lower() for l in result['lessons'])

    def test_recent_lessons_empty(self, tmp_path):
        """Test recent_lessons returns empty list when no reflections exist."""
        sml = SelfMemoryLoop(project_root=str(tmp_path))
        lessons = sml.recent_lessons(limit=5)
        assert lessons == []

    def test_recent_lessons_limit(self, tmp_path):
        """Test recent_lessons respects the limit."""
        sml = SelfMemoryLoop(project_root=str(tmp_path))

        # Add reflections via internal WM (we can access it directly)
        for i in range(10):
            sml._wm.add_reflection(f'Lesson {i}', tags=['test'])

        lessons = sml.recent_lessons(limit=3)
        assert len(lessons) == 3

    @pytest.mark.asyncio
    async def test_compile_context(self, tmp_path):
        """Test compile_context returns a string (may be empty without fable setup)."""
        sml = SelfMemoryLoop(project_root=str(tmp_path))
        context = await sml.compile_context(task_context='test')
        # Should not crash — may return empty or formatted string
        assert isinstance(context, str)

    @pytest.mark.asyncio
    async def test_reflect_different_tasks(self, tmp_path):
        """Test multiple reflections don't interfere."""
        sml = SelfMemoryLoop(project_root=str(tmp_path))

        r1 = await sml.reflect('Task A', 'success', 'Great success')
        r2 = await sml.reflect('Task B', 'failure', 'Epic fail')

        assert r1['outcome'] == 'success'
        assert r2['outcome'] == 'failure'

        lessons = sml.recent_lessons(limit=10)
        assert len(lessons) >= 2

    @pytest.mark.asyncio
    async def test_lesson_ids_returned(self, tmp_path):
        """Test that lesson IDs are returned from reflect."""
        sml = SelfMemoryLoop(project_root=str(tmp_path))
        result = await sml.reflect(
            task_description='Test task',
            outcome='success',
            observations='Everything worked perfectly.',
            tags=['test'],
        )
        assert 'lesson_ids' in result
        # lesson_ids may be empty if fable_memory deduplicates
        assert isinstance(result['lesson_ids'], list)
