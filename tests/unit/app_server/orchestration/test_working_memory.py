"""Tests for WorkingMemory — session-scoped task state persistence."""

import json
import os
import tempfile
import time
from pathlib import Path

import pytest

from wren.app_server.orchestration.working_memory import WorkingMemory


@pytest.fixture
def temp_dir():
    """Create a temporary directory for working memory storage."""
    with tempfile.TemporaryDirectory() as tmp:
        cwd = os.getcwd()
        os.chdir(tmp)
        yield Path(tmp)
        os.chdir(cwd)


@pytest.fixture
def wm(temp_dir):
    """Create a fresh WorkingMemory instance in a temp directory."""
    return WorkingMemory(project_root=str(temp_dir))


class TestWorkingMemory:
    def test_add_entry(self, wm):
        """Test adding a basic entry."""
        entry = wm.add('test_type', 'test content', {'key': 'value'})
        assert entry['type'] == 'test_type'
        assert entry['content'] == 'test content'
        assert entry['metadata'] == {'key': 'value'}
        assert 'id' in entry
        assert 'timestamp' in entry

    def test_add_decision(self, wm):
        """Test add_decision helper."""
        entry = wm.add_decision('Use postgres', context='db_setup')
        assert entry['type'] == 'decision'
        assert entry['content'] == 'Use postgres'
        assert entry['metadata']['context'] == 'db_setup'

    def test_add_progress(self, wm):
        """Test add_progress helper."""
        entry = wm.add_progress('Setup docker', 'running', 'Pulling images')
        assert entry['type'] == 'progress'
        assert entry['content'] == 'Setup docker'
        assert entry['metadata']['status'] == 'running'
        assert entry['metadata']['detail'] == 'Pulling images'

    def test_add_todo(self, wm):
        """Test add_todo helper."""
        entry = wm.add_todo('Deploy backend', depends_on=['Setup infra'])
        assert entry['type'] == 'todo'
        assert entry['content'] == 'Deploy backend'
        assert entry['metadata']['status'] == 'pending'
        assert entry['metadata']['depends_on'] == ['Setup infra']

    def test_add_todo_no_deps(self, wm):
        """Test add_todo without dependencies."""
        entry = wm.add_todo('Setup infra')
        assert entry['metadata']['depends_on'] == []

    def test_complete_todo(self, wm):
        """Test completing a todo."""
        entry = wm.add_todo('Setup docker')
        result = wm.complete_todo(entry['id'], result='Done')
        assert result is not None
        assert result['metadata']['status'] == 'completed'
        assert result['metadata']['result'] == 'Done'
        assert 'completed_at' in result['metadata']

    def test_complete_todo_nonexistent(self, wm):
        """Test completing a non-existent todo returns None."""
        result = wm.complete_todo('nonexistent_id')
        assert result is None

    def test_add_reflection(self, wm):
        """Test add_reflection helper."""
        entry = wm.add_reflection('Learned to use docker compose', tags=['docker'])
        assert entry['type'] == 'reflection'
        assert 'docker' in entry['metadata']['tags']

    def test_query_by_type(self, wm):
        """Test querying entries filtered by type."""
        wm.add_decision('Decision 1')
        wm.add_decision('Decision 2')
        wm.add_progress('Progress 1', 'running')
        wm.add_reflection('Reflection 1')

        decisions = wm.query('decision', limit=10)
        assert len(decisions) == 2
        assert all(d['type'] == 'decision' for d in decisions)

    def test_query_limit(self, wm):
        """Test query result limit."""
        for i in range(10):
            wm.add_decision(f'Decision {i}')

        results = wm.query('decision', limit=3)
        assert len(results) == 3

    def test_get_pending_todos(self, wm):
        """Test get_pending_todos returns only pending items."""
        t1 = wm.add_todo('Task 1')
        wm.add_todo('Task 2')
        wm.complete_todo(t1['id'])

        pending = wm.get_pending_todos()
        assert len(pending) == 1
        assert pending[0]['content'] == 'Task 2'

    def test_get_completed_todos(self, wm):
        """Test get_completed_todos returns only completed items."""
        t1 = wm.add_todo('Task 1')
        t2 = wm.add_todo('Task 2')
        wm.complete_todo(t1['id'])

        completed = wm.get_completed_todos()
        assert len(completed) == 1
        assert completed[0]['content'] == 'Task 1'

        # t2 should not be in completed
        t2_ids = [t['id'] for t in completed]
        assert t2['id'] not in t2_ids

    def test_summary_empty(self, wm):
        """Test summary when no entries exist."""
        summary = wm.summary()
        assert 'No working memory entries yet.' in summary

    def test_summary_with_entries(self, wm):
        """Test summary contains all sections."""
        wm.add_decision('Use docker', context='infra')
        wm.add_todo('Setup docker')
        wm.add_reflection('Docker works great', tags=['docker'])

        summary = wm.summary()
        assert 'Working Memory' in summary
        assert 'Decisions' in summary
        assert 'Pending Tasks' in summary
        assert 'Recent Reflections' in summary

    def test_clear_session(self, wm):
        """Test clearing all entries."""
        wm.add_decision('Test decision')
        wm.add_todo('Test task')
        assert len(wm.query()) > 0

        wm.clear_session()
        assert len(wm.query()) == 0

    def test_persistence(self, wm, temp_dir):
        """Test that entries persist across WorkingMemory instances."""
        wm.add_decision('Persist this', context='test')
        wm.add_todo('Persist todo')

        # Create a new instance pointing to the same directory
        wm2 = WorkingMemory(project_root=str(temp_dir))
        decisions = wm2.query('decision')
        assert len(decisions) == 1
        assert decisions[0]['content'] == 'Persist this'

        todos = wm2.get_pending_todos()
        assert len(todos) == 1
        assert todos[0]['content'] == 'Persist todo'

    def test_persistence_corrupted_json(self, wm, temp_dir):
        """Test handling of corrupted memory file."""
        mem_path = temp_dir / '.wren' / 'working_memory.json'
        mem_path.parent.mkdir(parents=True, exist_ok=True)
        mem_path.write_text('{invalid json}')

        # Should not crash — should start fresh
        wm2 = WorkingMemory(project_root=str(temp_dir))
        assert len(wm2.query()) == 0

    def test_multiple_entry_types(self, wm):
        """Test mixed entry types are stored correctly."""
        wm.add_decision('D1')
        wm.add_progress('P1', 'running')
        wm.add_todo('T1')
        wm.add_reflection('R1')
        wm.add('custom', 'C1')

        all_entries = wm.query()
        assert len(all_entries) == 5

        types = [e['type'] for e in all_entries]
        assert 'decision' in types
        assert 'progress' in types
        assert 'todo' in types
        assert 'reflection' in types
        assert 'custom' in types

    def test_entry_ids_unique(self, wm):
        """Test that each entry gets a unique ID."""
        ids = set()
        for i in range(50):
            e = wm.add_decision(f'D{i}')
            assert e['id'] not in ids
            ids.add(e['id'])

    def test_query_nonexistent_type(self, wm):
        """Test querying by a type that doesn't exist."""
        wm.add_decision('Test')
        results = wm.query('nonexistent')
        assert len(results) == 0

    def test_summary_no_reflections(self, wm):
        """Test summary without reflections still shows other sections."""
        wm.add_decision('D1')
        wm.add_todo('T1')
        summary = wm.summary()
        assert 'Recent Reflections' not in summary

    def test_summary_no_decisions(self, wm):
        """Test summary without decisions still shows other sections."""
        wm.add_todo('T1')
        summary = wm.summary()
        assert 'Decisions' not in summary

    def test_complete_todo_updates_file(self, wm, temp_dir):
        """Test that completing a todo actually saves to disk."""
        entry = wm.add_todo('Task to complete')
        wm.complete_todo(entry['id'], result='Done!')

        # Read the file directly
        mem_path = temp_dir / '.wren' / 'working_memory.json'
        assert mem_path.exists()
        data = json.loads(mem_path.read_text())
        assert len(data['entries']) == 1
        assert data['entries'][0]['metadata']['status'] == 'completed'
        assert data['entries'][0]['metadata']['result'] == 'Done!'
