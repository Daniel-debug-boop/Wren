"""Meta-Orchestrator (v2) — PARENT CONTROLLER.

Spawns child agent instances dynamically based on goal decomposition.
Manages their full lifecycle: create → init → assign task → monitor →
collect → reap. All child agents communicate ONLY through the message
bus. Budgets enforced at the parent level.

This is the brain. No agent runs without going through here.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from wren.harness.circuit_breaker import CircuitBreaker
from wren.harness.context_budget import ContextBudget, ContextBudgetConfig
from wren.harness.storage.store import Store
from wren.harness.task_graph import PrioritizedTask, TaskGraph, TaskStatus
from wren.harness.config import HarnessConfig
from wren.harness.resource_budget import ResourceBudget
from wren.harness.message_bus import (
    AgentMessage,
    MessageBus,
    MessagePriority,
    MessageType,
)
from wren.harness.knowledge.vector_store import VectorStore
from wren.harness.knowledge.working_memory_rag import WorkingMemoryRAG
from wren.harness.knowledge.skill_library import SkillLibrary
from wren.harness.reflection.self_critique import SelfCritiqueAgent
from wren.harness.agents.base import AgentHandle, AgentStatus, ChildAgent
from wren.harness.agents.coding_harness import CodingHarness
from wren.harness.agents.research_agent import ResearchAgent
from wren.harness.agents.planner_agent import PlannerAgent
from wren.harness.agents.writer_agent import WriterAgent
from wren.harness.agents.reviewer_agent import ReviewerAgent
from wren.harness.agents.dark_factory import DarkFactory
from wren.harness.agents.hitl_console import HITLConsole
from wren.harness.persistence import CheckpointManager, serialize_orchestrator_state, restore_orchestrator_state
from wren.harness.project_context import ProjectContext, ProjectContextLoader
from wren.harness.sandbox.execution_sandbox import ExecutionSandbox

_logger = logging.getLogger(__name__)

_MAX_CHILDREN = 10  # max concurrently running child agents
_CHILD_TIMEOUT_S = 300.0  # max time a child can run before parent reclaims


@dataclass
class MetaOrchestratorState:
    conversation_id: str = ''
    started_at: float = field(default_factory=time.time)
    goals_processed: int = 0
    children_spawned: int = 0
    children_completed: int = 0
    children_failed: int = 0
    errors: int = 0
    last_error: str = ''
    current_phase: str = 'idle'


@dataclass
class ErrorRecoveryConfig:
    """Configuration for the error recovery retry loop.

    When a reviewer finds blockers in generated code, the orchestrator
    can re-spawn the writer with the review feedback as context, then
    re-run the reviewer. This loop repeats until:
    - max_retries is reached
    - the failure pattern converges (same failures N times in a row)
    - the reviewer passes
    """

    max_retries: int = 3
    convergence_threshold: int = 2  # same failure hash N consecutive times → stop
    enable_auto_recovery: bool = True


@dataclass
class RetryState:
    """Per-task retry tracking for the error recovery loop."""

    retry_count: int = 0
    max_retries: int = 3
    previous_review_results: list[dict] = field(default_factory=list)
    last_failure_signature: str = ''
    convergence_count: int = 0


class MetaOrchestrator:
    """Parent controller — spawns, monitors, and reaps child agents.

    Usage:
        mo = MetaOrchestrator('conv_123')
        await mo.start()
        result = await mo.process_goal('Build a full-stack web app')
        await mo.shutdown()
    """

    def __init__(
        self, conversation_id: str = '', config: HarnessConfig | None = None
    ) -> None:
        self._conv_id = conversation_id
        self._cfg = config or HarnessConfig()
        self._state = MetaOrchestratorState(conversation_id=conversation_id)

        # Auth layer
        self._auth = BusAuth()
        self._orch_token = self._auth.issue_token('meta_orchestrator', 'orchestrator')

        # Core infrastructure (owned by parent, shared with children)
        self._bus = MessageBus(auth=self._auth)
        self._budget = ResourceBudget(limits=self._cfg.budget_limits)
        self._sandbox = ExecutionSandbox(message_bus=self._bus, budget=self._budget)

        # Health & telemetry
        self._health = HealthChecker()

        T.info(
            'orchestrator.init',
            'MetaOrchestrator initialised',
            conversation_id=conversation_id,
        )

        # Knowledge layer
        self._vs = VectorStore(persist_path=self._cfg.vector_persist_path)
        self._rag = WorkingMemoryRAG(vector_store=self._vs)
        self._skill_lib = SkillLibrary(vector_store=self._vs)

        # Reflection layer
        self._critiquer = SelfCritiqueAgent()
        self._fact_checker = FactChecker()
        self._quality = QualityGates()

        # Model router — API-key-aware model selection
        self._model_router = ModelRouter()

        # Error recovery — retry loop for reviewer failures
        self._error_recovery_config = ErrorRecoveryConfig()
        self._retry_tracker: dict[str, RetryState] = {}

        # Project context — WREN.md / CLAUDE.md from sandbox workspace
        self._project_context: ProjectContext | None = None
        self._project_loader = ProjectContextLoader(self._sandbox)

        # Checkpoint persistence — survives server restarts
        self._checkpoint_mgr = CheckpointManager(self._cfg.db_path)
        self._auto_checkpoint = True

        # Context budget — token tracking & auto-pruning
        self._context_budget = ContextBudget(
            ContextBudgetConfig(
                active_window_tokens=32_000,
                pruning_threshold_tokens=64_000,
                hard_cap_tokens=128_000,
                preserve_recent_turns=5,
            )
        )

        # SDK integration — tool registry, capability manifest, guardrails
        try:
            from wren.harness.sdk_wiring import get_sdk_context

            self._sdk_ctx = get_sdk_context()
            T.info(
                'orchestrator.sdk_init',
                f'SDK wiring loaded: {len(self._sdk_ctx.registry.list_all())} tools, '
                f'{len(self._sdk_ctx.enforcer._guardrails)} guardrails',
            )
        except Exception as e:
            self._sdk_ctx = None
            _logger.warning('SDK wiring unavailable: %s', e)

        # Background services
        self._dark = DarkFactory(max_concurrent=2)
        self._hitl = HITLConsole(notify_callback=self._on_hitl_request)

        # Child agent registry — ALL spawned children live here
        self._children: dict[str, ChildAgent] = {}
        self._child_tokens: dict[str, str] = {}  # agent_id -> auth token
        self._child_tasks: dict[str, asyncio.Task] = {}

        # Background tasks
        self._bg_tasks: list[asyncio.Task] = []
        self._running = False

        # Circuit breaker for child execution
        self._circuit_breaker = CircuitBreaker(
            'child_execution', threshold=3, recovery_timeout_s=30.0
        )

        # Progress callback — called with dict on each child status change
        self._progress_callback = None

        # Task graph reference (for checkpoint serialization)
        self._task_graph: TaskGraph | None = None

        # Register bus subscribers
        self._bus.subscribe('error', self._on_error_message)
        self._bus.subscribe(
            MessageType.APPROVAL_REQUEST.value, self._on_approval_request
        )
        self._bus.subscribe('progress', self._on_progress_message)

    # ═══════════════════════════════════════════════════════════
    #  LIFECYCLE
    # ═══════════════════════════════════════════════════════════

    async def start(self) -> None:
        """Start all background services."""
        self._running = True
        self._state.current_phase = 'planning'

        if self._cfg.auto_start_bus:
            self._bg_tasks.append(asyncio.create_task(self._bus.start()))
        if self._cfg.auto_start_dark_factory:
            self._bg_tasks.append(asyncio.create_task(self._dark.start()))

        # Child monitor — watches for hung children
        self._bg_tasks.append(asyncio.create_task(self._monitor_children()))

        # Load skills
        await asyncio.to_thread(self._skill_lib.load_all)

        # Load project context from sandbox workspace (WREN.md/CLAUDE.md)
        self._project_context = await self._project_loader.load()
        if self._project_context and self._project_context.found:
            _logger.info(
                'MetaOrchestrator: loaded project context from %s',
                self._project_context.source_file,
            )

        _logger.info('MetaOrchestrator: started conv=%s', self._conv_id)

    async def shutdown(self, grace_period_s: float = 5.0) -> None:
        """Shut down everything: drain children, stop services.

        Args:
            grace_period_s: Seconds to wait for running children to finish
                            before force-killing them.
        """
        self._running = False
        self._state.current_phase = 'shutting_down'
        T.info('orchestrator.shutdown', f'grace={grace_period_s}s conv={self._conv_id}')

        # Draining phase — give running children grace_period_s to finish
        busy = [
            aid
            for aid, child in self._children.items()
            if child.handle.status == AgentStatus.BUSY
        ]
        if busy and grace_period_s > 0:
            _logger.info(
                'MetaOrchestrator: draining %d busy children (%.0fs)',
                len(busy),
                grace_period_s,
            )
            await asyncio.sleep(min(grace_period_s, 5.0))

        # Kill all child agents
        for aid, child in list(self._children.items()):
            await self._kill_child(aid)
        self._children.clear()
        self._child_tokens.clear()
        self._child_tasks.clear()

        # Stop background services
        self._bus.stop()
        self._dark.stop()
        for t in self._bg_tasks:
            if not t.done():
                t.cancel()
        if self._bg_tasks:
            await asyncio.gather(*self._bg_tasks, return_exceptions=True)
        self._bg_tasks.clear()

        self._state.current_phase = 'done'
        _logger.info('MetaOrchestrator: shutdown conv=%s', self._conv_id)

    # ═══════════════════════════════════════════════════════════
    #  CHILD AGENT SPAWNING
    # ═══════════════════════════════════════════════════════════

    async def spawn_agent(
        self,
        agent_type: str,
        task_desc: str = '',
        budget_slice: ResourceBudget | None = None,
    ) -> AgentHandle:
        """Spawn a child agent, init it, and return its handle.

        The child runs as an asyncio task. The parent owns the
        task and can kill it at any time.
        """
        if len(self._children) >= self._cfg.max_concurrent_children:
            raise RuntimeError(
                f'Max children ({self._cfg.max_concurrent_children}) reached'
            )

        # Create the right agent type
        child = self._create_agent(agent_type)
        if not child:
            raise ValueError(f'Unknown agent type: {agent_type}')

        self._children[child.agent_id] = child
        self._state.children_spawned += 1

        # Issue auth token for this child
        token = self._auth.issue_token(child.agent_id, agent_type)
        self._child_tokens[child.agent_id] = token

        # Init with budget, bus & auth token
        await child.init(
            budget=budget_slice or self._budget, bus=self._bus, token=token
        )

        # Persist to Store
        Store.save_child(child.agent_id, agent_type, 'idle', task_name='')

        T.info(
            'child.spawned',
            f'{agent_type} spawned',
            agent_id=child.agent_id[:12],
            agent_type=agent_type,
        )

        # Emit progress
        await self._emit_progress(child.agent_id, 'spawned', task_name='')
        return child.handle

    async def assign_and_run(
        self,
        handle: AgentHandle,
        task: dict[str, Any],
        reap: bool = True,
    ) -> Any:
        """Assign a task to a spawned child and wait for result.

        The child runs in a tracked asyncio task so the parent
        can kill it if it times out. Guarded by circuit breaker
        for error cascading. After completion the child is reaped
        (removed from registry) by default.
        """
        child = self._children.get(handle.agent_id)
        if not child:
            raise RuntimeError(f'Child {handle.agent_id} not found')

        task_name = task.get('name', 'unnamed')
        await self._emit_progress(handle.agent_id, 'assigned', task_name=task_name)

        async def _run_child() -> Any:
            try:
                return await child.receive_task(task)
            except Exception:
                raise

        task_obj = asyncio.create_task(_run_child())
        self._child_tasks[handle.agent_id] = task_obj

        try:
            start = time.time()

            async def _timed_run():
                return await asyncio.wait_for(
                    task_obj, timeout=self._cfg.child_timeout_s
                )

            result = await self._circuit_breaker.call(_timed_run)
            elapsed = time.time() - start
            if handle.status == AgentStatus.COMPLETED:
                self._state.children_completed += 1
                T.info(
                    'child.completed',
                    f'task={task_name} elapsed={elapsed:.1f}s',
                    agent_id=handle.agent_id[:12],
                    duration_s=round(elapsed, 1),
                )
            else:
                self._state.children_failed += 1
                T.warn(
                    'child.failed',
                    f'task={task_name} elapsed={elapsed:.1f}s',
                    agent_id=handle.agent_id[:12],
                )
            await self._emit_progress(
                handle.agent_id, handle.status.value, task_name=task_name
            )
            if reap:
                await self._kill_child(handle.agent_id)
            T.metric('children_completed')
            return result
        except asyncio.TimeoutError:
            T.error(
                'child.timeout',
                f'task={task.get("name", "")} timeout={self._cfg.child_timeout_s}s',
                agent_id=handle.agent_id[:12],
            )
            await self._kill_child(handle.agent_id)
            self._state.children_failed += 1
            T.metric('children_timed_out')
            raise RuntimeError(
                f'Child {handle.agent_id} timed out after {self._cfg.child_timeout_s}s'
            )
        except Exception as e:
            self._state.children_failed += 1
            T.error('child.error', str(e), agent_id=handle.agent_id[:12])
            await self._kill_child(handle.agent_id)
            raise

    async def kill_agent(self, agent_id: str) -> None:
        """Kill a child agent immediately."""
        await self._kill_child(agent_id)

    def list_children(self) -> list[AgentHandle]:
        return [c.handle for c in self._children.values()]

    def get_child(self, agent_id: str) -> ChildAgent | None:
        return self._children.get(agent_id)

    # ── Internal child management ────────────────────────────

    def _create_agent(self, agent_type: str) -> ChildAgent | None:
        mapping: dict[str, type[ChildAgent]] = {
            'coding': CodingHarness,
            'research': ResearchAgent,
            'planner': PlannerAgent,
            'writer': WriterAgent,
            'reviewer': ReviewerAgent,
        }
        cls = mapping.get(agent_type)
        return cls() if cls else None

    async def _kill_child(self, agent_id: str) -> None:
        task_name = ''
        child = self._children.pop(agent_id, None)
        task = self._child_tasks.pop(agent_id, None)

        # Revoke auth token
        token = self._child_tokens.pop(agent_id, '')
        if token:
            self._auth.revoke_token(token)

        if child:
            task_name = child.handle.task_name
            await child.shutdown()
            child.handle.status = AgentStatus.KILLED
            Store.save_child(agent_id, child.agent_type, 'killed')
            await self._emit_progress(agent_id, 'killed', task_name=task_name)

        if task and not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

    async def _monitor_children(self) -> None:
        """Background loop: reap timed-out children."""
        while self._running:
            await asyncio.sleep(5.0)
            now = time.time()
            for aid, child in list(self._children.items()):
                age = now - child.handle.spawned_at
                if (
                    age > self._cfg.child_timeout_s
                    and child.handle.status == AgentStatus.BUSY
                ):
                    _logger.warning(
                        'MetaOrchestrator: reaping hung child %s (age=%.0fs)',
                        aid[:12],
                        age,
                    )
                    await self._kill_child(aid)

    # ═══════════════════════════════════════════════════════════
    #  GOAL PROCESSING
    # ═══════════════════════════════════════════════════════════

    async def process_goal(self, goal: str) -> dict[str, Any]:
        """Main entry: decompose goal → spawn children → execute → reflect."""
        _logger.info('MetaOrchestrator: processing goal="%s"', goal[:80])
        self._state.goals_processed += 1
        self._state.current_phase = 'planning'

        intent = await self._analyse_goal(goal)
        tasks = self._decompose_goal(intent)

        # Build task graph
        graph = TaskGraph()
        for t in tasks:
            graph.add(t)
        self._task_graph = graph  # keep reference for checkpointing

        self._rag.store(goal, source='user_goal', tags=['goal'])

        # Execute task graph by spawning children for each task
        self._state.current_phase = 'executing'
        results = await self._execute_graph(graph)

        # Reflect
        self._state.current_phase = 'reflecting'
        reflection = await self._reflect(results, goal)

        self._state.current_phase = 'idle'

        # Save checkpoint after goal completes
        if self._auto_checkpoint:
            await self.save_checkpoint()

        return {
            'goal': goal[:200],
            'intent': intent,
            'task_count': len(tasks),
            'children_spawned': self._state.children_spawned,
            'children_completed': self._state.children_completed,
            'results': results,
            'reflection': reflection,
        }

    async def process_message(self, message: str, source: str = 'user') -> str:
        """Process an incoming user message."""
        self._rag.store(message, source=source, tags=['message'])
        ctx = self._rag.retrieve(message)

        if self._is_goal_like(message):
            result = await self.process_goal(message)
            lines = [
                f'Goal decomposed into {result["task_count"]} tasks.',
                f'Children spawned: {result["children_spawned"]}',
                f'Completed: {result["children_completed"]}',
            ]
            return '\n'.join(lines)
        return ctx.to_prompt_suffix()

    # ═══════════════════════════════════════════════════════════
    #  TASK GRAPH EXECUTION (spawns children per task)
    # ═══════════════════════════════════════════════════════════

    async def _execute_graph(self, graph: TaskGraph) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        while not graph.is_complete():
            ready = graph.ready(max_count=self._cfg.max_concurrent_children)
            if not ready:
                if graph.has_failures():
                    break
                await asyncio.sleep(0.1)
                continue

            batch_results = await asyncio.gather(
                *[self._execute_task_via_child(t) for t in ready],
                return_exceptions=True,
            )

            for task, outcome in zip(ready, batch_results):
                if isinstance(outcome, Exception):
                    self._state.errors += 1
                    self._state.last_error = str(outcome)
                    graph.update_status(task.id, TaskStatus.FAILED, error=str(outcome))
                    results.append(
                        {
                            'task_id': task.id,
                            'name': task.name,
                            'success': False,
                            'error': str(outcome)[:200],
                        }
                    )
                else:
                    graph.update_status(task.id, TaskStatus.COMPLETED, result=outcome)
                    results.append(
                        {
                            'task_id': task.id,
                            'name': task.name,
                            'success': True,
                            'result': outcome,
                        }
                    )

                # ── Checkpoint after each task ──
                if self._auto_checkpoint and self._conv_id:
                    await self.save_checkpoint()

                # ── Error Recovery: check if reviewer needs retry ──
                if (
                    isinstance(outcome, dict)
                    and self._error_recovery_config.enable_auto_recovery
                ):
                    await self._maybe_retry_reviewer(graph, task, outcome, results)

        # Strip stale retrying markers that were superseded by real results
        final_task_ids = {r['task_id'] for r in results if not r.get('retrying')}
        results[:] = [
            r for r in results
            if not (r.get('retrying') and r['task_id'] in final_task_ids)
        ]

        return results

    async def _execute_task_via_child(self, task: PrioritizedTask) -> Any:
        """Select agent type, spawn child, assign task, collect result."""
        agent_type = self._classify_task(task)
        handle = await self.spawn_agent(agent_type, task_desc=task.description)

        task_dict: dict[str, Any] = {
            'name': task.name,
            'description': task.description,
            'priority': task.priority,
            'metadata': task.metadata,
        }

        # Inject project context for planner tasks
        if agent_type == 'planner' and self._project_context and self._project_context.found:
            task_dict['project_context'] = self._project_context

        # Inject review_feedback from metadata for writer retries
        review_feedback = task.metadata.get('review_feedback')
        if review_feedback:
            task_dict['review_feedback'] = review_feedback

        result = await self.assign_and_run(handle, task_dict)

        # ── Track token usage in context budget ──
        self._track_task_cost(agent_type, task, result)

        return result

    def _track_task_cost(self, agent_type: str, task: PrioritizedTask, result: Any) -> None:
        """Record token usage for a completed task in the context budget.

        Estimates token counts from task complexity and result size.
        In a production system, these would come from actual API response metadata.
        """
        input_est = len(task.description) * 4  # rough char→token estimate
        output_est = 0
        model_used = ''

        if isinstance(result, dict):
            if 'duration_s' in result:
                output_est = int(result.get('duration_s', 0) * 100)
            if 'write_result' in result:
                wr = result['write_result']
                output_est = sum(r.get('token_count', 100) for r in wr.get('results', []))
            if 'review' in result:
                output_est = len(str(result.get('review', ''))) // 4

        # Get the selected model for this agent type
        try:
            model_selection = self.select_model_for_agent(agent_type, task.description)
            model_used = model_selection.primary_model.name
            estimated_cost = model_selection.estimated_cost_usd
            self._model_router.record_call(
                model_name=model_used,
                role=agent_type,
                input_tokens=input_est,
                output_tokens=output_est,
            )
        except Exception:
            estimated_cost = 0.0

        # Record in context budget
        self._context_budget.record_turn(
            role=f'agent_{agent_type}',
            input_tokens=input_est,
            output_tokens=output_est,
            content_preview=f"Task: {task.description[:100]} | Result: {str(result)[:100]}",
            model_used=model_used,
            estimated_cost_usd=estimated_cost,
        )

        # Prune if needed
        if self._context_budget.needs_pruning():
            pruned = self._context_budget.prune()
            if pruned:
                _logger.info(
                    'ContextBudget: pruned %d turns, usage now at %.1f%% of hard cap',
                    len(pruned),
                    self._context_budget.usage_pct() * 100,
                )

        # Enforce hard cap — raise when conversation exceeds model context limit
        if self._context_budget.at_capacity():
            from wren.harness.resource_budget import BudgetExceeded
            raise BudgetExceeded(
                'context_tokens',
                self._context_budget.config.hard_cap_tokens,
                self._context_budget.current_tokens(),
            )

    # ═══════════════════════════════════════════════════════════
    #  ERROR RECOVERY — REVIEWER → WRITER RETRY LOOP
    # ═══════════════════════════════════════════════════════════

    async def _maybe_retry_reviewer(
        self,
        graph: TaskGraph,
        task: PrioritizedTask,
        outcome: dict[str, Any],
        results: list[dict[str, Any]],
    ) -> None:
        """Check if a reviewer result needs retry and, if so, re-spawn
        the upstream writer tasks with the review feedback as context.

        Convergence detection: if the same failure pattern appears
        N consecutive retries, we abort (no point retrying the same
        thing). Max retries is also enforced.
        """
        # Only retry if reviewer flagged failures with blockers
        overall_passed = outcome.get(
            'overall_passed',
            outcome.get('review', {}).get('overall_passed', True),
        )
        if overall_passed:
            return

        blocker_count = outcome.get('blocker_count', outcome.get('review', {}).get('blocker_count', 0))
        if blocker_count == 0:
            # Minor warnings only — not worth retrying
            return

        # Get or create retry state for this task
        state = self._retry_tracker.setdefault(
            task.id,
            RetryState(max_retries=self._error_recovery_config.max_retries),
        )

        # Check max retries
        if state.retry_count >= state.max_retries:
            _logger.warning(
                'ErrorRecovery: max retries (%d) reached for %s — giving up',
                state.max_retries,
                task.name,
            )
            return

        # Compute failure signature for convergence check
        sig = self._compute_failure_signature(outcome)
        if sig == state.last_failure_signature:
            state.convergence_count += 1
        else:
            state.convergence_count = 0
        state.last_failure_signature = sig
        state.previous_review_results.append(outcome)

        # Check convergence
        if state.convergence_count >= self._error_recovery_config.convergence_threshold:
            _logger.info(
                'ErrorRecovery: converged (%d consecutive identical failures) for %s',
                state.convergence_count,
                task.name,
            )
            return

        # Find upstream writer/coding tasks that produced the reviewed output
        writer_tasks: list[PrioritizedTask] = []
        seen: set[str] = set()

        def _collect_upstream_writers(tid: str) -> None:
            if tid in seen:
                return
            seen.add(tid)
            dep = graph.get(tid)
            if not dep:
                return
            dep_type = self._classify_task(dep)
            if dep_type in ('writer', 'coding'):
                writer_tasks.append(dep)
            for parent_id in dep.depends_on:
                _collect_upstream_writers(parent_id)

        for dep_id in task.depends_on:
            _collect_upstream_writers(dep_id)

        if not writer_tasks:
            _logger.debug(
                'ErrorRecovery: no upstream writer tasks found for %s — cannot retry',
                task.name,
            )
            return

        state.retry_count += 1
        _logger.info(
            'ErrorRecovery: retry %d/%d for "%s" — re-running %d writer tasks with review feedback',
            state.retry_count,
            state.max_retries,
            task.name,
            len(writer_tasks),
        )

        # Extract actionable feedback from review
        review_feedback = self._extract_review_feedback(outcome)

        # Reset reviewer task to PENDING with retry metadata
        graph.update_status(task.id, TaskStatus.PENDING)
        task.metadata['review_feedback'] = review_feedback
        task.metadata['retry_count'] = state.retry_count

        # Reset upstream writer tasks to PENDING with review feedback
        for wt in writer_tasks:
            graph.update_status(wt.id, TaskStatus.PENDING)
            wt.metadata['review_feedback'] = review_feedback
            wt.metadata['retry_count'] = state.retry_count

        # Mark the last result entry for this task as 'retrying' so
        # downstream callers know it's being retried (not a final failure)
        for i, r in enumerate(results):
            if r.get('task_id') == task.id:
                results[i] = {
                    'task_id': task.id,
                    'name': task.name,
                    'success': False,
                    'retrying': True,
                    'retry_count': state.retry_count,
                }
                break
        else:
            # No existing entry — add a placeholder
            results.append({
                'task_id': task.id,
                'name': task.name,
                'success': False,
                'retrying': True,
                'retry_count': state.retry_count,
            })

        # Emit progress event for the retry
        await self._emit_progress(
            f'recovery_{task.id}',
            'retrying',
            task_name=f'{task.name} (retry {state.retry_count}/{state.max_retries})',
        )

    @staticmethod
    def _extract_review_feedback(review_result: dict[str, Any]) -> dict[str, Any]:
        """Extract actionable feedback from a review result for the writer.

        Produces a structured dict with:
        - summary: overall review summary
        - blockers: list of blocker-level failures with suggestions
        - files: per-file failure details with line numbers and fix suggestions
        - errors: all error-level failures
        """
        files = review_result.get('files', review_result.get('review', {}).get('files', []))

        blockers: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        file_failures: list[dict[str, Any]] = []

        for f in files:
            file_path = f.get('file_path', 'unknown')
            for check in f.get('checks', []):
                entry = {
                    'file_path': file_path,
                    'check_name': check.get('check_name', 'unknown'),
                    'message': check.get('message', ''),
                    'suggestion': check.get('suggestion', ''),
                    'line_number': check.get('line_number', 0),
                }
                severity = check.get('severity', 'info')
                if severity == 'blocker':
                    blockers.append(entry)
                elif severity == 'error':
                    errors.append(entry)
                if not check.get('passed', True):
                    file_failures.append(entry)

        return {
            'summary': review_result.get('summary', review_result.get('review', {}).get('summary', '')),
            'blockers': blockers,
            'errors': errors,
            'failures': file_failures,
            'total_failed': len(file_failures),
        }

    @staticmethod
    def _compute_failure_signature(review_result: dict[str, Any]) -> str:
        """Compute a deterministic hash of the failure pattern.

        Used for convergence detection: if the same failure signature
        appears repeatedly, no progress is being made and we should stop.
        """
        files = review_result.get('files', review_result.get('review', {}).get('files', []))
        failure_pairs: list[tuple[str, str]] = []

        for f in files:
            file_path = f.get('file_path', '')
            for check in f.get('checks', []):
                if not check.get('passed', True):
                    failure_pairs.append((
                        file_path,
                        check.get('check_name', 'unknown'),
                    ))

        failure_pairs.sort()
        raw = json.dumps(failure_pairs, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def _classify_task(task: PrioritizedTask) -> str:
        """Map task to agent type based on name/description.

        Uses the full agent suite: planner, researcher, writer, reviewer, coding.
        """
        name = task.name.lower()
        desc = task.description.lower()

        # Planner: planning, architecture, design, analysis
        if any(
            kw in name or kw in desc
            for kw in ['plan', 'architect', 'design', 'analyze', 'analyse', 'outline']
        ):
            return 'planner'

        # Researcher: research, search, find, learn, investigate
        if any(
            kw in name or kw in desc
            for kw in ['research', 'search', 'find', 'learn', 'investigate', 'lookup']
        ):
            return 'research'

        # Reviewer: review, verify, check, audit, lint, test
        if any(
            kw in name or kw in desc
            for kw in ['review', 'verify', 'check', 'audit', 'lint', 'test', 'validate']
        ):
            return 'reviewer'

        # Writer: write, implement, create, build, scaffold (code-focused)
        if any(
            kw in name or kw in desc
            for kw in ['write', 'implement', 'code', 'create file', 'modify', 'scaffold']
        ):
            return 'writer'

        return 'coding'  # default: coding harness handles general tasks

    # ═══════════════════════════════════════════════════════════
    #  GOAL ANALYSIS & DECOMPOSITION
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    async def _analyse_goal(goal: str) -> dict[str, Any]:
        gl = goal.lower()
        score = sum(
            [
                2
                if any(
                    kw in gl
                    for kw in ['code', 'build', 'implement', 'app', 'api', 'script']
                )
                else 0,
                2
                if any(
                    kw in gl
                    for kw in [' and ', 'then', 'after', 'first', 'finally', ',']
                )
                else 0,
                1
                if any(
                    kw in gl for kw in ['docker', 'deploy', 'test', 'browser', 'shell']
                )
                else 0,
                1
                if any(kw in gl for kw in ['research', 'find', 'search', 'what is'])
                else 0,
                1 if len(goal.split()) > 15 else 0,
            ]
        )
        has_code = any(
            kw in gl
            for kw in ['code', 'build', 'implement', 'write', 'app', 'api', 'script']
        )
        has_research = any(
            kw in gl for kw in ['research', 'find', 'search', 'learn', 'investigate']
        )
        return {
            'raw': goal[:200],
            'complexity': 'complex'
            if score >= 4
            else ('moderate' if score >= 2 else 'simple'),
            'type': 'project'
            if (has_code and score >= 3)
            else (
                'coding' if has_code else ('research' if has_research else 'general')
            ),
            'score': score,
        }

    @staticmethod
    def _is_goal_like(msg: str) -> bool:
        markers = [
            'build',
            'create',
            'implement',
            'develop',
            'make',
            'setup',
            'deploy',
            'migrate',
            'refactor',
            'write a',
        ]
        ml = msg.lower()
        return any(ml.startswith(m) for m in markers) or len(msg.split()) > 20

    def _decompose_goal(self, intent: dict[str, Any]) -> list[PrioritizedTask]:
        gtype = intent['type']
        if gtype == 'project':
            return [
                PrioritizedTask(
                    name='plan', description='Architecture & design plan', priority=80
                ),
                PrioritizedTask(
                    name='research',
                    description='Research required technologies',
                    depends_on=['plan'],
                    priority=70,
                ),
                PrioritizedTask(
                    name='scaffold',
                    description='Scaffold project structure',
                    depends_on=['research'],
                    priority=60,
                ),
                PrioritizedTask(
                    name='implement_core',
                    description='Implement core functionality',
                    depends_on=['scaffold'],
                    priority=50,
                ),
                PrioritizedTask(
                    name='implement_features',
                    description='Implement feature set',
                    depends_on=['implement_core'],
                    priority=40,
                ),
                PrioritizedTask(
                    name='test',
                    description='Write & run tests',
                    depends_on=['implement_features'],
                    priority=30,
                ),
                PrioritizedTask(
                    name='review',
                    description='Code review & quality check',
                    depends_on=['test'],
                    priority=20,
                ),
                PrioritizedTask(
                    name='deploy',
                    description='Deploy & verify',
                    depends_on=['review'],
                    priority=10,
                ),
            ]
        elif gtype == 'research':
            return [
                PrioritizedTask(
                    name='search', description='Search for information', priority=70
                ),
                PrioritizedTask(
                    name='analyse',
                    description='Analyse findings',
                    depends_on=['search'],
                    priority=50,
                ),
                PrioritizedTask(
                    name='synthesise',
                    description='Synthesise report',
                    depends_on=['analyse'],
                    priority=30,
                ),
            ]
        else:
            return [
                PrioritizedTask(
                    name='analyse', description='Analyse request', priority=70
                ),
                PrioritizedTask(
                    name='execute',
                    description='Execute response',
                    depends_on=['analyse'],
                    priority=50,
                ),
                PrioritizedTask(
                    name='verify',
                    description='Verify result',
                    depends_on=['execute'],
                    priority=30,
                ),
            ]

    # ═══════════════════════════════════════════════════════════
    #  REFLECTION
    # ═══════════════════════════════════════════════════════════

    async def _reflect(
        self, results: list[dict[str, Any]], goal: str
    ) -> dict[str, Any]:
        text = '\n'.join(str(r) for r in results)
        critique = self._critiquer.critique_text(text, source='harness')
        quality = await self._quality.run_all(
            {
                'response': text,
                'critique_score': critique.score,
                'blockers': [str(f) for f in critique.blockers],
            }
        )

        # Store learnings
        passed_count = sum(1 for r in results if r.get('success'))
        if passed_count == len(results):
            self._rag.store(
                f'Goal completed: {goal[:100]}',
                source='meta_orchestrator',
                tags=['success'],
            )

        return {
            'critique': critique.summary(),
            'quality': quality.summary(),
            'passed': quality.passed,
            'total_tasks': len(results),
            'passed_tasks': passed_count,
        }

    # ═══════════════════════════════════════════════════════════
    #  BUS HANDLERS
    # ═══════════════════════════════════════════════════════════

    async def _on_error_message(self, msg: AgentMessage) -> None:
        self._state.errors += 1
        self._state.last_error = str(msg.payload)

    async def _on_approval_request(self, msg: AgentMessage) -> None:
        if self._cfg.enable_hitl:
            await self._hitl.request_approval(
                title=msg.payload.get('title', 'Approval needed'),
                description=msg.payload.get('description', ''),
                timeout_s=self._cfg.hitl_timeout_s,
            )

    @staticmethod
    async def _on_hitl_request(req: Any) -> None:
        _logger.info('HITL: %s', req.title)

    # ═══════════════════════════════════════════════════════════
    #  PROGRESS STREAMING
    # ═══════════════════════════════════════════════════════════

    def set_progress_callback(self, callback) -> None:
        """Set a callback invoked on every child status change.

        Callback signature: async def cb(event: dict) or def cb(event: dict)
        Event keys: agent_id, agent_type, status, task_name, elapsed_s, error.
        """
        self._progress_callback = callback

    async def _emit_progress(
        self, agent_id: str, status: str, *, task_name: str = '', error: str = ''
    ) -> None:
        event = {
            'agent_id': agent_id[:12],
            'agent_type': '',
            'status': status,
            'task_name': task_name,
            'elapsed_s': 0.0,
            'error': error[:200] if error else '',
            'timestamp': time.time(),
        }
        child = self._children.get(agent_id)
        if child:
            event['agent_type'] = child.agent_type
            event['elapsed_s'] = round(time.time() - child.handle.spawned_at, 1)

        # Publish on bus so subscribers can stream
        try:
            await self._bus.publish(
                AgentMessage(
                    source='meta_orchestrator',
                    msg_type=MessageType.EVENT,
                    priority=MessagePriority.LOW,
                    payload=event,
                ),
                token=self._orch_token,
            )
        except Exception:
            pass

        # Call progress callback if set
        cb = self._progress_callback
        if cb:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(event)
                else:
                    cb(event)
            except Exception:
                pass

    async def _on_progress_message(self, msg: AgentMessage) -> None:
        """Relay progress events from children to the progress callback."""
        cb = self._progress_callback
        if cb:
            try:
                payload = {'source': msg.source, **msg.payload}
                if asyncio.iscoroutinefunction(cb):
                    await cb(payload)
                else:
                    cb(payload)
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════════
    #  MODEL ROUTING
    # ═══════════════════════════════════════════════════════════

    def configure_api_keys(self, api_keys: dict[str, str]) -> None:
        """Configure API keys for model routing.

        Args:
            api_keys: Dict mapping provider -> API key
                      (e.g. {'openai': 'sk-...', 'anthropic': 'sk-ant-...'})
        """
        self._model_router.configure_api_keys(api_keys)

    def select_model_for_agent(
        self,
        agent_type: str,
        task_description: str = '',
        require_vision: bool = False,
        allow_premium: bool = False,
        force_model: str | None = None,
    ) -> Any:
        """Select the best model for a given agent type based on available API keys.

        Returns a ModelSelectionResult with the selected model info.
        """
        role_mapping = {
            'planner': 'planner',
            'research': 'researcher',
            'writer': 'writer',
            'reviewer': 'reviewer',
            'coding': 'writer',
        }
        role = role_mapping.get(agent_type, 'writer')
        return self._model_router.select_for_role(
            role=role,
            task_description=task_description,
            require_vision=require_vision,
            allow_premium=allow_premium,
            force_model=force_model,
        )

    @property
    def model_router(self) -> ModelRouter:
        return self._model_router

    # ═══════════════════════════════════════════════════════════
    #  QUERY
    # ═══════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════
    #  CHECKPOINT PERSISTENCE
    # ═══════════════════════════════════════════════════════════

    async def save_checkpoint(self) -> None:
        """Persist current orchestrator state to disk.

        Called automatically after each task completion, retry cycle,
        and goal completion (when ``auto_checkpoint`` is enabled).
        """
        if not self._conv_id:
            return
        try:
            state = serialize_orchestrator_state(self)
            await self._checkpoint_mgr.save(self._conv_id, state)
        except Exception as e:
            _logger.warning('Failed to save checkpoint: %s', e)

    async def restore_from_checkpoint(self) -> bool:
        """Restore orchestrator state from the latest checkpoint.

        Returns True if state was restored, False if no checkpoint
        exists or restoration failed.
        """
        if not self._conv_id:
            return False
        if not self._checkpoint_mgr.has_checkpoint(self._conv_id):
            return False
        try:
            state = await self._checkpoint_mgr.load(self._conv_id)
            if state:
                restore_orchestrator_state(self, state)
                _logger.info(
                    'Restored orchestrator from checkpoint conv=%s',
                    self._conv_id,
                )
                return True
        except Exception as e:
            _logger.warning('Failed to restore checkpoint: %s', e)
        return False

    def status(self) -> dict[str, Any]:
        child_summary = [
            {
                'id': h.agent_id[:12],
                'type': h.agent_type,
                'status': h.status.value,
                'task': h.task_name,
            }
            for h in self.list_children()
        ]
        return {
            'conversation_id': self._conv_id,
            'phase': self._state.current_phase,
            'uptime_s': round(time.time() - self._state.started_at, 1),
            'goals_processed': self._state.goals_processed,
            'children': {
                'active': len(self._children),
                'spawned': self._state.children_spawned,
                'completed': self._state.children_completed,
                'failed': self._state.children_failed,
            },
            'errors': self._state.errors,
            'last_error': self._state.last_error[:120]
            if self._state.last_error
            else '',
            'budget': self._budget.global_usage(),
            'context_budget': self._context_budget.to_dict(),
            'model_router': self._model_router.cost_summary(),
            'bus': self._bus.stats(),
            'auth': self._auth.stats(),
            'circuit_breaker': self._circuit_breaker.stats(),
            'dark_factory': self._dark.stats(),
            'active_children': child_summary,
        }

    def health_check(self) -> dict[str, Any]:
        """Run full health check across all subsystems."""
        report = self._health.check_all()
        return report.to_dict()

    @property
    def bus(self) -> MessageBus:
        return self._bus

    @property
    def sandbox(self) -> ExecutionSandbox:
        return self._sandbox

    @property
    def dark_factory(self) -> DarkFactory:
        return self._dark

    @property
    def hitl(self) -> HITLConsole:
        return self._hitl

    @property
    def rag(self) -> WorkingMemoryRAG:
        return self._rag

    @property
    def fact_checker(self) -> FactChecker:
        return self._fact_checker

    def __repr__(self) -> str:
        return (
            f'MetaOrchestrator(conv={self._conv_id}, phase={self._state.current_phase}, '
            f'children={len(self._children)}, spawned={self._state.children_spawned})'
        )
