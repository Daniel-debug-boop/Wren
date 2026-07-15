"""REST API endpoints for harness MetaOrchestrator (v2 multi-agent system).

Exposes the full harness lifecycle: goal processing, child agent spawning,
task assignment, health monitoring, and status inspection.
"""

import logging

from fastapi import APIRouter, HTTPException

from wren.harness import MetaOrchestrator, HarnessConfig

from wren.app_server.config import get_default_persistence_dir
from wren.app_server.settings.provider_store import LLMProviderStore

_logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/api/orchestration/harness',
    tags=['harness'],
)


# ------------------------------------------------------------------
# Singleton store for active orchestrator instances
# ------------------------------------------------------------------
class _OrchestratorStore:
    """Holds active MetaOrchestrator instances keyed by session ID."""

    def __init__(self) -> None:
        self._instances: dict[str, MetaOrchestrator] = {}

    async def get_or_create(self, session_id: str) -> MetaOrchestrator:
        if session_id not in self._instances:
            config = HarnessConfig()
            orch = MetaOrchestrator(
                conversation_id=session_id,
                config=config,
            )

            # Start background services (bus, child monitor, skills, project context)
            await orch.start()

            # ── Restore from checkpoint if available (server restart) ──
            try:
                restored = await orch.restore_from_checkpoint()
                if restored:
                    _logger.info(
                        'Resumed session %s from checkpoint',
                        session_id,
                    )
            except Exception as e:
                _logger.warning('Checkpoint restore failed: %s', e)

            # ── Configure ModelRouter with saved LLM provider keys ──
            try:
                await self._configure_model_router(session_id)
            except Exception as e:
                _logger.warning('Failed to configure ModelRouter: %s', e)

            self._instances[session_id] = orch

        return self._instances[session_id]

    async def _configure_model_router(self, session_id: str) -> None:
        """Load saved LLM provider API keys and configure the orchestrator's ModelRouter.

        Reads from the file-based provider store and calls
        ``MetaOrchestrator.configure_api_keys()`` so the ModelRouter can
        auto-select models for Planner → Researcher → Writer → Reviewer
        agent roles based on which providers the user has configured.
        """
        orch = self._instances.get(session_id)
        if not orch:
            return

        store = LLMProviderStore.get_instance(get_default_persistence_dir())
        api_keys = await store.get_api_keys_map()

        if api_keys:
            orch.configure_api_keys(api_keys)
            _logger.info(
                'ModelRouter configured with %d API keys: %s',
                len(api_keys),
                list(api_keys.keys()),
            )

    def get(self, session_id: str) -> MetaOrchestrator | None:
        return self._instances.get(session_id)

    def remove(self, session_id: str) -> None:
        orch = self._instances.pop(session_id, None)
        if orch:
            _logger.info('Removed session %s from orchestrator store', session_id)


_store = _OrchestratorStore()


def _get_orch(session_id: str) -> MetaOrchestrator:
    orch = _store.get(session_id)
    if not orch:
        raise HTTPException(status_code=404, detail=f'Session {session_id} not found')
    return orch


# ------------------------------------------------------------------
# Goal processing
# ------------------------------------------------------------------


@router.post('/process-goal')
async def harness_process_goal(session_id: str, goal: str):
    """Process a goal through the MetaOrchestrator: decompose, spawn, execute.

    This is the main entry point. Returns task IDs as they are created.
    """
    orch = await _store.get_or_create(session_id)
    result = await orch.process_goal(goal)
    return {
        'goal': goal,
        'tasks': result,
        'session_id': session_id,
    }


# ------------------------------------------------------------------
# Child agent lifecycle
# ------------------------------------------------------------------


@router.post('/spawn-agent')
async def harness_spawn_agent(
    session_id: str,
    agent_type: str,
    task: str,
):
    """Spawn a child agent of the given type with a task."""
    orch = _get_orch(session_id)
    handle = await orch.spawn_agent(agent_type, task_desc=task)
    return {
        'handle': {
            'agent_id': handle.agent_id,
            'agent_type': handle.agent_type,
            'task_name': task,
        },
        'agent_type': agent_type,
        'task': task,
        'session_id': session_id,
    }


@router.post('/assign-task')
async def harness_assign_task(
    session_id: str,
    handle: str,
    task: str,
):
    """Assign a task to an already-spawned child agent."""
    orch = _get_orch(session_id)
    result = await orch.assign_and_run(handle, task)
    return {
        'handle': handle,
        'task': task,
        'result': result,
        'session_id': session_id,
    }


@router.post('/kill-agent')
async def harness_kill_agent(session_id: str, handle: str):
    """Kill a child agent by handle."""
    orch = _get_orch(session_id)
    await orch.kill_agent(handle)
    return {'handle': handle, 'killed': True, 'session_id': session_id}


# ------------------------------------------------------------------
# Status & inspection
# ------------------------------------------------------------------


@router.get('/status')
async def harness_status(session_id: str):
    """Get full orchestrator status: children, tasks, health, budget."""
    orch = _get_orch(session_id)
    status_data = orch.status()
    return {
        'state': status_data.get('phase', 'unknown'),
        'children': status_data.get('active_children', []),
        'active_children': status_data.get('children', {}).get('active', 0),
        'uptime_s': status_data.get('uptime_s', 0),
        'goals_processed': status_data.get('goals_processed', 0),
        'session_id': session_id,
    }


@router.get('/health')
async def harness_health(session_id: str):
    """Run health checks on all harness subsystems."""
    orch = _get_orch(session_id)
    report = await orch.health_check()
    return {
        'healthy': report.healthy if hasattr(report, 'healthy') else True,
        'checks': report.checks if hasattr(report, 'checks') else [],
        'session_id': session_id,
    }


@router.get('/children')
async def harness_children(session_id: str):
    """List all active child agents with their status."""
    orch = _get_orch(session_id)
    children = []
    for handle, agent in (orch._children or {}).items():
        children.append(
            {
                'handle': handle,
                'type': type(agent).__name__,
                'status': agent.status.value if hasattr(agent, 'status') else 'unknown',
            }
        )
    return {'children': children, 'count': len(children), 'session_id': session_id}


# ------------------------------------------------------------------
# Think pipeline (risk assessment)
# ------------------------------------------------------------------


@router.post('/think')
async def harness_think(session_id: str, task: str):
    """Run ThinkPipeline risk assessment on a task before execution."""
    orch = _get_orch(session_id)
    pipeline = getattr(orch, '_think_pipeline', None)
    if not pipeline:
        raise HTTPException(status_code=501, detail='ThinkPipeline not configured')
    result = pipeline.assess(task)
    return {
        'task': task,
        'risk_level': result.risk_level if hasattr(result, 'risk_level') else 'unknown',
        'approved': result.approved if hasattr(result, 'approved') else True,
        'session_id': session_id,
    }


# ------------------------------------------------------------------
# Session management
# ------------------------------------------------------------------


@router.post('/session/close')
async def harness_close_session(session_id: str):
    """Close a harness session and clean up resources."""
    orch = _get_orch(session_id)
    if hasattr(orch, 'close') and callable(orch.close):
        await orch.close()
    _store.remove(session_id)
    return {'session_id': session_id, 'closed': True}
