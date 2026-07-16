# wren/core/orchestrator.py
"""DEPRECATED: Standalone parallel agent orchestrator.

Used by scripts/run_parallel_agents.py only. Will be migrated to
wren.harness or a standalone scripts/ module in a future release.
Do NOT add new imports from this module.
"""

from __future__ import annotations

import warnings

warnings.warn(
    'wren.server.orchestrator is deprecated and will be moved to scripts/. '
    'Use wren.harness.MetaOrchestrator for new code.',
    DeprecationWarning,
    stacklevel=2,
)

import asyncio
import contextlib
import logging
import random
import signal
import socket
import time
import traceback
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, asdict
from enum import Enum
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt='%Y-%m-%d %H:%M:%S'),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Domain enums
# ---------------------------------------------------------------------------
class TaskStatus(str, Enum):
    QUEUED = 'queued'
    PENDING = 'pending'  # deps not satisfied
    RUNNING = 'running'
    PAUSED = 'paused'
    VERIFYING = 'verifying'  # post-run self-verification
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    TIMED_OUT = 'timed_out'
    CRASHED = 'crashed'


class TaskPriority(int, Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 8
    URGENT = 10


class EventKind(str, Enum):
    CREATED = 'task.created'
    QUEUED = 'task.queued'
    SCHEDULED = 'task.scheduled'
    STARTED = 'task.started'
    LLM_CALL = 'llm.call'
    LLM_RESPONSE = 'llm.response'
    ACTION = 'agent.action'
    OBSERVATION = 'agent.observation'
    CHECKPOINT = 'agent.checkpoint'
    HEARTBEAT = 'task.heartbeat'
    VERIFYING = 'task.verifying'
    COMPLETED = 'task.completed'
    FAILED = 'task.failed'
    CANCELLED = 'task.cancelled'
    TIMED_OUT = 'task.timed_out'
    RETRY = 'task.retry'
    LOG = 'log'


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class TaskEvent:
    task_id: str
    kind: EventKind
    timestamp: float = field(default_factory=time.time)
    payload: Dict[str, Any] = field(default_factory=dict)
    seq: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'kind': self.kind.value,
            'timestamp': self.timestamp,
            'seq': self.seq,
            'payload': self.payload,
        }


@dataclass
class TaskSpec:
    prompt: str
    repo_path: str
    api_key: Optional[str] = None
    model_name: str = 'claude-sonnet-4.5'
    runtime_cls: str = 'docker'
    runtime_opts: Dict[str, Any] = field(default_factory=dict)
    timeout_s: float = 1800.0
    max_retries: int = 2
    backoff_base_s: float = 2.0
    backoff_cap_s: float = 60.0
    priority: TaskPriority = TaskPriority.NORMAL
    tenant_id: str = 'default'
    tags: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    secrets_scope: Optional[str] = None
    network_egress: str = 'open'  # open | restricted | none
    seed: Optional[int] = None
    verify_fn: Optional[Callable[[Any], Awaitable[bool]]] = None
    max_cost_usd: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskHandle:
    task_id: str
    spec: TaskSpec
    status: TaskStatus = TaskStatus.QUEUED
    attempts: int = 0
    result: Any = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    ended_at: Optional[float] = None
    last_heartbeat: Optional[float] = None
    cost_usd: float = 0.0
    events: deque = field(default_factory=lambda: deque(maxlen=2000))
    fut: Optional[asyncio.Future] = None
    cancel_token: asyncio.Event = field(default_factory=asyncio.Event)

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'status': self.status.value,
            'attempts': self.attempts,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'ended_at': self.ended_at,
            'last_heartbeat': self.last_heartbeat,
            'cost_usd': self.cost_usd,
            'spec': {
                'model_name': self.spec.model_name,
                'runtime_cls': self.spec.runtime_cls,
                'timeout_s': self.spec.timeout_s,
                'max_retries': self.spec.max_retries,
                'priority': self.spec.priority.name,
                'tenant_id': self.spec.tenant_id,
                'tags': self.spec.tags,
                'depends_on': self.spec.depends_on,
            },
            'events': [e.to_dict() for e in list(self.events)[-50:]],
        }


# ---------------------------------------------------------------------------
# Hooks protocol
# ---------------------------------------------------------------------------
HookFn = Callable[[TaskHandle, Dict[str, Any]], Awaitable[None]]


class LifecycleHooks:
    """Override these in a subclass or register via `add_hook`."""

    async def on_created(self, h: TaskHandle, ctx: Dict[str, Any]) -> None: ...
    async def on_scheduled(self, h: TaskHandle, ctx: Dict[str, Any]) -> None: ...
    async def on_started(self, h: TaskHandle, ctx: Dict[str, Any]) -> None: ...
    async def on_event(self, h: TaskHandle, evt: TaskEvent) -> None: ...
    async def on_completed(self, h: TaskHandle, ctx: Dict[str, Any]) -> None: ...
    async def on_failed(self, h: TaskHandle, ctx: Dict[str, Any]) -> None: ...
    async def on_cancelled(self, h: TaskHandle, ctx: Dict[str, Any]) -> None: ...
    async def on_finalized(self, h: TaskHandle, ctx: Dict[str, Any]) -> None: ...


# ---------------------------------------------------------------------------
# Runtime factory
# ---------------------------------------------------------------------------
class RuntimeFactory:
    """Indirection over runtime construction so orchestrator is runtime-agnostic."""

    _registry: Dict[str, Callable[..., Any]] = {}

    @classmethod
    def register(cls, name: str, builder: Callable[..., Any]) -> None:
        cls._registry[name] = builder

    @classmethod
    def build(cls, name: str, workspace_dir: str, opts: Mapping[str, Any]) -> Any:
        if name not in cls._registry:
            raise ValueError(
                f"Unknown runtime '{name}'. Available: {list(cls._registry)}"
            )
        return cls._registry[name](workspace_dir=workspace_dir, **dict(opts))


def _register_default_runtimes() -> None:
    try:
        from wren.runtime.docker import DockerRuntime  # type: ignore

        RuntimeFactory.register(
            'docker',
            lambda workspace_dir, **kw: DockerRuntime(
                workspace_dir=workspace_dir, **kw
            ),
        )
    except Exception:
        pass
    try:
        from wren.runtime.kubernetes import K8sRuntime  # type: ignore

        RuntimeFactory.register(
            'k8s',
            lambda workspace_dir, **kw: K8sRuntime(workspace_dir=workspace_dir, **kw),
        )
    except Exception:
        pass
    try:
        from wren.runtime.e2b import E2BRuntime  # type: ignore

        RuntimeFactory.register(
            'e2b',
            lambda workspace_dir, **kw: E2BRuntime(workspace_dir=workspace_dir, **kw),
        )
    except Exception:
        pass
    # Always-available stub for tests
    RuntimeFactory.register(
        'memory',
        lambda workspace_dir, **kw: _InMemoryRuntime(workspace_dir=workspace_dir, **kw),
    )


class _InMemoryRuntime:
    """Tiny no-op runtime for tests / dry runs."""

    def __init__(self, workspace_dir: str, **kw):
        self.workspace_dir = workspace_dir
        self.opts = kw
        self.started = False

    async def start(self):
        self.started = True

    async def stop(self):
        self.started = False

    async def execute(self, cmd: str):
        return (0, '', '')

    async def heartbeat(self) -> float:
        return time.time()


class _StubAgent:
    """Minimal agent stub when wren.core.agent is not available."""

    def __init__(
        self,
        runtime: Any,
        h: TaskHandle,
        env: Mapping[str, str],
        orchestrator: ParallelAgentOrchestrator,
    ):
        self.runtime = runtime
        self.h = h
        self.env = env
        self._orchestrator = orchestrator
        self.on_event: Any = None

    async def run_horizon_task(self, prompt: str) -> str:
        return f'stub_result: task={self.h.task_id} prompt_len={len(prompt)}'


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
class TaskStore:
    """Swappable persistence layer."""

    async def save(self, h: TaskHandle) -> None: ...
    async def load(self, task_id: str) -> Optional[TaskHandle]: ...
    async def list(self) -> List[TaskHandle]: ...
    async def delete(self, task_id: str) -> None: ...


class InMemoryTaskStore(TaskStore):
    def __init__(self):
        self._db: Dict[str, TaskHandle] = {}
        self._lock = asyncio.Lock()

    async def save(self, h):
        async with self._lock:
            self._db[h.task_id] = h

    async def load(self, tid):
        async with self._lock:
            return self._db.get(tid)

    async def list(self):
        async with self._lock:
            return list(self._db.values())

    async def delete(self, tid):
        async with self._lock:
            self._db.pop(tid, None)


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
class Metrics:
    def __init__(self):
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)

    def inc(self, name, n=1):
        self.counters[name] += n

    def set(self, name, v):
        self.gauges[name] = v

    def observe(self, name, v):
        self.histograms[name].append(v)

    def snapshot(self) -> Dict[str, Any]:
        return {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'histograms': {
                k: {
                    'count': len(v),
                    'sum': sum(v),
                    'p50': _p(v, 0.5),
                    'p95': _p(v, 0.95),
                    'p99': _p(v, 0.99),
                }
                for k, v in self.histograms.items()
                if v
            },
        }


def _p(xs: List[float], q: float) -> float:
    if not xs:
        return 0.0
    xs = sorted(xs)
    i = max(0, min(len(xs) - 1, int(q * (len(xs) - 1))))
    return xs[i]


# ---------------------------------------------------------------------------
# Concurrency primitives
# ---------------------------------------------------------------------------
class TenantQuota:
    """Per-tenant concurrency + rate limit."""

    def __init__(self, max_concurrent: int, rps: float):
        self.max_concurrent = max_concurrent
        self.sem = asyncio.Semaphore(max_concurrent)
        self.rps = rps
        self._tokens = rps
        self._last = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        await self.sem.acquire()
        # simple token bucket
        async with self._lock:
            now = time.monotonic()
            delta = now - self._last
            self._tokens = min(self.rps, self._tokens + delta * self.rps)
            if self._tokens < 1:
                wait = (1 - self._tokens) / self.rps
                await asyncio.sleep(wait)
                self._tokens = 0
            else:
                self._tokens -= 1
            self._last = time.monotonic()

    def release(self):
        self.sem.release()


async def _no_op() -> None:
    """Tiny no-op task used as an execution trigger placeholder inside execution loops."""
    pass


def _kind_from_str(kind: str) -> EventKind:
    try:
        return EventKind(kind)
    except ValueError:
        return EventKind.LOG


# ---------------------------------------------------------------------------
# The orchestrator
# ---------------------------------------------------------------------------
class ParallelAgentOrchestrator:
    """
    Orchestrates many isolated, autonomous, long-running agent loops.
    """

    # ---------- construction ----------
    def __init__(
        self,
        max_concurrent: int = 8,
        global_rps: float = 50.0,
        store: Optional[TaskStore] = None,
        hooks: Optional[LifecycleHooks] = None,
        watchdog_interval_s: float = 15.0,
        heartbeat_timeout_s: float = 180.0,
        default_tenant_quota: Tuple[int, float] = (4, 10.0),
        persist: bool = True,
    ):
        self.max_concurrent = max_concurrent
        self.global_sem = asyncio.Semaphore(max_concurrent)
        self.global_rps = global_rps
        self._global_tokens = global_rps
        self._global_last = time.monotonic()
        self._global_lock = asyncio.Lock()

        # Public atomic counters to tracking capacity instead of reading private semaphore internals
        self._global_running = 0
        self._tenant_running: Dict[str, int] = defaultdict(int)

        self.tasks: Dict[str, TaskHandle] = {}
        self.tenant_tasks: Dict[str, Set[str]] = defaultdict(set)
        self.tenant_quotas: Dict[str, TenantQuota] = {}
        self.tenant_quotas['default'] = TenantQuota(*default_tenant_quota)

        self.store = store or InMemoryTaskStore()
        self.hooks = hooks or LifecycleHooks()
        self._extra_hooks: List[LifecycleHooks] = []

        self.metrics = Metrics()
        self.watchdog_interval_s = watchdog_interval_s
        self.heartbeat_timeout_s = heartbeat_timeout_s

        self._evt_seq = 0
        self._subs: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self._global_subs: Set[asyncio.Queue] = set()
        self._persist = persist

        self._scheduler_task: Optional[asyncio.Task] = None
        self._watchdog_task: Optional[asyncio.Task] = None
        self._shutdown = False
        self._drain_event = asyncio.Event()
        self._started = False

        _register_default_runtimes()

    # ---------- lifecycle ----------
    async def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._scheduler_task = asyncio.create_task(
            self._scheduler_loop(), name='orch:scheduler'
        )
        self._watchdog_task = asyncio.create_task(
            self._watchdog_loop(), name='orch:watchdog'
        )
        self._install_signal_handlers()
        logger.info('orchestrator.started', max_concurrent=self.max_concurrent)

    async def shutdown(self, drain: bool = True, timeout_s: float = 60.0) -> None:
        """Graceful shutdown. Cancels remaining tasks if drain fails."""
        self._shutdown = True
        logger.info('orchestrator.shutdown', drain=drain, pending=len(self.tasks))
        if drain:
            self._drain_event.set()
            try:
                await asyncio.wait_for(self._await_drain(), timeout=timeout_s)
            except asyncio.TimeoutError:
                logger.warning('orchestrator.drain.timeout')

        # Cancel remaining active allocations
        for h in list(self.tasks.values()):
            if h.status in (
                TaskStatus.RUNNING,
                TaskStatus.QUEUED,
                TaskStatus.PENDING,
                TaskStatus.PAUSED,
            ):
                await self.cancel(h.task_id, reason='shutdown')
        for t in (self._scheduler_task, self._watchdog_task):
            if t and not t.done():
                t.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await t
        logger.info('orchestrator.stopped')

    async def _await_drain(self) -> None:
        while any(
            h.status in (TaskStatus.RUNNING, TaskStatus.QUEUED)
            for h in self.tasks.values()
        ):
            await asyncio.sleep(0.5)

    def _install_signal_handlers(self) -> None:
        if not hasattr(signal, 'SIGTERM'):
            return  # Windows platform support ceiling
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            with contextlib.suppress(NotImplementedError, RuntimeError):
                loop.add_signal_handler(
                    sig, lambda: asyncio.create_task(self.shutdown())
                )

    # ---------- public API ----------
    def set_tenant_quota(self, tenant: str, max_concurrent: int, rps: float) -> None:
        self.tenant_quotas[tenant] = TenantQuota(max_concurrent, rps)

    def add_hook(self, hook: LifecycleHooks) -> None:
        self._extra_hooks.append(hook)

    async def spawn(self, spec: TaskSpec) -> str:
        """Create a new background agent task. Returns task_id immediately."""
        tid = f'task_{uuid.uuid4().hex[:12]}'
        h = TaskHandle(task_id=tid, spec=spec)
        self.tasks[tid] = h
        self.tenant_tasks[spec.tenant_id].add(tid)
        if spec.tenant_id not in self.tenant_quotas:
            self.tenant_quotas[spec.tenant_id] = TenantQuota(4, 10.0)

        self._emit(
            h, EventKind.CREATED, {'prompt': spec.prompt[:200], 'repo': spec.repo_path}
        )
        await self._run_hook('on_created', h, {})
        if self._persist:
            await self.store.save(h)
        self.metrics.inc('tasks.created')
        logger.info('task.created', task_id=tid, tenant=spec.tenant_id)
        return tid

    async def spawn_many(self, specs: Iterable[TaskSpec]) -> List[str]:
        return [await self.spawn(s) for s in specs]

    async def cancel(self, task_id: str, reason: str = 'user_request') -> bool:
        h = self.tasks.get(task_id)
        if not h:
            return False
        if h.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMED_OUT,
        ):
            return False
        h.status = TaskStatus.CANCELLED
        h.ended_at = time.time()
        h.cancel_token.set()
        if h.fut and not h.fut.done():
            h.fut.cancel()
        self._emit(h, EventKind.CANCELLED, {'reason': reason})
        await self._run_hook('on_cancelled', h, {'reason': reason})
        if self._persist:
            await self.store.save(h)
        self.metrics.inc('tasks.cancelled')
        logger.info('task.cancelled', task_id=task_id, reason=reason)
        return True

    async def pause(self, task_id: str) -> bool:
        h = self.tasks.get(task_id)
        if not h or h.status != TaskStatus.RUNNING:
            return False
        h.status = TaskStatus.PAUSED
        self._emit(h, EventKind.LOG, {'msg': 'paused'})
        return True

    async def resume(self, task_id: str) -> bool:
        h = self.tasks.get(task_id)
        if not h or h.status != TaskStatus.PAUSED:
            return False
        h.status = TaskStatus.QUEUED
        self._emit(h, EventKind.LOG, {'msg': 'resumed'})
        return True

    async def status(self, task_id: str) -> Dict[str, Any]:
        h = self.tasks.get(task_id)
        if not h:
            cached = await self.store.load(task_id)
            if not cached:
                return {'error': 'Task not found'}
            return cached.to_public_dict()
        return h.to_public_dict()

    async def list_tasks(
        self, tenant: Optional[str] = None, status: Optional[TaskStatus] = None
    ) -> List[Dict[str, Any]]:
        out = []
        for h in self.tasks.values():
            if tenant and h.spec.tenant_id != tenant:
                continue
            if status and h.status != status:
                continue
            out.append(h.to_public_dict())
        return out

    async def wait(
        self, task_id: str, timeout_s: Optional[float] = None
    ) -> Dict[str, Any]:
        h = self.tasks.get(task_id)
        if not h:
            return {'error': 'Task not found'}
        if h.fut is None:
            return h.to_public_dict()
        try:
            await asyncio.wait_for(asyncio.shield(h.fut), timeout_s)
        except asyncio.TimeoutError:
            return {'task_id': task_id, 'status': 'still_running'}
        except asyncio.CancelledError:
            pass
        return h.to_public_dict()

    # ---------- event streaming ----------
    async def stream(self, task_id: str) -> asyncio.Queue[TaskEvent]:
        q: asyncio.Queue = asyncio.Queue(maxsize=1024)
        self._subs[task_id].add(q)
        h = self.tasks.get(task_id)
        if h:
            for e in list(h.events):
                await q.put(e)
        return q

    async def stream_all(self) -> asyncio.Queue[TaskEvent]:
        q: asyncio.Queue = asyncio.Queue(maxsize=2048)
        self._global_subs.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        for s in self._subs.values():
            s.discard(q)
        self._global_subs.discard(q)

    # ---------- metrics ----------
    def metrics_snapshot(self) -> Dict[str, Any]:
        self.metrics.set('tasks.active', self._global_running)
        self.metrics.set('tasks.total', len(self.tasks))
        self.metrics.set(
            'concurrency.available', self.max_concurrent - self._global_running
        )
        return self.metrics.snapshot()

    # ---------- scheduler ----------
    async def _scheduler_loop(self) -> None:
        """Continuously admit runnable tasks under concurrency ceilings."""
        while not self._shutdown:
            admitted = False
            ready = self._ready_tasks()
            for h in ready:
                if self._shutdown:
                    break
                if h.status != TaskStatus.QUEUED:
                    continue
                if not self._deps_satisfied(h):
                    continue

                # Public allocation check against tracking counters
                if self._global_running >= self.max_concurrent:
                    continue
                tq = self.tenant_quotas[h.spec.tenant_id]
                if self._tenant_running[h.spec.tenant_id] >= tq.max_concurrent:
                    continue

                if not await self._admit(h):
                    continue
                admitted = True
            await asyncio.sleep(0.1 if not admitted else 0.01)

    def _ready_tasks(self) -> List[TaskHandle]:
        return sorted(
            (h for h in self.tasks.values() if h.status == TaskStatus.QUEUED),
            key=lambda h: (-h.spec.priority.value, h.created_at),
        )

    def _deps_satisfied(self, h: TaskHandle) -> bool:
        for dep in h.spec.depends_on:
            d = self.tasks.get(dep)
            if not d or d.status != TaskStatus.COMPLETED:
                return False
        return True

    async def _admit(self, h: TaskHandle) -> bool:
        try:
            await self.global_sem.acquire()
            try:
                tq = self.tenant_quotas[h.spec.tenant_id]
                await tq.acquire()
            except Exception:
                self.global_sem.release()
                raise
        except Exception:
            return False

        # Global rate-limit token bucket
        async with self._global_lock:
            now = time.monotonic()
            delta = now - self._global_last
            self._global_tokens = min(
                self.global_rps, self._global_tokens + delta * self.global_rps
            )
            if self._global_tokens < 1:
                wait = (1 - self._global_tokens) / self.global_rps
                await asyncio.sleep(wait)
                self._global_tokens = 0
            else:
                self._global_tokens -= 1
            self._global_last = time.monotonic()

        # Update core runtime status counters
        self._global_running += 1
        self._tenant_running[h.spec.tenant_id] += 1

        h.status = TaskStatus.RUNNING
        h.started_at = time.time()
        h.last_heartbeat = time.time()
        self._emit(h, EventKind.SCHEDULED, {'worker': socket.gethostname()})
        await self._run_hook('on_scheduled', h, {'worker': socket.gethostname()})
        if self._persist:
            await self.store.save(h)

        h.fut = asyncio.create_task(self._execute(h), name=f'task:{h.task_id}')
        h.fut.add_done_callback(lambda _f, _h=h: self._on_done(_h))
        self.metrics.inc('tasks.started')
        return True

    def _on_done(self, h: TaskHandle) -> None:
        # Atomic counter remediation
        self._global_running = max(0, self._global_running - 1)
        self._tenant_running[h.spec.tenant_id] = max(
            0, self._tenant_running[h.spec.tenant_id] - 1
        )

        try:
            self.tenant_quotas[h.spec.tenant_id].release()
        except Exception:
            pass
        self.global_sem.release()
        if self._persist:
            asyncio.create_task(self.store.save(h))

    # ---------- execution ----------
    async def _execute(self, h: TaskHandle) -> None:
        """Run the agent loop with retry, timeout, verification, and cleanup."""
        backoff = h.spec.backoff_base_s
        while True:
            h.attempts += 1
            self._emit(h, EventKind.STARTED, {'attempt': h.attempts})
            await self._run_hook('on_started', h, {'attempt': h.attempts})
            runtime = None
            try:
                runtime = RuntimeFactory.build(
                    h.spec.runtime_cls, h.spec.repo_path, h.spec.runtime_opts
                )
                await runtime.start()

                env = dict(h.spec.env)
                if h.spec.seed is not None:
                    env['PYTHONHASHSEED'] = str(h.spec.seed)
                    env['OH_RAND_SEED'] = str(h.spec.seed)

                agent = self._build_agent(runtime, h, env)
                self._wire_agent_events(agent, h)

                timeout = h.spec.timeout_s
                async with self._timeout_or_cancel(h, timeout) as expired:
                    if expired:
                        raise asyncio.TimeoutError()
                    result = await agent.run_horizon_task(h.spec.prompt)

                if h.spec.verify_fn is not None:
                    h.status = TaskStatus.VERIFYING
                    self._emit(h, EventKind.VERIFYING, {})
                    ok = bool(await h.spec.verify_fn(result))
                    if not ok:
                        raise RuntimeError('verification_failed')

                h.result = result
                h.status = TaskStatus.COMPLETED
                h.ended_at = time.time()
                self._emit(h, EventKind.COMPLETED, {})
                await self._run_hook('on_completed', h, {'result': result})
                self.metrics.observe(
                    'task.duration_s', h.ended_at - (h.started_at or h.ended_at)
                )
                self.metrics.inc('tasks.completed')
                break

            except asyncio.CancelledError:
                h.status = TaskStatus.CANCELLED
                h.ended_at = time.time()
                self._emit(h, EventKind.CANCELLED, {'reason': 'cancelled'})
                await self._run_hook('on_cancelled', h, {})
                self.metrics.inc('tasks.cancelled')
                raise

            except asyncio.TimeoutError as e:
                self._emit(h, EventKind.TIMED_OUT, {'timeout_s': h.spec.timeout_s})
                if h.attempts > h.spec.max_retries:
                    h.status = TaskStatus.TIMED_OUT
                    h.error = str(e)
                    h.ended_at = time.time()
                    await self._run_hook('on_failed', h, {'error': str(e)})
                    self.metrics.inc('tasks.timed_out')
                    break
                self._emit(
                    h, EventKind.RETRY, {'attempt': h.attempts, 'backoff_s': backoff}
                )
                await asyncio.sleep(backoff + random.uniform(0, backoff * 0.3))
                backoff = min(h.spec.backoff_cap_s, backoff * 2)

            except Exception as e:
                tb = traceback.format_exc()
                self._emit(h, EventKind.FAILED, {'error': str(e), 'tb': tb[-2000:]})
                if h.attempts > h.spec.max_retries:
                    h.status = TaskStatus.FAILED
                    h.error = str(e)
                    h.ended_at = time.time()
                    await self._run_hook('on_failed', h, {'error': str(e), 'tb': tb})
                    self.metrics.inc('tasks.failed')
                    break
                self._emit(
                    h, EventKind.RETRY, {'attempt': h.attempts, 'backoff_s': backoff}
                )
                await asyncio.sleep(backoff + random.uniform(0, backoff * 0.3))
                backoff = min(h.spec.backoff_cap_s, backoff * 2)

            finally:
                if runtime is not None:
                    with contextlib.suppress(Exception):
                        await runtime.stop()
                await self._run_hook('on_finalized', h, {})

    @asynccontextmanager
    async def _timeout_or_cancel(self, h: TaskHandle, timeout_s: float):
        """Yields control, raising CancelledError if token sets, or letting timeout hit."""
        waiter = None
        try:
            async with asyncio.timeout(timeout_s):
                waiter = asyncio.create_task(h.cancel_token.wait())
                execution_trigger = asyncio.create_task(_no_op())

                done, pending = await asyncio.wait(
                    {waiter, execution_trigger}, return_when=asyncio.FIRST_COMPLETED
                )
                for p in pending:
                    p.cancel()
                if h.cancel_token.is_set():
                    raise asyncio.CancelledError()
                yield False
        except asyncio.TimeoutError:
            yield True
        finally:
            if waiter and not waiter.done():
                waiter.cancel()

    # ---------- agent wiring ----------
    def _build_agent(self, runtime: Any, h: TaskHandle, env: Mapping[str, str]) -> Any:
        try:
            from wren.core.agent import Agent  # type: ignore

            return Agent(
                runtime=runtime,
                api_key=h.spec.api_key,
                model=h.spec.model_name,
                env=dict(env),
                on_cost=lambda c: self._on_cost(h, c),
                on_heartbeat=lambda: self._on_heartbeat(h),
            )
        except ImportError:
            from wren.server.conversation_agent import ConversationAgentAdapter

            return ConversationAgentAdapter(runtime, h, env, self)

    def _wire_agent_events(self, agent: Any, h: TaskHandle) -> None:
        if hasattr(agent, 'on_event'):
            agent.on_event = lambda kind, payload: self._emit(
                h, _kind_from_str(kind), payload
            )

    def _on_cost(self, h: TaskHandle, cost: float) -> None:
        h.cost_usd += cost
        if h.spec.max_cost_usd and h.cost_usd >= h.spec.max_cost_usd:
            self._emit(
                h, EventKind.LOG, {'msg': 'cost_limit_reached', 'cost': h.cost_usd}
            )
            asyncio.create_task(self.cancel(h.task_id, reason='cost_limit'))

    def _on_heartbeat(self, h: TaskHandle) -> None:
        h.last_heartbeat = time.time()
        self._emit(h, EventKind.HEARTBEAT, {})

    # ---------- bus mechanics ----------
    def _emit(self, h: TaskHandle, kind: EventKind, payload: Dict[str, Any]) -> None:
        self._evt_seq += 1
        evt = TaskEvent(
            task_id=h.task_id, kind=kind, payload=payload, seq=self._evt_seq
        )
        h.events.append(evt)

        # Dispatch to active stream subscribers
        for q in list(self._subs[h.task_id]):
            try:
                q.put_nowait(evt)
            except asyncio.QueueFull:
                pass
        for q in list(self._global_subs):
            try:
                q.put_nowait(evt)
            except asyncio.QueueFull:
                pass

        # Direct execution mirror to life cycle hooks
        if self._extra_hooks:
            for hook in self._extra_hooks:
                asyncio.create_task(hook.on_event(h, evt))
        if self.hooks:
            asyncio.create_task(self.hooks.on_event(h, evt))

    async def _run_hook(
        self, hook_name: str, h: TaskHandle, ctx: Dict[str, Any]
    ) -> None:
        if self.hooks and hasattr(self.hooks, hook_name):
            try:
                await getattr(self.hooks, hook_name)(h, ctx)
            except Exception:
                logger.error(
                    f'lifecycle_hooks.error.{hook_name}',
                    task_id=h.task_id,
                    exc_info=True,
                )
        for hook in self._extra_hooks:
            if hasattr(hook, hook_name):
                try:
                    await getattr(hook, hook_name)(h, ctx)
                except Exception:
                    logger.error(
                        f'lifecycle_hooks.extra.error.{hook_name}',
                        task_id=h.task_id,
                        exc_info=True,
                    )

    # ---------- watchdog ----------
    async def _watchdog_loop(self) -> None:
        """Reap zombie tasks whose heartbeats have gone silent."""
        while not self._shutdown:
            try:
                now = time.time()
                for h in list(self.tasks.values()):
                    if h.status != TaskStatus.RUNNING:
                        continue
                    if (
                        h.last_heartbeat
                        and now - h.last_heartbeat > self.heartbeat_timeout_s
                    ):
                        self._emit(
                            h,
                            EventKind.LOG,
                            {
                                'msg': 'watchdog.kill',
                                'silent_s': now - h.last_heartbeat,
                            },
                        )
                        self.metrics.inc('tasks.zombie_killed')
                        await self.cancel(h.task_id, reason='heartbeat_lost')
                await asyncio.sleep(self.watchdog_interval_s)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.error('watchdog.loop.error', exc_info=True)
                await asyncio.sleep(5.0)
