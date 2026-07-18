"""Meta-Orchestrator v2 — PARENT CONTROLLER.

Spawns child agents, manages their lifecycle, enforces budgets,
and reflects on results. All agents run as children of the
orchestrator and communicate only through the message bus.

Agent Types:
  - planner: Maps out file changes and dictates sequential order
  - researcher: Uses fast models to parse project files and gather context
  - writer: Uses focused coding models to write and modify code
  - reviewer: Runs automated checks to verify code functionality
  - coding: General-purpose coding harness (legacy/fallback)
"""

from wren.harness.config import HarnessConfig
from wren.harness.auth import BusAuth, AuthError
from wren.harness.health import HealthChecker, HealthReport
from wren.harness.telemetry import Telemetry, TelemetryEvent
from wren.harness.circuit_breaker import CircuitBreaker, CircuitState

from wren.harness.meta_orchestrator import (
    MetaOrchestrator,
    MetaOrchestratorState,
)
from wren.harness.task_graph import TaskGraph, PrioritizedTask, TaskStatus
from wren.harness.resource_budget import (
    ResourceBudget,
    BudgetLimit,
    BudgetExceeded,
)
from wren.harness.message_bus import (
    MessageBus,
    AgentMessage,
    MessagePriority,
    MessageType,
)

from wren.harness.knowledge.vector_store import VectorStore
from wren.harness.knowledge.working_memory_rag import WorkingMemoryRAG
from wren.harness.knowledge.skill_library import SkillLibrary

from wren.harness.reflection.self_critique import (
    SelfCritiqueAgent,
    CritiqueFinding,
    CritiqueReport,
    CritiqueSeverity,
)
from wren.harness.reflection.fact_checker import (
    FactChecker,
    FactCheck,
    FactCheckResult,
)
from wren.harness.reflection.quality_gates import (
    QualityGates,
    QualityGatesReport,
    GateResult,
    GateVerdict,
)

from wren.harness.agents.base import ChildAgent, AgentHandle, AgentStatus
from wren.harness.agents.coding_harness import CodingHarness
from wren.harness.agents.research_agent import ResearchAgent
from wren.harness.agents.planner_agent import PlannerAgent
from wren.harness.agents.writer_agent import WriterAgent
from wren.harness.agents.reviewer_agent import ReviewerAgent
from wren.harness.agents.dark_factory import DarkFactory, DarkTask
from wren.harness.agents.hitl_console import HITLConsole, ApprovalRequest, Decision

from wren.harness.sandbox.execution_sandbox import (
    ExecutionSandbox,
    ExecutionResult,
)

from wren.harness.model_router import (
    ModelRouter,
    ModelRegistry,
    ModelInfo,
    ModelTier,
    ModelSelectionResult,
    AgentRoleConfig,
)

__all__ = [
    # Auth
    'BusAuth',
    'AuthError',
    # Health & Telemetry
    'HealthChecker',
    'HealthReport',
    'Telemetry',
    'TelemetryEvent',
    # Parent controller
    'MetaOrchestrator',
    'HarnessConfig',
    'MetaOrchestratorState',
    'CircuitBreaker',
    'CircuitState',
    # Task graph
    'TaskGraph',
    'PrioritizedTask',
    'TaskStatus',
    # Budget
    'ResourceBudget',
    'BudgetLimit',
    'BudgetExceeded',
    # Bus
    'MessageBus',
    'AgentMessage',
    'MessagePriority',
    'MessageType',
    # Knowledge
    'VectorStore',
    'WorkingMemoryRAG',
    'SkillLibrary',
    # Reflection
    'SelfCritiqueAgent',
    'CritiqueFinding',
    'CritiqueReport',
    'CritiqueSeverity',
    'FactChecker',
    'FactCheck',
    'FactCheckResult',
    'QualityGates',
    'QualityGatesReport',
    'GateResult',
    'GateVerdict',
    # Child agents
    'ChildAgent',
    'AgentHandle',
    'AgentStatus',
    'CodingHarness',
    'ResearchAgent',
    'PlannerAgent',
    'WriterAgent',
    'ReviewerAgent',
    # Background / HITL
    'DarkFactory',
    'DarkTask',
    'HITLConsole',
    'ApprovalRequest',
    'Decision',
    # Sandbox
    'ExecutionSandbox',
    'ExecutionResult',
    # Model Router
    'ModelRouter',
    'ModelRegistry',
    'ModelInfo',
    'ModelTier',
    'ModelSelectionResult',
    'AgentRoleConfig',
]
