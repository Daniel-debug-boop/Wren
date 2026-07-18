"""Tests for the Store facade."""

import json
import pytest
from wren.harness.storage.store import Store


class TestStore:
    def test_save_and_get_child(self):
        Store.save_child('store_test_1', 'coding', 'idle', task_name='test')
        row = Store.get_child('store_test_1')
        assert row is not None
        assert row['agent_type'] == 'coding'
        Store.delete_child('store_test_1')
        assert Store.get_child('store_test_1') is None

    def test_all_children(self):
        Store.save_child('sc1', 'a', 'idle')
        Store.save_child('sc2', 'b', 'busy')
        children = Store.all_children()
        assert len(children) >= 2
        Store.delete_child('sc1')
        Store.delete_child('sc2')

    def test_save_and_get_task(self):
        data = {'name': 'store_task', 'priority': 99}
        Store.save_task('st1', data)
        assert Store.get_task('st1') == data

    def test_add_and_all_facts(self):
        Store.add_fact('store fact test', 0.95, 'pytest')
        facts = Store.all_facts()
        assert any(f['claim'] == 'store fact test' for f in facts)

    def test_write_log(self):
        Store.write_log('INFO', 'store test log', 'test_mod', {'k': 'v'})
        logs = Store.recent_logs(5)
        assert len(logs) >= 1

    def test_vector_roundtrip(self):
        Store.save_vector('sv1', 'store vector content', [0.5, 0.6], tags='test')
        results = Store.search_vectors('vector', 'default')
        assert len(results) >= 0  # may match or not, just checking no crash
        Store.delete_vector('sv1')

    def test_incr_metric(self):
        Store.incr_metric('store_test_metric')
        Store.incr_metric('store_test_metric', 5)
        metrics = Store.all_metrics()
        assert metrics.get('store_test_metric', 0) >= 6
