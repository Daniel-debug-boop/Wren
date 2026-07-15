"""Planner Agent — maps out file changes and dictates their sequential order.

The Planner receives a high-level goal and produces a structured plan:
  - Which files need to be created, modified, or deleted
  - The exact order of changes (dependencies between files)
  - Risk assessment for each change
  - Estimated effort and token cost

Output is a sequential task list consumed by the Writer and Reviewer.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from wren.harness.agents.base import ChildAgent
from wren.harness.message_bus import AgentMessage, MessagePriority, MessageType

_logger = logging.getLogger(__name__)


@dataclass
class PlannedChange:
    """A single planned file change in the plan."""

    file_path: str
    change_type: str  # 'create', 'modify', 'delete', 'rename'
    description: str
    dependencies: list[str] = field(default_factory=list)
    estimated_tokens: int = 0
    risk_level: str = 'low'  # 'low', 'medium', 'high'
    acceptance_criteria: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'file_path': self.file_path,
            'change_type': self.change_type,
            'description': self.description,
            'dependencies': self.dependencies,
            'estimated_tokens': self.estimated_tokens,
            'risk_level': self.risk_level,
            'acceptance_criteria': self.acceptance_criteria,
        }


@dataclass
class PlanResult:
    """Complete plan output from the PlannerAgent."""

    goal: str
    summary: str
    changes: list[PlannedChange] = field(default_factory=list)
    execution_order: list[str] = field(default_factory=list)
    estimated_total_tokens: int = 0
    complexity_score: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'goal': self.goal,
            'summary': self.summary,
            'changes': [c.to_dict() for c in self.changes],
            'execution_order': self.execution_order,
            'estimated_total_tokens': self.estimated_total_tokens,
            'complexity_score': self.complexity_score,
            'warnings': self.warnings,
        }


class PlannerAgent(ChildAgent):
    """Child agent that produces structured plans from high-level goals.

    The Planner:
      1. Analyzes the goal to determine scope and complexity
      2. Identifies all files that need to be created, modified, or deleted
      3. Orders changes by dependency (sequential execution plan)
      4. Provides risk assessment and acceptance criteria for each change
      5. Estimates token cost and complexity

    Output is consumed by the WriterAgent (execution) and ReviewerAgent (verification).
    """

    def __init__(self, agent_id: str = '') -> None:
        super().__init__(agent_id or 'planner_agent', 'planner')

    async def _on_init(self) -> None:
        _logger.debug('PlannerAgent: init')

    async def _execute(self, task: dict[str, Any]) -> dict[str, Any]:
        description = task.get('description', task.get('task', ''))
        goal = task.get('goal', description)
        files = task.get('files', [])

        # ── Project context (WREN.md / CLAUDE.md from workspace) ──
        project_context = task.get('project_context')
        context_block = ''
        if project_context and getattr(project_context, 'found', False):
            context_block = project_context.formatted
            _logger.info(
                'PlannerAgent: loaded project context from %s',
                project_context.source_file,
            )

        _logger.info('PlannerAgent: planning goal="%s"', goal[:80])

        start = time.time()

        # Try to use message bus for LLM-backed planning
        plan = await self._generate_plan(goal, files, description, context_block)

        _logger.info(
            'PlannerAgent: done changes=%d complexity=%.1f',
            len(plan.changes),
            plan.complexity_score,
        )

        result = plan.to_dict()
        result['duration_s'] = round(time.time() - start, 2)

        # Publish plan on bus
        if self._bus:
            await self._bus.publish(
                AgentMessage(
                    source=self.agent_id,
                    msg_type=MessageType.TASK_RESULT,
                    payload={'plan': result},
                ),
                token=self._token,
            )

        return result

    async def _generate_plan(
        self,
        goal: str,
        files: list[str],
        description: str,
        context_block: str = '',
    ) -> PlanResult:
        """Generate a structured plan. Uses bus for LLM if available."""
        if self._bus:
            try:
                req = AgentMessage(
                    source=self.agent_id,
                    msg_type=MessageType.TASK_REQUEST,
                    priority=MessagePriority.HIGH,
                    payload={
                        'action': 'plan',
                        'goal': goal,
                        'files': files,
                        'description': description,
                        'project_context': context_block,
                    },
                )
                resp = await self._bus.publish_and_wait(
                    req, token=self._token, timeout_s=30.0
                )
                if resp and 'plan' in resp.payload:
                    plan_data = resp.payload['plan']
                    plan = self._plan_from_dict(plan_data, goal)
                    # Tag the plan with project context info
                    if context_block:
                        plan.summary += f' (using project context)'
                    return plan
            except Exception as e:
                _logger.warning('PlannerAgent: bus planning failed: %s', e)

        # Fallback: heuristic-based planning
        return self._heuristic_plan(goal, files, description)

    def _heuristic_plan(
        self, goal: str, files: list[str], description: str
    ) -> PlanResult:
        """Generate a plan using heuristics when LLM is unavailable."""
        changes: list[PlannedChange] = []
        execution_order: list[str] = []

        gl = goal.lower()
        is_new_project = any(
            kw in gl for kw in ['new', 'create', 'build', 'start', 'scaffold']
        )

        if is_new_project:
            # New project: scaffold structure first, then implement
            structure_changes = [
                PlannedChange(
                    file_path='README.md',
                    change_type='create',
                    description='Project overview and setup instructions',
                    risk_level='low',
                    acceptance_criteria=['Describes project purpose', 'Has setup steps'],
                ),
                PlannedChange(
                    file_path='package.json',
                    change_type='create',
                    description='Project dependencies and scripts',
                    risk_level='low',
                    acceptance_criteria=['All required deps listed'],
                ),
                PlannedChange(
                    file_path='src/index.ts',
                    change_type='create',
                    description='Main entry point',
                    risk_level='medium',
                    dependencies=['package.json'],
                    acceptance_criteria=['Exports correct interface'],
                ),
            ]
            changes.extend(structure_changes)
            execution_order = [c.file_path for c in structure_changes]
        elif files:
            # Existing files: plan modifications
            for f in files:
                changes.append(
                    PlannedChange(
                        file_path=f,
                        change_type='modify',
                        description=f'Modify {f} to implement: {description[:80]}',
                        risk_level='medium',
                        acceptance_criteria=['Change is backward-compatible'],
                    )
                )
            execution_order = [c.file_path for c in changes]
        else:
            # Generic: analyze first, then plan
            changes.append(
                PlannedChange(
                    file_path='(analysis)',
                    change_type='modify',
                    description=f'Analyze {description[:100]}',
                    risk_level='low',
                )
            )
            execution_order = ['(analysis)']

        return PlanResult(
            goal=goal,
            summary=f'Planned {len(changes)} changes for: {goal[:100]}',
            changes=changes,
            execution_order=execution_order,
            estimated_total_tokens=len(goal) * 2,
            complexity_score=min(10.0, len(goal) / 50),
            warnings=[] if is_new_project else ['No existing files analyzed'],
        )

    @staticmethod
    def _plan_from_dict(data: dict[str, Any], goal: str) -> PlanResult:
        """Convert a dict response back to a PlanResult."""
        raw_changes = data.get('changes', [])
        changes = [
            PlannedChange(
                file_path=c.get('file_path', ''),
                change_type=c.get('change_type', 'modify'),
                description=c.get('description', ''),
                dependencies=c.get('dependencies', []),
                estimated_tokens=c.get('estimated_tokens', 0),
                risk_level=c.get('risk_level', 'low'),
                acceptance_criteria=c.get('acceptance_criteria', []),
            )
            for c in raw_changes
        ]
        return PlanResult(
            goal=goal,
            summary=data.get('summary', ''),
            changes=changes,
            execution_order=data.get('execution_order', [c.file_path for c in changes]),
            estimated_total_tokens=data.get('estimated_total_tokens', 0),
            complexity_score=data.get('complexity_score', 0.0),
            warnings=data.get('warnings', []),
        )

    async def _on_shutdown(self) -> None:
        _logger.debug('PlannerAgent: shutdown')
