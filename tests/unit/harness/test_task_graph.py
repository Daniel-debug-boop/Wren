"""Tests for task graph — DAG dependency resolution, priority ordering,
status tracking."""

import pytest
from wren.harness.task_graph import TaskGraph, PrioritizedTask, TaskStatus


class TestTaskGraph:
    def test_add_simple(self):
        g = TaskGraph()
        t = PrioritizedTask(name='task1', description='test', priority=50)
        g.add(t)
        assert g.get('task1') is not None

    def test_ready_respects_priority(self):
        g = TaskGraph()
        g.add(PrioritizedTask(name='low', description='low', priority=10))
        g.add(PrioritizedTask(name='high', description='high', priority=90))
        ready = g.ready(max_count=5)
        assert len(ready) == 2
        assert ready[0].name == 'high'

    def test_ready_respects_dependencies(self):
        g = TaskGraph()
        g.add(PrioritizedTask(name='a', description='a', priority=50))
        g.add(PrioritizedTask(name='b', description='b', depends_on=['a'], priority=50))
        ready = g.ready(max_count=5)
        assert len(ready) == 1
        assert ready[0].name == 'a'

    def test_ready_after_completion(self):
        g = TaskGraph()
        g.add(PrioritizedTask(name='a', description='a', priority=50, depends_on=[]))
        g.add(PrioritizedTask(name='b', description='b', depends_on=['a'], priority=50))
        g.update_status('a', TaskStatus.COMPLETED)
        ready = g.ready(max_count=5)
        assert len(ready) == 1
        assert ready[0].name == 'b'

    def test_failure_blocks_dependents(self):
        g = TaskGraph()
        g.add(PrioritizedTask(name='a', description='a', priority=50))
        g.add(PrioritizedTask(name='b', description='b', depends_on=['a'], priority=50))
        g.update_status('a', TaskStatus.FAILED)
        ready = g.ready(max_count=5)
        assert len(ready) == 0

    def test_is_complete(self):
        g = TaskGraph()
        g.add(PrioritizedTask(name='a', description='a', priority=50))
        assert not g.is_complete()
        g.update_status('a', TaskStatus.COMPLETED)
        assert g.is_complete()

    def test_has_failures(self):
        g = TaskGraph()
        g.add(PrioritizedTask(name='a', description='a', priority=50))
        assert not g.has_failures()
        g.update_status('a', TaskStatus.FAILED)
        assert g.has_failures()

    def test_get_missing(self):
        g = TaskGraph()
        assert g.get('nonexistent') is None

    def test_max_count_ready(self):
        g = TaskGraph()
        for i in range(10):
            g.add(PrioritizedTask(name=f't{i}', description=f't{i}', priority=50))
        ready = g.ready(max_count=3)
        assert len(ready) == 3
