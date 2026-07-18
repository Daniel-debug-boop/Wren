"""Orchestrator checkpoint persistence — save/restore state to disk as JSON.

Allows MetaOrchestrator state to survive server restarts by writing
periodic checkpoints to a configurable directory. On restart, the
orchestrator can resume from the latest checkpoint (skipping completed
tasks, preserving cost tracking and budget).

What is persisted:
  - MetaOrchestratorState (goals processed, phase, error state)
  - TaskGraph (all tasks with status, results, dependencies)
  - ContextBudget (turn records, config, token counts)
  - ModelRouter cost summary (total cost, by-model, by-role)
  - RetryTracker (per-task retry counts and convergence state)
  - Child registry metadata (what was running, not active processes)
  - ProjectContext cache (source file reference)

What is NOT persisted (in-memory only):
  - Running asyncio Tasks / child agent processes
  - MessageBus connections and subscriptions
  - Circuit breaker in-memory counters
  - Progress callback references
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any

_logger = logging.getLogger(__name__)

_CHECKPOINT_VERSION = 1


@dataclass
class CheckpointMetadata:
    """Header metadata for every checkpoint file."""

    version: int = _CHECKPOINT_VERSION
    conversation_id: str = ''
    saved_at: float = 0.0
    task_count: int = 0
    completed_count: int = 0
    phase: str = ''


class CheckpointManager:
    """Manages save/load of orchestrator checkpoints to a directory.

    Each conversation gets its own checkpoint file:
      ``<persistence_dir>/checkpoints/orch_<conv_id>.json``

    No locking is needed since the MetaOrchestrator is single-process
    and checkpoint writes are serialised by the event loop.
    """

    def __init__(self, persistence_dir: str) -> None:
        self._base_dir = persistence_dir
        self._checkpoint_dir = os.path.join(persistence_dir, 'checkpoints')
        os.makedirs(self._checkpoint_dir, exist_ok=True)

    # ── Path helpers ────────────────────────────────────────────

    def _path(self, conv_id: str) -> str:
        return os.path.join(self._checkpoint_dir, f'orch_{conv_id}.json')

    def _tmp_path(self, conv_id: str) -> str:
        return os.path.join(self._checkpoint_dir, f'orch_{conv_id}.tmp.json')

    # ── Save ────────────────────────────────────────────────────

    async def save(self, conv_id: str, state: dict[str, Any]) -> None:
        """Write a checkpoint for the given conversation.

        Writes to a .tmp file first, then atomically renames to the
        final path to avoid partial writes on crash.
        """
        if not conv_id:
            return

        payload = {
            'checkpoint_version': _CHECKPOINT_VERSION,
            'saved_at': time.time(),
            'conversation_id': conv_id,
            'state': state,
        }

        tmp_path = self._tmp_path(conv_id)
        final_path = self._path(conv_id)

        # Write in a thread to avoid blocking the event loop
        def _write() -> None:
            with open(tmp_path, 'w') as f:
                json.dump(payload, f, indent=2, default=str)
            os.replace(tmp_path, final_path)

        await asyncio.to_thread(_write)
        _logger.debug('Checkpoint saved for %s (%d keys)', conv_id, len(state))

    # ── Load ────────────────────────────────────────────────────

    async def load(self, conv_id: str) -> dict[str, Any] | None:
        """Load the latest checkpoint for a conversation.

        Returns None if no checkpoint exists or if it's corrupted.
        """
        path = self._path(conv_id)
        if not os.path.isfile(path):
            return None

        def _read() -> dict[str, Any] | None:
            try:
                with open(path) as f:
                    data: dict[str, Any] = json.load(f)
                return data
            except (json.JSONDecodeError, OSError) as e:
                _logger.warning('Checkpoint corrupt for %s: %s', conv_id, e)
                return None

        data = await asyncio.to_thread(_read)
        if data is None:
            return None

        state = data.get('state')
        if state is None:
            return None

        _logger.info(
            'Checkpoint loaded for %s (version=%s, phase=%s)',
            conv_id,
            data.get('checkpoint_version', '?'),
            state.get('current_phase', '?'),
        )
        return state

    # ── Exists / Delete ─────────────────────────────────────────

    def has_checkpoint(self, conv_id: str) -> bool:
        return os.path.isfile(self._path(conv_id))

    def delete(self, conv_id: str) -> None:
        path = self._path(conv_id)
        tmp_path = self._tmp_path(conv_id)
        for p in (path, tmp_path):
            if os.path.isfile(p):
                os.remove(p)

    def list_conversations(self) -> list[str]:
        """List all conversation IDs that have checkpoints."""
        conv_ids: list[str] = []
        prefix = 'orch_'
        suffix = '.json'
        for fname in os.listdir(self._checkpoint_dir):
            if fname.startswith(prefix) and fname.endswith(suffix) and 'tmp.' not in fname:
                conv_id = fname[len(prefix):-len(suffix)]
                conv_ids.append(conv_id)
        return conv_ids


# ═══════════════════════════════════════════════════════════════
#  State serialization helpers
# ═══════════════════════════════════════════════════════════════

def serialize_orchestrator_state(orch: Any) -> dict[str, Any]:
    """Extract serializable state from a MetaOrchestrator instance.

    This function is called by the orchestrator to produce a snapshot
    of its current state for checkpointing.

    Args:
        orch: A MetaOrchestrator instance (typed Any to avoid import
              circularity at module level).

    Returns:
        A JSON-serializable dict with all persistable state.
    """
    return {
        'current_phase': getattr(orch._state, 'current_phase', 'idle'),
        'goals_processed': getattr(orch._state, 'goals_processed', 0),
        'children_spawned': getattr(orch._state, 'children_spawned', 0),
        'children_completed': getattr(orch._state, 'children_completed', 0),
        'children_failed': getattr(orch._state, 'children_failed', 0),
        'errors': getattr(orch._state, 'errors', 0),
        'last_error': getattr(orch._state, 'last_error', ''),
        'started_at': getattr(orch._state, 'started_at', 0.0),
        # Task graph serialization (if available)
        'tasks': _serialize_task_graph(getattr(orch, '_task_graph', None)),
        # Context budget serialization
        'context_budget': _serialize_context_budget(getattr(orch, '_context_budget', None)),
        # Model router cost summary
        'model_router': _serialize_model_router(getattr(orch, '_model_router', None)),
        # Retry tracker
        'retry_states': _serialize_retry_tracker(getattr(orch, '_retry_tracker', {})),
        # Error recovery config
        'error_recovery': _serialize_error_recovery_config(getattr(orch, '_error_recovery_config', None)),
        # Project context reference
        'project_context': _serialize_project_context(getattr(orch, '_project_context', None)),
        # Child registry metadata
        'children': _serialize_children(getattr(orch, '_children', {})),
    }


def restore_orchestrator_state(orch: Any, state: dict[str, Any]) -> None:
    """Restore orchestrator state from a checkpoint dict.

    Only restores fields that are safe to overwrite — skips running
    state like child agent processes or bus connections.
    """
    if not state:
        return

    # ── MetaOrchestratorState ──
    s = orch._state
    s.current_phase = state.get('current_phase', s.current_phase)
    s.goals_processed = state.get('goals_processed', s.goals_processed)
    s.children_spawned = state.get('children_spawned', s.children_spawned)
    s.children_completed = state.get('children_completed', s.children_completed)
    s.children_failed = state.get('children_failed', s.children_failed)
    s.errors = state.get('errors', s.errors)
    s.last_error = state.get('last_error', s.last_error)

    # Only restore started_at if this is a true resume (not a fresh start)
    restored_started = state.get('started_at', 0.0)
    if restored_started:
        s.started_at = restored_started

    # ── Task graph ──
    _restore_task_graph(orch, state.get('tasks', []))

    # ── Context budget ──
    _restore_context_budget(orch, state.get('context_budget'))

    # ── Model router cost summary ──
    _restore_model_router(orch, state.get('model_router'))

    # ── Retry tracker ──
    _restore_retry_tracker(orch, state.get('retry_states', {}))

    # ── Error recovery config ──
    _restore_error_recovery_config(orch, state.get('error_recovery'))

    _logger.info(
        'Orchestrator state restored: phase=%s, goals=%d, tasks=%d children=%d',
        s.current_phase,
        s.goals_processed,
        len(state.get('tasks', [])),
        state.get('children_spawned', 0),
    )


# ── Task graph serialization ─────────────────────────────────

def _serialize_task_graph(graph: Any) -> list[dict[str, Any]]:
    if graph is None:
        return []
    tasks = []
    # TaskGraph._tasks is a dict[str, PrioritizedTask]
    raw_tasks = getattr(graph, '_tasks', {})
    for tid, t in raw_tasks.items():
        tasks.append({
            'id': getattr(t, 'id', tid),
            'name': getattr(t, 'name', ''),
            'description': getattr(t, 'description', ''),
            'priority': getattr(t, 'priority', 50),
            'depends_on': getattr(t, 'depends_on', []),
            'status': getattr(t, 'status', 'pending').value
            if hasattr(getattr(t, 'status', ''), 'value')
            else str(getattr(t, 'status', 'pending')),
            'result': getattr(t, 'result', None),
            'error': getattr(t, 'error', ''),
            'metadata': getattr(t, 'metadata', {}),
        })
    return tasks


def _restore_task_graph(orch: Any, tasks_data: list[dict[str, Any]]) -> None:
    """Restore tasks into the orchestrator's task graph."""
    graph = getattr(orch, '_task_graph', None)
    if graph is None or not tasks_data:
        return

    from wren.harness.task_graph import PrioritizedTask, TaskStatus

    raw_tasks = getattr(graph, '_tasks', {})
    restored_count = 0

    for td in tasks_data:
        tid = td.get('id', '')
        if not tid or tid in raw_tasks:
            continue  # Don't overwrite existing tasks

        # Find the right status enum
        status_str = td.get('status', 'pending')
        try:
            status = TaskStatus(status_str)
        except ValueError:
            status = TaskStatus.PENDING

        task = PrioritizedTask(
            id=tid,
            name=td.get('name', ''),
            description=td.get('description', ''),
            priority=td.get('priority', 50),
            depends_on=td.get('depends_on', []),
            status=status,
            result=td.get('result'),
            error=td.get('error', ''),
            metadata=td.get('metadata', {}),
        )
        raw_tasks[tid] = task
        restored_count += 1

    if restored_count:
        _logger.debug('Restored %d tasks from checkpoint', restored_count)


# ── Context budget serialization ─────────────────────────────

def _serialize_context_budget(budget: Any) -> dict[str, Any] | None:
    if budget is None:
        return None

    config = getattr(budget, 'config', None)
    turns = getattr(budget, '_turns', [])

    turn_list = []
    for t in turns:
        turn_list.append({
            'role': getattr(t, 'role', ''),
            'input_tokens': getattr(t, 'input_tokens', 0),
            'output_tokens': getattr(t, 'output_tokens', 0),
            'content_preview': getattr(t, 'content_preview', ''),
            'model_used': getattr(t, 'model_used', ''),
            'estimated_cost_usd': getattr(t, 'estimated_cost_usd', 0.0),
        })

    return {
        'config': {
            'active_window_tokens': getattr(config, 'active_window_tokens', 32_000),
            'pruning_threshold_tokens': getattr(config, 'pruning_threshold_tokens', 64_000),
            'hard_cap_tokens': getattr(config, 'hard_cap_tokens', 128_000),
            'preserve_recent_turns': getattr(config, 'preserve_recent_turns', 5),
        } if config else {},
        'turns': turn_list,
    }


def _restore_context_budget(orch: Any, data: dict[str, Any] | None) -> None:
    """Restore context budget config and recent turns from checkpoint.

    Skips restoring individual turn records (which would re-add previously
    pruned turns) and only restores the config. The budget will be rebuilt
    naturally as new tasks execute.
    """
    if data is None:
        return
    budget = getattr(orch, '_context_budget', None)
    if budget is None:
        return

    # Restore config only (turns are rebuilt as tasks execute)
    cfg_data = data.get('config', {})
    cfg = getattr(budget, 'config', None)
    if cfg:
        for key in ('active_window_tokens', 'pruning_threshold_tokens', 'hard_cap_tokens'):
            val = cfg_data.get(key)
            if val is not None and hasattr(cfg, key):
                setattr(cfg, key, val)


# ── Model router serialization ──────────────────────────────

def _serialize_model_router(router: Any) -> dict[str, Any] | None:
    if router is None:
        return None
    cost_fn = getattr(router, 'cost_summary', None)
    if not cost_fn:
        return None
    return cost_fn()  # Already a dict


def _restore_model_router(orch: Any, data: dict[str, Any] | None) -> None:
    """Restore cost tracking into ModelRouter's accumulators."""
    if data is None:
        return
    router = getattr(orch, '_model_router', None)
    if router is None:
        return

    # ModelRouter uses simple counters: total_tokens, total_cost_usd, by_model, by_role
    # Set them directly if the fields exist
    for key in ('total_tokens', 'total_cost_usd'):
        val = data.get(key)
        if val is not None and hasattr(router, key):
            setattr(router, key, val)

    for dict_key in ('by_model', 'by_role'):
        val = data.get(dict_key, {})
        if val and hasattr(router, dict_key):
            existing = getattr(router, dict_key, {})
            for k, v in val.items():
                existing[k] = v


# ── Retry tracker serialization ─────────────────────────────

def _serialize_retry_tracker(tracker: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        tid: {
            'retry_count': getattr(rs, 'retry_count', 0),
            'max_retries': getattr(rs, 'max_retries', 3),
            'last_failure_signature': getattr(rs, 'last_failure_signature', ''),
            'convergence_count': getattr(rs, 'convergence_count', 0),
        }
        for tid, rs in tracker.items()
    }


def _restore_retry_tracker(orch: Any, data: dict[str, dict[str, Any]]) -> None:
    """Restore retry state for each tracked task.

    Uses a lazy import of RetryState to avoid circular dependency
    (meta_orchestrator imports from persistence).
    """
    if not data:
        return
    from wren.harness.meta_orchestrator import RetryState

    tracker = getattr(orch, '_retry_tracker', {})
    for tid, rs_data in data.items():
        tracker[tid] = RetryState(
            retry_count=rs_data.get('retry_count', 0),
            max_retries=rs_data.get('max_retries', 3),
            last_failure_signature=rs_data.get('last_failure_signature', ''),
            convergence_count=rs_data.get('convergence_count', 0),
        )


# ── Error recovery config serialization ─────────────────────

def _serialize_error_recovery_config(cfg: Any) -> dict[str, Any] | None:
    if cfg is None:
        return None
    return {
        'max_retries': getattr(cfg, 'max_retries', 3),
        'convergence_threshold': getattr(cfg, 'convergence_threshold', 2),
        'enable_auto_recovery': getattr(cfg, 'enable_auto_recovery', True),
    }


def _restore_error_recovery_config(orch: Any, data: dict[str, Any] | None) -> None:
    if data is None:
        return
    cfg = getattr(orch, '_error_recovery_config', None)
    if cfg is None:
        return
    for key in ('max_retries', 'convergence_threshold', 'enable_auto_recovery'):
        val = data.get(key)
        if val is not None and hasattr(cfg, key):
            setattr(cfg, key, val)


# ── Project context serialization ───────────────────────────

def _serialize_project_context(ctx: Any) -> dict[str, Any] | None:
    if ctx is None:
        return None
    return {
        'source_file': getattr(ctx, 'source_file', ''),
        'found': getattr(ctx, 'found', False),
        'raw_content': getattr(ctx, 'raw_content', ''),
    }


# ── Children serialization ──────────────────────────────────

def _serialize_children(children: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for aid, child in children.items():
        handle = getattr(child, 'handle', None)
        result.append({
            'agent_id': aid,
            'agent_type': getattr(child, 'agent_type', getattr(handle, 'agent_type', '')),
            'status': getattr(handle, 'status', 'unknown').value
            if hasattr(getattr(handle, 'status', ''), 'value')
            else str(getattr(handle, 'status', 'unknown')),
            'task_name': getattr(handle, 'task_name', ''),
        })
    return result
