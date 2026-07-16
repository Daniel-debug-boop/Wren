"""Child agent protocol — all agents spawned by MetaOrchestrator
implement this interface.

A child agent:
  - Is created by the parent (MetaOrchestrator)
  - Receives tasks via init/receive_task
  - Communicates ONLY through the message bus
  - Has a resource budget allocated by the parent
  - ALWAYS thinks before acting (ThinkPipeline)
  - Reports results and shuts down when done
"""

from __future__ import annotations

import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TYPE_CHECKING

from wren.harness.storage.store import Store

if TYPE_CHECKING:
    from wren.harness.thinking.pipeline import ThinkOutput, ThinkPipeline

_logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    CREATED = 'created'
    INITIALIZING = 'initializing'
    THINKING = 'thinking'
    IDLE = 'idle'
    BUSY = 'busy'
    COMPLETED = 'completed'
    FAILED = 'failed'
    KILLED = 'killed'


@dataclass
class AgentHandle:
    """Handle returned to parent when a child agent is spawned."""

    agent_id: str = field(default_factory=lambda: f'agent_{uuid.uuid4().hex[:8]}')
    agent_type: str = ''
    status: AgentStatus = AgentStatus.CREATED
    task_name: str = ''
    spawned_at: float = field(default_factory=time.time)
    completed_at: float = 0.0
    result: Any = None
    error: str = ''
    budget: Any = None
    last_think: Any = None  # ThinkOutput from last thinking cycle

    @property
    def uptime(self) -> float:
        end = self.completed_at or time.time()
        return end - self.spawned_at

    def to_dict(self) -> dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'type': self.agent_type,
            'status': self.status.value,
            'task': self.task_name,
            'uptime_s': round(self.uptime, 2),
            'error': self.error[:200] if self.error else '',
        }


class ChildAgent(ABC):
    """Abstract base for all child agents spawned by MetaOrchestrator.

    Forces a think-before-you-act cycle before every task execution.
    Subclasses implement _execute() — thinking is handled by the base.
    """

    def __init__(self, agent_id: str, agent_type: str) -> None:
        self.agent_id = agent_id
        self.agent_type = agent_type
        self._handle = AgentHandle(agent_id=agent_id, agent_type=agent_type)
        self._token: str = ''
        self._budget: Any = None
        self._bus: Any = None
        self._think_pipeline: Any = None  # ThinkPipeline

    # ── Lifecycle (called by parent) ─────────────────────────────

    async def init(
        self,
        budget: Any = None,
        bus: Any = None,
        think_pipeline: Any = None,
        token: str = '',
    ) -> None:
        """Initialize the agent before first use.

        Args:
            budget: ResourceBudget instance
            bus: MessageBus instance
            think_pipeline: ThinkPipeline instance (created if not provided)
            token: Auth token for message bus publishing
        """
        self._token = token
        self._budget = budget
        self._bus = bus
        # from wren.harness.thinking.pipeline import ThinkPipeline  # noqa: F401

        self._think_pipeline = think_pipeline or ThinkPipeline(
            agent_id=self.agent_id, agent_type=self.agent_type
        )
        self._handle.status = AgentStatus.INITIALIZING
        Store.save_child(self.agent_id, self.agent_type, 'initializing')
        await self._on_init()
        self._handle.status = AgentStatus.IDLE
        Store.save_child(self.agent_id, self.agent_type, 'idle')
        _logger.debug('ChildAgent %s initialised', self.agent_id[:12])

    async def receive_task(self, task: dict[str, Any]) -> Any:
        """Receive and execute a task.

        THINK before acting. The thinking pipeline runs first.
        If it denies the task (high risk), execution is skipped.
        Also runs SDK guardrail checks on task description.
        """
        self._handle.status = AgentStatus.THINKING
        self._handle.task_name = task.get('name', 'unnamed')
        Store.save_child(
            self.agent_id, self.agent_type, 'thinking', task_name=self._handle.task_name
        )

        # ── SDK GUARDRAIL CHECK ─────────────────────────────────
        try:
            from wren.harness.sdk_wiring import get_sdk_context

            ctx = get_sdk_context()
            from wren.tool.base import Action, ToolDef

            # Create a synthetic action from task description to check guardrails
            desc = task.get('description', task.get('task', ''))
            action = Action(tool_name='bash', arguments={'command': desc})
            dummy_tool = ToolDef(
                name='bash',
                description='shell command',
                parameters={},
                category='terminal',
                safety='dangerous',
            )
            result = ctx.enforcer.check(dummy_tool, action)
            if not result.allowed:
                _logger.warning(
                    'ChildAgent %s: task blocked by SDK guardrails: %s',
                    self.agent_id[:12],
                    result.reason,
                )
                self._handle.status = AgentStatus.FAILED
                self._handle.error = f'Blocked by guardrails: {result.reason}'
                self._handle.completed_at = time.time()
                Store.save_child(
                    self.agent_id,
                    self.agent_type,
                    'failed',
                    task_name=self._handle.task_name,
                    error=self._handle.error,
                )
                raise RuntimeError(self._handle.error)
        except ImportError:
            pass  # SDK not available, skip guardrail check

        # ── THINK BEFORE ACT ─────────────────────────────────
        think: ThinkOutput = await self._think_pipeline.think(task)
        self._handle.last_think = think

        # Store thinking result
        Store.save_child(
            self.agent_id,
            self.agent_type,
            'thinking',
            task_name=self._handle.task_name,
            result={'think': think.to_dict()},
        )

        if not think.approved:
            _logger.warning(
                'ChildAgent %s: task denied by ThinkPipeline (risk=%.2f)',
                self.agent_id[:12],
                think.risk_score,
            )
            self._handle.status = AgentStatus.FAILED
            self._handle.error = (
                f'Denied by ThinkPipeline: risk_score={think.risk_score:.2f}'
            )
            self._handle.completed_at = time.time()
            Store.save_child(
                self.agent_id,
                self.agent_type,
                'failed',
                task_name=self._handle.task_name,
                error=self._handle.error,
            )
            raise RuntimeError(self._handle.error)

        # ── EXECUTE ──────────────────────────────────────────
        self._handle.status = AgentStatus.BUSY
        Store.save_child(
            self.agent_id, self.agent_type, 'busy', task_name=self._handle.task_name
        )

        try:
            result = await self._execute(task)
            self._handle.status = AgentStatus.COMPLETED
            self._handle.completed_at = time.time()
            self._handle.result = result
            Store.save_child(
                self.agent_id,
                self.agent_type,
                'completed',
                task_name=self._handle.task_name,
                result=result,
            )
            return result
        except Exception as e:
            self._handle.status = AgentStatus.FAILED
            self._handle.error = str(e)
            self._handle.completed_at = time.time()
            Store.save_child(
                self.agent_id,
                self.agent_type,
                'failed',
                task_name=self._handle.task_name,
                error=str(e),
            )
            raise

    async def shutdown(self) -> None:
        """Clean up resources."""
        await self._on_shutdown()
        if self._handle.status not in (
            AgentStatus.COMPLETED,
            AgentStatus.FAILED,
            AgentStatus.KILLED,
        ):
            self._handle.status = AgentStatus.KILLED
        Store.save_child(
            self.agent_id,
            self.agent_type,
            self._handle.status.value,
            task_name=self._handle.task_name,
        )

    @property
    def handle(self) -> AgentHandle:
        return self._handle

    @property
    def last_think(self) -> Any:
        return self._handle.last_think

    # ── Subclass hooks ───────────────────────────────────────────

    @abstractmethod
    async def _on_init(self) -> None:
        """Subclass-specific initialisation."""

    @abstractmethod
    async def _execute(self, task: dict[str, Any]) -> Any:
        """Execute the assigned task and return result."""

    @abstractmethod
    async def _on_shutdown(self) -> None:
        """Subclass-specific cleanup."""

    def __repr__(self) -> str:
        return f'{self.agent_type}(id={self.agent_id[:12]}, status={self._handle.status.value})'
