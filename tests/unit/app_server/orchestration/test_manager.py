"""Tests for ManagerAgent and SubTask — goal decomposition and task tracking."""

import pytest

from wren.app_server.orchestration.manager import ManagerAgent, SubTask


class TestSubTask:
    def test_create(self):
        """Test basic SubTask creation."""
        t = SubTask(
            name='Setup docker',
            description='Install Docker and configure containers',
            depends_on=['Setup OS'],
            estimated_effort='medium',
            acceptance_criteria=['Docker runs', 'Containers work'],
        )
        assert t.name == 'Setup docker'
        assert t.status == 'pending'
        assert t.depends_on == ['Setup OS']
        assert t.estimated_effort == 'medium'
        assert len(t.acceptance_criteria) == 2
        assert t.id.startswith('task_')
        assert t.result is None
        assert t.error is None

    def test_create_defaults(self):
        """Test SubTask defaults."""
        t = SubTask(name='Simple task', description='Do a thing')
        assert t.depends_on == []
        assert t.estimated_effort == 'medium'
        assert t.acceptance_criteria == []
        assert t.status == 'pending'

    def test_to_dict(self):
        """Test serialization to dict."""
        t = SubTask(
            name='Build API',
            description='Build REST API',
            depends_on=['Setup DB'],
            estimated_effort='large',
            acceptance_criteria=['All endpoints work'],
        )
        d = t.to_dict()
        assert d['name'] == 'Build API'
        assert d['status'] == 'pending'
        assert d['depends_on'] == ['Setup DB']
        assert d['estimated_effort'] == 'large'
        assert d['acceptance_criteria'] == ['All endpoints work']
        assert d['id'] == t.id
        assert d['result'] is None
        assert d['error'] is None
        assert d['started_at'] is None
        assert d['completed_at'] is None

    def test_from_dict(self):
        """Test deserialization from dict."""
        d = {
            'id': 'task_custom123',
            'name': 'Deploy',
            'description': 'Deploy to production',
            'depends_on': ['Test'],
            'estimated_effort': 'small',
            'acceptance_criteria': ['Site loads'],
            'status': 'completed',
            'result': 'Deployed successfully',
            'error': None,
            'started_at': 100.0,
            'completed_at': 200.0,
        }
        t = SubTask.from_dict(d)
        assert t.id == 'task_custom123'
        assert t.name == 'Deploy'
        assert t.status == 'completed'
        assert t.result == 'Deployed successfully'
        assert t.started_at == 100.0
        assert t.completed_at == 200.0

    def test_from_dict_minimal(self):
        """Test deserialization from minimal dict."""
        d = {'name': 'Task', 'description': 'Desc'}
        t = SubTask.from_dict(d)
        assert t.name == 'Task'
        assert t.status == 'pending'
        assert t.id.startswith('task_')

    def test_roundtrip(self):
        """Test to_dict → from_dict roundtrip preserves data."""
        original = SubTask(
            name='Roundtrip',
            description='Testing',
            depends_on=['Dep'],
            estimated_effort='large',
            acceptance_criteria=['AC1'],
        )
        original.status = 'running'
        original.started_at = 42.0

        restored = SubTask.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.status == original.status
        assert restored.started_at == original.started_at


class TestManagerAgent:
    def test_initialize_goal(self, tmp_path):
        """Test initializing a new goal."""
        mgr = ManagerAgent(project_root=str(tmp_path))
        result = mgr.initialize_goal('Build a full-stack app')
        assert result['goal'] == 'Build a full-stack app'
        assert result['status'] == 'initialized'
        assert mgr._goal == 'Build a full-stack app'

    def test_decompose_and_plan(self, tmp_path):
        """Test decomposing a goal into sub-tasks and getting the plan."""
        mgr = ManagerAgent(project_root=str(tmp_path))
        mgr.initialize_goal('Build app')

        sub_tasks = [
            {
                'name': 'Setup infra',
                'description': 'Setup infrastructure',
                'depends_on': [],
                'estimated_effort': 'medium',
                'acceptance_criteria': ['Infra ready'],
            },
            {
                'name': 'Build backend',
                'description': 'Build the backend',
                'depends_on': ['Setup infra'],
                'estimated_effort': 'large',
                'acceptance_criteria': ['API works'],
            },
        ]

        plan = mgr.decompose(sub_tasks)
        assert len(plan) == 2
        assert plan[0]['name'] == 'Setup infra'
        assert plan[1]['depends_on'] == ['Setup infra']

        # Plan from getter
        plan2 = mgr.plan()
        assert len(plan2) == 2

    def test_get_ready_tasks(self, tmp_path):
        """Test getting tasks whose dependencies are met."""
        mgr = ManagerAgent(project_root=str(tmp_path))
        mgr.initialize_goal('Build app')

        mgr.decompose([
            {
                'name': 'Setup infra',
                'description': 'Setup infra',
                'depends_on': [],
            },
            {
                'name': 'Build backend',
                'description': 'Build backend',
                'depends_on': ['Setup infra'],
            },
        ])

        # Only 'Setup infra' should be ready
        ready = mgr.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].name == 'Setup infra'

    def test_get_ready_tasks_after_completion(self, tmp_path):
        """Test that completing a task unblocks dependents."""
        mgr = ManagerAgent(project_root=str(tmp_path))
        mgr.initialize_goal('Build app')

        mgr.decompose([
            {
                'name': 'Setup infra',
                'description': 'Setup infra',
                'depends_on': [],
            },
            {
                'name': 'Build backend',
                'description': 'Build backend',
                'depends_on': ['Setup infra'],
            },
        ])

        # Complete the blocking task
        infra = mgr.get_ready_tasks()[0]
        mgr.start_task(infra.id)
        mgr.complete_task(infra.id, 'Done')

        # Now 'Build backend' should be ready
        ready = mgr.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].name == 'Build backend'

    def test_start_task(self, tmp_path):
        """Test starting a task changes its status."""
        mgr = ManagerAgent(project_root=str(tmp_path))
        mgr.initialize_goal('Build')
        mgr.decompose([{
            'name': 'Task 1',
            'description': 'First task',
            'depends_on': [],
        }])

        task_id = mgr.plan()[0]['id']
        task = mgr.start_task(task_id)
        assert task is not None
        assert task.status == 'running'
        assert task.started_at is not None

    def test_start_nonexistent_task(self, tmp_path):
        """Test starting a non-existent task returns None."""
        mgr = ManagerAgent(project_root=str(tmp_path))
        task = mgr.start_task('nonexistent')
        assert task is None

    def test_complete_task_success(self, tmp_path):
        """Test completing a task successfully."""
        mgr = ManagerAgent(project_root=str(tmp_path))
        mgr.initialize_goal('Build')
        mgr.decompose([{
            'name': 'Task 1',
            'description': 'First task',
            'depends_on': [],
        }])

        task_id = mgr.plan()[0]['id']
        mgr.start_task(task_id)
        task = mgr.complete_task(task_id, 'Success!')
        assert task is not None
        assert task.status == 'completed'
        assert task.result == 'Success!'
        assert task.completed_at is not None

    def test_complete_task_failure(self, tmp_path):
        """Test completing a task with failure."""
        mgr = ManagerAgent(project_root=str(tmp_path))
        mgr.initialize_goal('Build')
        mgr.decompose([{
            'name': 'Task 1',
            'description': 'First task',
            'depends_on': [],
        }])

        task_id = mgr.plan()[0]['id']
        mgr.start_task(task_id)
        task = mgr.complete_task(task_id, '', error='Something broke')
        assert task is not None
        assert task.status == 'failed'
        assert task.error == 'Something broke'

    def test_complete_nonexistent_task(self, tmp_path):
        """Test completing a non-existent task returns None."""
        mgr = ManagerAgent(project_root=str(tmp_path))
        task = mgr.complete_task('nonexistent', 'result')
        assert task is None

    def test_status(self, tmp_path):
        """Test status report with counts."""
        mgr = ManagerAgent(project_root=str(tmp_path))
        mgr.initialize_goal('Build app')

        mgr.decompose([
            {'name': 'T1', 'description': 'Task 1', 'depends_on': []},
            {'name': 'T2', 'description': 'Task 2', 'depends_on': []},
            {'name': 'T3', 'description': 'Task 3', 'depends_on': []},
        ])

        status = mgr.status()
        assert status['goal'] == 'Build app'
        assert status['total'] == 3
        assert status['status_counts']['pending'] == 3

        # Complete one task
        task_id = mgr.plan()[0]['id']
        mgr.start_task(task_id)
        mgr.complete_task(task_id, 'Done')

        status = mgr.status()
        assert status['status_counts']['pending'] == 2
        assert status['status_counts']['completed'] == 1

    def test_summary(self, tmp_path):
        """Test summary text generation."""
        mgr = ManagerAgent(project_root=str(tmp_path))
        mgr.initialize_goal('Test project')
        mgr.decompose([{
            'name': 'Task 1',
            'description': 'First task',
            'depends_on': [],
        }])

        summary = mgr.summary()
        assert 'Manager Summary' in summary
        assert 'Test project' in summary
        assert 'Pending: 1' in summary
        assert 'Working Memory' in summary  # includes WM summary

    def test_initialize_clears_previous(self, tmp_path):
        """Test that initialize_goal clears previous state."""
        mgr = ManagerAgent(project_root=str(tmp_path))
        mgr.initialize_goal('Old goal')
        mgr.decompose([{
            'name': 'Old task',
            'description': 'Old',
            'depends_on': [],
        }])
        assert len(mgr.plan()) == 1

        # Re-initialize
        mgr.initialize_goal('New goal')
        assert len(mgr.plan()) == 0
        assert mgr._goal == 'New goal'

    @pytest.mark.asyncio
    async def test_finalize(self, tmp_path):
        """Test finalize runs the self-memory loop."""
        mgr = ManagerAgent(project_root=str(tmp_path))
        mgr.initialize_goal('Test finalize')
        mgr.decompose([{
            'name': 'Task 1',
            'description': 'A task',
            'depends_on': [],
        }])

        task_id = mgr.plan()[0]['id']
        mgr.start_task(task_id)
        mgr.complete_task(task_id, 'Done')

        result = await mgr.finalize('All completed successfully')
        assert 'lessons' in result
        assert result['outcome'] == 'success'
