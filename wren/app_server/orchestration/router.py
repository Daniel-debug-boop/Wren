"""REST API endpoints for manager agent, working memory, and self-memory loop."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from wren.app_server.orchestration.manager import ManagerAgent, SubTask
from wren.app_server.orchestration.self_memory_loop import SelfMemoryLoop
from wren.app_server.orchestration.sub_agent_service import SubAgentService
from wren.app_server.orchestration.error_recovery import (
    AdaptiveRetryLoop,
    ErrorSignature,
    SolutionRegistry,
)
from wren.app_server.orchestration.working_memory import WorkingMemory

_logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/api/orchestration',
    tags=['orchestration'],
)


def _get_wm() -> WorkingMemory:
    return WorkingMemory()


def _get_sml() -> SelfMemoryLoop:
    return SelfMemoryLoop()


def _get_mgr() -> ManagerAgent:
    return ManagerAgent()


# ------------------------------------------------------------------
# Working Memory endpoints
# ------------------------------------------------------------------


@router.get('/memory')
async def get_memory(entry_type: str | None = None, limit: int = 20):
    """Query working memory entries, optionally filtered by type."""
    wm = _get_wm()
    entries = wm.query(entry_type=entry_type, limit=limit)
    return {
        'entries': entries,
        'count': len(entries),
        'summary': wm.summary(),
        'pending': [t['content'] for t in wm.get_pending_todos()],
    }


@router.post('/memory')
async def add_memory(
    entry_type: str, content: str, metadata: dict[str, Any] | None = None
):
    """Add an entry to working memory."""
    wm = _get_wm()
    entry = wm.add(entry_type, content, metadata)
    return {'entry': entry, 'success': True}


@router.post('/memory/decision')
async def add_decision(decision: str, context: str = ''):
    """Log a decision to working memory."""
    wm = _get_wm()
    entry = wm.add_decision(decision, context)
    return {'entry': entry, 'success': True}


@router.post('/memory/reflection')
async def add_reflection(summary: str, tags: list[str] | None = None):
    """Log a reflection to working memory."""
    wm = _get_wm()
    entry = wm.add_reflection(summary, tags=tags)
    return {'entry': entry, 'success': True}


@router.get('/memory/summary')
async def memory_summary():
    """Get a plain-text summary of working memory."""
    wm = _get_wm()
    return {'summary': wm.summary()}


@router.delete('/memory')
async def clear_memory():
    """Clear all working memory entries."""
    wm = _get_wm()
    wm.clear_session()
    return {'success': True}


# ------------------------------------------------------------------
# Manager Agent endpoints
# ------------------------------------------------------------------


@router.post('/manager/init')
async def manager_init(goal: str):
    """Initialize a new manager goal."""
    mgr = _get_mgr()
    result = mgr.initialize_goal(goal)
    return result


@router.post('/manager/decompose')
async def manager_decompose(sub_tasks: list[dict[str, Any]]):
    """Register decomposed sub-tasks."""
    mgr = _get_mgr()
    plan = mgr.decompose(sub_tasks)
    return {'sub_tasks': plan, 'count': len(plan)}


@router.get('/manager/plan')
async def manager_plan():
    """Get the current sub-task plan."""
    mgr = _get_mgr()
    return {
        'sub_tasks': mgr.plan(),
        'ready': [t.to_dict() for t in mgr.get_ready_tasks()],
    }


@router.get('/manager/status')
async def manager_status():
    """Get full manager status with counts."""
    mgr = _get_mgr()
    return mgr.status()


@router.get('/manager/summary')
async def manager_summary():
    """Get a plain-text manager summary."""
    mgr = _get_mgr()
    return {'summary': mgr.summary()}


@router.post('/manager/start-task')
async def manager_start_task(task_id: str):
    """Mark a sub-task as running."""
    mgr = _get_mgr()
    task = mgr.start_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f'Task {task_id} not found')
    return {'task': task.to_dict()}


@router.post('/manager/complete-task')
async def manager_complete_task(task_id: str, result: str, error: str | None = None):
    """Mark a sub-task as completed or failed."""
    mgr = _get_mgr()
    task = mgr.complete_task(task_id, result, error)
    if not task:
        raise HTTPException(status_code=404, detail=f'Task {task_id} not found')
    return {'task': task.to_dict()}


@router.post('/manager/finalize')
async def manager_finalize(overall_outcome: str = 'success'):
    """Finalize the project and run the self-memory loop."""
    mgr = _get_mgr()
    result = await mgr.finalize(overall_outcome)
    return result


# ------------------------------------------------------------------
# Self-Memory Loop endpoints
# ------------------------------------------------------------------


@router.post('/reflect')
async def reflect(
    task_description: str,
    outcome: str,
    observations: str,
    tags: list[str] | None = None,
):
    """Run the self-reflection cycle for a completed task."""
    sml = _get_sml()
    result = await sml.reflect(task_description, outcome, observations, tags=tags)
    return result


@router.get('/lessons')
async def recent_lessons(limit: int = 10):
    """Get recent reflections from working memory."""
    sml = _get_sml()
    lessons = sml.recent_lessons(limit=limit)
    return {'lessons': lessons, 'count': len(lessons)}


# ------------------------------------------------------------------
# Sub-Agent endpoints
# ------------------------------------------------------------------


@router.post('/sub-agent/spawn')
async def sub_agent_spawn(
    parent_conversation_id: str,
    task_name: str,
    task_description: str,
    acceptance_criteria: list[str] | None = None,
):
    """Spawn a sub-conversation for a single task."""
    svc = SubAgentService()
    result = await svc.spawn_sub_task(
        parent_conversation_id=parent_conversation_id,
        task_name=task_name,
        task_description=task_description,
        acceptance_criteria=acceptance_criteria,
    )
    return result.to_dict()


@router.post('/sub-agent/execute')
async def sub_agent_execute(
    parent_conversation_id: str,
    tasks: list[dict[str, Any]],
    sequential: bool = False,
):
    """Execute multiple sub-tasks and collect results."""
    svc = SubAgentService()
    results = await svc.execute_sub_tasks(
        parent_conversation_id=parent_conversation_id,
        tasks=tasks,
        sequential=sequential,
    )
    return {
        'results': [r.to_dict() for r in results],
        'total': len(results),
        'completed': sum(1 for r in results if r.status == 'completed'),
        'failed': sum(1 for r in results if r.status == 'failed'),
    }


# ------------------------------------------------------------------
# Error Recovery endpoints
# ------------------------------------------------------------------


@router.post('/error/classify')
async def error_classify(error_text: str):
    """Classify an error and check for known solutions."""
    sig = ErrorSignature(error_text)
    registry = SolutionRegistry()
    known = registry.lookup(error_text)
    strategies = ErrorSignature.STRATEGY_MUTATIONS.get(
        sig.error_type,
        ErrorSignature.STRATEGY_MUTATIONS['default'],
    )
    return {
        'error_type': sig.error_type,
        'signature': sig.signature,
        'key_identifiers': sig.key_identifiers,
        'known_solution': known,
        'available_strategies': strategies,
    }


@router.post('/error/record-success')
async def error_record_success(error_text: str, strategy: str, strategy_index: int = 0):
    """Record a winning strategy for an error."""
    registry = SolutionRegistry()
    registry.record_success(error_text, strategy, strategy_index)
    return {'success': True}


@router.get('/error/solutions')
async def error_solutions():
    """List all known error solutions."""
    registry = SolutionRegistry()
    solutions = registry.all_solutions()
    return {'solutions': solutions, 'count': len(solutions)}


@router.post('/error/retry')
async def error_retry(
    operation_name: str,
    max_retries: int = 5,
):
    """Execute an operation with the adaptive retry loop.

    This endpoint creates a retry loop instance. The caller must retry
    with actual operations — this returns the loop's summary/stats.
    """
    loop = AdaptiveRetryLoop(max_retries=max_retries)
    return {
        'operation': operation_name,
        'max_retries': max_retries,
        'status': 'ready',
        'message': 'Use the AdaptiveRetryLoop.execute() method in code '
        'to run operations with automatic retry.',
    }
