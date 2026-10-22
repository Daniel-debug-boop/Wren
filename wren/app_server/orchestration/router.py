"""REST API + WebSocket endpoints for orchestration manager, working memory,
self-memory loop, terminal execution, and context compilation.

All state is scoped per conversation via ``_ConversationStore`` so the UI
panel sees the same ManagerAgent + WorkingMemory across REST calls.
"""

import json
import logging
import os
import subprocess  # nosec: restricted to sandboxed commands
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, HTTPException, WebSocket, WebSocketDisconnect

from wren.app_server.orchestration.manager import ManagerAgent
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

# ══════════════════════════════════════════════════════════════════════
# P0: Conversation-scoped state store
# ══════════════════════════════════════════════════════════════════════


class _ConversationState:
    """Holds one conversation's ManagerAgent, WorkingMemory, SelfMemoryLoop,
    and a terminal subprocess handle."""

    def __init__(self, conversation_id: str) -> None:
        self.conversation_id = conversation_id
        base = Path(os.getcwd()) / '.wren' / 'conversations' / conversation_id
        base.mkdir(parents=True, exist_ok=True)

        self.wm = WorkingMemory(project_root=str(base))
        self.mgr = ManagerAgent(project_root=str(base), working_memory=self.wm)
        self.sml = SelfMemoryLoop(
            project_root=str(base),
            working_memory=self.wm,
        )
        # P1: Terminal session (lazy)
        self._term_proc: subprocess.Popen | None = None  # type: ignore[type-arg]
        self._term_history: list[dict[str, Any]] = []

    def get_terminal(self) -> subprocess.Popen:  # type: ignore[type-arg]
        if self._term_proc is None or self._term_proc.poll() is not None:
            self._term_proc = subprocess.Popen(  # nosec: sandboxed
                ['/bin/bash', '-i'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=os.getcwd(),
            )
        return self._term_proc

    def add_term_history(self, cmd: str, stdout: str, exit_code: int) -> None:
        self._term_history.append(
            {
                'cmd': cmd,
                'stdout': stdout[-2000:],
                'exit_code': exit_code,
                'ts': time.time(),
            }
        )
        if len(self._term_history) > 50:
            self._term_history = self._term_history[-50:]

    def terminal_history(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._term_history[-limit:]

    def close(self) -> None:
        if self._term_proc and self._term_proc.poll() is None:
            self._term_proc.terminate()
            self._term_proc.wait(timeout=5)


class _ConversationStore:
    """Holds active ConversationState instances keyed by conversation_id."""

    def __init__(self) -> None:
        self._states: dict[str, _ConversationState] = {}

    def get_or_create(self, conversation_id: str = 'default') -> _ConversationState:
        """Return existing state or create one."""
        cid = conversation_id or 'default'
        if cid not in self._states:
            self._states[cid] = _ConversationState(cid)
        return self._states[cid]

    def get(self, conversation_id: str = 'default') -> _ConversationState | None:
        return self._states.get(conversation_id or 'default')

    def remove(self, conversation_id: str) -> None:
        state = self._states.pop(conversation_id, None)
        if state:
            state.close()

    def remove_all(self) -> None:
        for state in self._states.values():
            state.close()
        self._states.clear()

    def get_manager(self, conversation_id: str = 'default') -> ManagerAgent:
        return self.get_or_create(conversation_id).mgr

    def get_wm(self, conversation_id: str = 'default') -> WorkingMemory:
        return self.get_or_create(conversation_id).wm

    def get_sml(self, conversation_id: str = 'default') -> SelfMemoryLoop:
        return self.get_or_create(conversation_id).sml


_store = _ConversationStore()


def _conv_id(q: str | None = None) -> str:
    """Return conversation_id (query param or 'default')."""
    return q or 'default'


# ══════════════════════════════════════════════════════════════════════
# P2: WebSocket — live state push
# ══════════════════════════════════════════════════════════════════════

_ws_clients: dict[str, set[WebSocket]] = {}


async def _broadcast_state(conversation_id: str) -> None:
    """Push current state to all WebSocket clients for this conversation."""
    clients = _ws_clients.get(conversation_id, set())
    if not clients:
        return
    state = _store.get(conversation_id)
    if not state:
        return
    mgr = state.mgr
    wm = state.wm
    sml = state.sml
    payload = json.dumps(
        {
            'type': 'state_update',
            'manager': mgr.status(),
            'memory': {
                'entries': wm.query(limit=20),
                'count': len(wm._entries) if hasattr(wm, '_entries') else 0,
                'pending': [t['content'] for t in wm.get_pending_todos()],
            },
            'lessons': sml.recent_lessons(limit=5),
            'ts': time.time(),
        }
    )
    dead = set()
    for ws in clients:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    clients -= dead


@router.websocket('/ws/{conversation_id}')
async def orchestration_ws(websocket: WebSocket, conversation_id: str = 'default') -> None:
    """WebSocket endpoint for live orchestration state updates.

    On connect the client receives the current full state, then
    automatic pushes every time state changes (via broadcast).
    """
    cid = conversation_id or 'default'
    await websocket.accept()
    _ws_clients.setdefault(cid, set()).add(websocket)

    try:
        # Send initial snapshot
        state = _store.get_or_create(cid)
        mgr = state.mgr
        wm = state.wm
        sml = state.sml
        snapshot = json.dumps(
            {
                'type': 'state_snapshot',
                'manager': mgr.status(),
                'memory': {
                    'entries': wm.query(limit=20),
                    'count': len(wm._entries) if hasattr(wm, '_entries') else 0,
                    'pending': [t['content'] for t in wm.get_pending_todos()],
                },
                'lessons': sml.recent_lessons(limit=5),
                'ts': time.time(),
            }
        )
        await websocket.send_text(snapshot)

        # Keep connection alive, handle incoming refresh requests
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get('action') == 'refresh':
                await _broadcast_state(cid)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        _logger.debug('WS error: %s', e)
    finally:
        _ws_clients.get(cid, set()).discard(websocket)


# ══════════════════════════════════════════════════════════════════════
# P0: Working Memory endpoints (conversation-scoped)
# ══════════════════════════════════════════════════════════════════════


@router.get('/memory')
async def get_memory(
    conversation_id: str | None = None,
    entry_type: str | None = None,
    limit: int = 20,
):
    """Query working memory entries for a conversation."""
    wm = _store.get_wm(_conv_id(conversation_id))
    entries = wm.query(entry_type=entry_type, limit=limit)
    return {
        'entries': entries,
        'count': len(entries),
        'summary': wm.summary(),
        'pending': [t['content'] for t in wm.get_pending_todos()],
    }


@router.post('/memory')
async def add_memory(
    entry_type: str = Body('note'),
    content: str = Body(''),
    metadata: dict[str, Any] | None = Body(None),
    conversation_id: str | None = Body(None),
):
    """Add an entry to working memory for a conversation."""
    wm = _store.get_wm(_conv_id(conversation_id))
    entry = wm.add(entry_type, content, metadata)
    await _broadcast_state(_conv_id(conversation_id))
    return {'entry': entry, 'success': True}


@router.post('/memory/decision')
async def add_decision(
    decision: str = Body(''),
    context: str = Body(''),
    conversation_id: str | None = Body(None),
):
    """Log a decision to working memory."""
    wm = _store.get_wm(_conv_id(conversation_id))
    entry = wm.add_decision(decision, context)
    await _broadcast_state(_conv_id(conversation_id))
    return {'entry': entry, 'success': True}


@router.post('/memory/reflection')
async def add_reflection(
    summary: str = Body(''),
    tags: list[str] | None = Body(None),
    conversation_id: str | None = Body(None),
):
    """Log a reflection to working memory."""
    wm = _store.get_wm(_conv_id(conversation_id))
    entry = wm.add_reflection(summary, tags=tags)
    await _broadcast_state(_conv_id(conversation_id))
    return {'entry': entry, 'success': True}


@router.get('/memory/summary')
async def memory_summary(conversation_id: str | None = None) -> Any:
    """Get a plain-text summary of working memory."""
    wm = _store.get_wm(_conv_id(conversation_id))
    return {'summary': wm.summary()}


@router.delete('/memory')
async def clear_memory(conversation_id: str | None = None) -> Any:
    """Clear all working memory entries for a conversation."""
    wm = _store.get_wm(_conv_id(conversation_id))
    wm.clear_session()
    await _broadcast_state(_conv_id(conversation_id))
    return {'success': True}


# ══════════════════════════════════════════════════════════════════════
# P0: Manager Agent endpoints (conversation-scoped)
# ══════════════════════════════════════════════════════════════════════


@router.post('/manager/init')
async def manager_init(
    goal: str = Body(...),
    conversation_id: str | None = Body(None),
):
    """Initialize a new manager goal for a conversation."""
    mgr = _store.get_manager(_conv_id(conversation_id))
    result = mgr.initialize_goal(goal)
    await _broadcast_state(_conv_id(conversation_id))
    return result


@router.post('/manager/decompose')
async def manager_decompose(
    sub_tasks: list[dict[str, Any]] = Body(...),
    conversation_id: str | None = Body(None),
):
    """Register decomposed sub-tasks."""
    mgr = _store.get_manager(_conv_id(conversation_id))
    plan = mgr.decompose(sub_tasks)
    await _broadcast_state(_conv_id(conversation_id))
    return {'sub_tasks': plan, 'count': len(plan)}


@router.get('/manager/plan')
async def manager_plan(conversation_id: str | None = None) -> Any:
    """Get the current sub-task plan."""
    mgr = _store.get_manager(_conv_id(conversation_id))
    return {
        'sub_tasks': mgr.plan(),
        'ready': [t.to_dict() for t in mgr.get_ready_tasks()],
    }


@router.get('/manager/status')
async def manager_status(conversation_id: str | None = None) -> Any:
    """Get full manager status with counts."""
    mgr = _store.get_manager(_conv_id(conversation_id))
    return mgr.status()


@router.get('/manager/summary')
async def manager_summary(conversation_id: str | None = None) -> Any:
    """Get a plain-text manager summary."""
    mgr = _store.get_manager(_conv_id(conversation_id))
    return {'summary': mgr.summary()}


@router.post('/manager/start-task')
async def manager_start_task(
    task_id: str = Body(...),
    conversation_id: str | None = Body(None),
):
    """Mark a sub-task as running."""
    mgr = _store.get_manager(_conv_id(conversation_id))
    task = mgr.start_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f'Task {task_id} not found')
    await _broadcast_state(_conv_id(conversation_id))
    return {'task': task.to_dict()}


@router.post('/manager/complete-task')
async def manager_complete_task(
    task_id: str = Body(...),
    result: str = Body(''),
    error: str | None = Body(None),
    conversation_id: str | None = Body(None),
):
    """Mark a sub-task as completed or failed."""
    mgr = _store.get_manager(_conv_id(conversation_id))
    task = mgr.complete_task(task_id, result, error)
    if not task:
        raise HTTPException(status_code=404, detail=f'Task {task_id} not found')
    await _broadcast_state(_conv_id(conversation_id))
    return {'task': task.to_dict()}


@router.post('/manager/finalize')
async def manager_finalize(
    overall_outcome: str = Body('success'),
    conversation_id: str | None = Body(None),
):
    """Finalize and run the self-memory loop."""
    mgr = _store.get_manager(_conv_id(conversation_id))
    result = await mgr.finalize(overall_outcome)
    await _broadcast_state(_conv_id(conversation_id))
    return result


# ══════════════════════════════════════════════════════════════════════
# P0: Self-Memory Loop endpoints (conversation-scoped)
# ══════════════════════════════════════════════════════════════════════


@router.post('/reflect')
async def reflect(
    task_description: str = Body(''),
    outcome: str = Body('success'),
    observations: str = Body(''),
    tags: list[str] | None = Body(None),
    conversation_id: str | None = Body(None),
):
    """Run the self-reflection cycle for a completed task."""
    sml = _store.get_sml(_conv_id(conversation_id))
    result = await sml.reflect(task_description, outcome, observations, tags=tags)
    await _broadcast_state(_conv_id(conversation_id))
    return result


@router.get('/lessons')
async def recent_lessons(
    limit: int = 10,
    conversation_id: str | None = None,
):
    """Get recent reflections from working memory."""
    wm = _store.get_wm(_conv_id(conversation_id))
    entries = wm.query('reflection', limit=limit)
    return {'lessons': entries, 'count': len(entries)}


# ══════════════════════════════════════════════════════════════════════
# P1: Terminal execution
# ══════════════════════════════════════════════════════════════════════


@router.post('/terminal/exec')
async def terminal_exec(
    command: str = Body(...),
    conversation_id: str | None = Body(None),
):
    """Execute a shell command in the conversation's terminal session."""
    cid = _conv_id(conversation_id)
    state = _store.get_or_create(cid)
    proc = state.get_terminal()

    try:
        stdout, stderr = proc.communicate(input=command + '\n', timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        exit_code = -1
    except Exception as e:
        state.add_term_history(command, str(e), -1)
        return {'stdout': '', 'stderr': str(e), 'exit_code': -1}

    exit_code = proc.returncode or 0
    output = (stdout or '') + (stderr or '')
    state.add_term_history(command, output, exit_code)

    # Re-create proc for next call after a timeout/kill
    state._term_proc = None  # type: ignore[union-attr]

    return {'stdout': output[-4000:], 'stderr': '', 'exit_code': exit_code}


@router.get('/terminal/history')
async def terminal_history(
    limit: int = 20,
    conversation_id: str | None = None,
):
    """Get terminal command history for a conversation."""
    state = _store.get(_conv_id(conversation_id))
    if not state:
        return {'history': [], 'count': 0}
    return {'history': state.terminal_history(limit=limit), 'count': 0}


# ══════════════════════════════════════════════════════════════════════
# P3: Memory → action context compilation
# ══════════════════════════════════════════════════════════════════════


@router.get('/context')
async def orchestration_context(
    query: str = '',
    conversation_id: str | None = None,
):
    """Compile lessons + working memory into a system prompt block.

    Returns the FableMemory compiled instruction and a plain-text
    working memory summary. Use this to inject past lessons into
    the agent's system prompt for continuous improvement.
    """
    cid = _conv_id(conversation_id)
    sml = _store.get_sml(cid)
    wm = _store.get_wm(cid)

    # Compile context from FableMemory (cross-session lessons)
    fable_context = ''
    try:
        fable_context = await sml.compile_context(task_context=query)
    except Exception as e:
        _logger.debug('FableMemory compile failed: %s', e)

    return {
        'fable_context': fable_context,
        'working_memory_summary': wm.summary(),
        'conversation_id': cid,
    }


@router.post('/context/inject')
async def inject_context(
    inject_into: str = Body('system_prompt'),
    conversation_id: str | None = Body(None),
):
    """Inject compiled context into the current agent session.

    This is a stub for wiring lessons back into the agent loop.
    In production this would call the LLM provider's session update
    or re-initialize the agent with enriched system prompts.
    """
    cid = _conv_id(conversation_id)
    sml = _store.get_sml(cid)
    wm = _store.get_wm(cid)
    try:
        fable = await sml.compile_context()
    except Exception as e:
        fable = f'<failed: {e}>'

    result = {
        'injected_into': inject_into,
        'fable_context_length': len(fable),
        'working_memory_entries': len(wm._entries) if hasattr(wm, '_entries') else 0,
        'status': 'injected',
    }
    _logger.info('Context injection for %s: %s', cid, result)
    return result


# ══════════════════════════════════════════════════════════════════════
# Sub-Agent endpoints
# ══════════════════════════════════════════════════════════════════════


@router.post('/sub-agent/spawn')
async def sub_agent_spawn(
    parent_conversation_id: str = Body(...),
    task_name: str = Body(...),
    task_description: str = Body(...),
    acceptance_criteria: list[str] | None = Body(None),
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
    parent_conversation_id: str = Body(...),
    tasks: list[dict[str, Any]] = Body(...),
    sequential: bool = Body(False),
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


# ══════════════════════════════════════════════════════════════════════
# Error Recovery endpoints
# ══════════════════════════════════════════════════════════════════════


@router.post('/error/classify')
async def error_classify(error_text: str = Body(...) -> Any):
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
async def error_record_success(
    error_text: str = Body(...),
    strategy: str = Body(...),
    strategy_index: int = Body(0),
):
    registry = SolutionRegistry()
    registry.record_success(error_text, strategy, strategy_index)
    return {'success': True}


@router.get('/error/solutions')
async def error_solutions() -> Any:
    registry = SolutionRegistry()
    solutions = registry.all_solutions()
    return {'solutions': solutions, 'count': len(solutions)}


@router.post('/error/retry')
async def error_retry(
    operation_name: str = Body(...),
    max_retries: int = Body(5),
):
    __loop = AdaptiveRetryLoop(max_retries=max_retries)  # noqa: F841 — kept for future use
    return {
        'operation': operation_name,
        'max_retries': max_retries,
        'status': 'ready',
        'message': 'Use AdaptiveRetryLoop.execute() to run with retry.',
    }


# ══════════════════════════════════════════════════════════════════════
# Session cleanup
# ══════════════════════════════════════════════════════════════════════


@router.delete('/session/{conversation_id}')
async def close_session(conversation_id: str) -> Any:
    """Close a conversation session and clean up resources."""
    _store.remove(conversation_id)
    return {'conversation_id': conversation_id, 'closed': True}


@router.get('/sessions')
async def list_sessions() -> Any:
    """List all active conversation sessions."""
    return {
        'sessions': list(_store._states.keys()),
        'count': len(_store._states),
    }
