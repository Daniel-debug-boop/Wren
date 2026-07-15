"""Tests for SQLite database layer."""

import json
import tempfile
import time
import pytest
from wren.harness.storage.database import _Database


@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix='.db') as f:
        yield _Database(f.name)


class TestDatabase:
    def test_init_applies_schema(self, db):
        row = db.conn.execute(
            "SELECT value FROM harness_meta WHERE key='schema_version'"
        ).fetchone()
        assert row is not None

    def test_child_save_and_get(self, db):
        db.child_save('test_1', 'coding', 'idle', task_name='test_task')
        row = db.child_get('test_1')
        assert row is not None
        assert row['agent_type'] == 'coding'
        assert row['status'] == 'idle'

    def test_child_all(self, db):
        db.child_save('a1', 'coding', 'idle')
        db.child_save('a2', 'research', 'busy')
        children = db.child_all()
        assert len(children) >= 2

    def test_child_delete(self, db):
        db.child_save('del_me', 'test', 'idle')
        db.child_delete('del_me')
        assert db.child_get('del_me') is None

    def test_task_save_and_get(self, db):
        data = {'name': 'task1', 'priority': 50}
        db.task_save('t1', data)
        assert db.task_get('t1') == data

    def test_fact_add_and_all(self, db):
        db.fact_add('test claim', 0.9, 'test')
        facts = db.fact_all()
        assert any(f['claim'] == 'test claim' for f in facts)

    def test_log_write_and_recent(self, db):
        db.log_write('INFO', 'test message', 'test_module', {'key': 'val'})
        logs = db.log_recent(5)
        assert len(logs) >= 1

    def test_vector_save_and_all(self, db):
        db.vector_save(
            'vec1', 'hello world', [0.1, 0.2, 0.3], tags='greeting', namespace='test'
        )
        rows = db.vector_all('test')
        assert len(rows) >= 1
        assert rows[0]['key'] == 'vec1'

    def test_vector_search(self, db):
        db.vector_save('code1', 'def foo(): pass', [0.1], tags='python', namespace='ns')
        results = db.vector_search('foo', 'ns')
        assert len(results) >= 1

    def test_vector_delete_namespace(self, db):
        db.vector_save('v1', 'x', [0.1], namespace='del_ns')
        db.vector_delete_namespace('del_ns')
        assert len(db.vector_all('del_ns')) == 0

    def test_metric_incr_and_all(self, db):
        db.metric_incr('test_calls')
        db.metric_incr('test_calls', 5)
        metrics = db.all_metrics()
        assert metrics.get('test_calls', 0) >= 6

    def test_meta_get_set(self, db):
        db.meta_set('my_key', 'my_val')
        assert db.meta_get('my_key') == 'my_val'
        assert db.meta_get('nonexistent', 'default') == 'default'

    def test_database_isolation(self, db):
        db.child_save('iso_1', 'coding', 'busy')
        db.child_save('iso_2', 'research', 'idle')
        all_c = db.child_all()
        assert len(all_c) >= 2
        assert all_c[0]['agent_id'] != all_c[1]['agent_id']
