"""Think-before-you-act pipeline.

Every child agent runs through this BEFORE executing any task.
The pipeline forces:
  1. Goal clarification — what exactly needs to happen
  2. Risk assessment — what could go wrong
  3. Plan generation — step-by-step execution plan
  4. Resource estimation — tokens, time, tools needed
  5. Rollback plan — how to undo if it fails

The thinking output is stored in the database and available
for post-hoc analysis.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from wren.harness.telemetry import T


class RiskLevel(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


@dataclass
class Risk:
    description: str = ''
    level: RiskLevel = RiskLevel.LOW
    likelihood: float = 0.0  # 0-1
    impact: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {
            'description': self.description[:200],
            'level': self.level.value,
            'likelihood': round(self.likelihood, 2),
            'impact': self.impact[:200],
        }


@dataclass
class ThinkOutput:
    """Result of the think-before-you-act pipeline."""

    thought_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    agent_id: str = ''
    task_name: str = ''
    goal_clarification: str = ''
    risks: list[Risk] = field(default_factory=list)
    risk_score: float = 0.0
    plan_steps: list[str] = field(default_factory=list)
    estimated_tokens: int = 0
    estimated_time_s: float = 0.0
    estimated_tools: list[str] = field(default_factory=list)
    rollback_plan: str = ''
    capability_summary: str = ''  # SDK-generated tool inventory for system prompt
    approved: bool = True
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            'thought_id': self.thought_id,
            'agent_id': self.agent_id,
            'task_name': self.task_name,
            'goal_clarification': self.goal_clarification[:300],
            'risks': [r.to_dict() for r in self.risks],
            'risk_score': round(self.risk_score, 2),
            'plan_steps': self.plan_steps[:10],
            'estimated_tokens': self.estimated_tokens,
            'estimated_time_s': round(self.estimated_time_s, 1),
            'estimated_tools': self.estimated_tools[:10],
            'rollback_plan': self.rollback_plan[:300],
            'capability_summary': self.capability_summary[:200]
            if self.capability_summary
            else '',
            'approved': self.approved,
            'duration_ms': round(self.duration_ms, 1),
        }


class ThinkPipeline:
    """Forced thinking pipeline — runs before every agent action.

    Can be overridden per agent type, but defaults catch all.
    """

    def __init__(self, agent_id: str = '', agent_type: str = '') -> None:
        self._agent_id = agent_id
        self._agent_type = agent_type

    async def think(self, task: dict[str, Any]) -> ThinkOutput:
        """Run the think-before-you-act pipeline.

        Called by EVERY child agent before receive_task().
        Returns a ThinkOutput with approval flag.
        """
        start = time.time()
        desc = task.get('description', task.get('task', ''))
        name = task.get('name', 'unnamed')

        output = ThinkOutput(
            agent_id=self._agent_id,
            task_name=name,
        )

        # 1. Goal clarification
        output.goal_clarification = self._clarify_goal(desc, task)

        # 2. Risk assessment
        output.risks = self._assess_risks(desc, task)
        output.risk_score = max((r.likelihood * 1.0 for r in output.risks), default=0.0)
        high_risks = [
            r for r in output.risks if r.level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        ]
        if high_risks:
            output.approved = False  # auto-deny high-risk tasks unless overridden

        # 3. Plan generation
        output.plan_steps = self._generate_plan(name, desc, task)

        # 4. Resource estimation
        output.estimated_tokens = self._estimate_tokens(desc, output.plan_steps)
        output.estimated_time_s = self._estimate_time(desc, output.plan_steps)
        output.estimated_tools = self._estimate_tools(desc, task)

        # 5. Rollback plan
        output.rollback_plan = self._rollback_plan(name, desc)

        # 6. Capability summary from SDK
        try:
            from wren.harness.sdk_wiring import get_sdk_context

            ctx = get_sdk_context()
            output.capability_summary = ctx.system_prompt_addendum[:500]
        except Exception:
            output.capability_summary = ''

        output.duration_ms = (time.time() - start) * 1000

        # Emit telemetry
        T.info(
            'think.completed',
            f'agent={self._agent_id} task={name} '
            f'risks={len(output.risks)} steps={len(output.plan_steps)} '
            f'approved={output.approved} duration_ms={output.duration_ms:.0f}',
            tags=['thinking', self._agent_type],
        )

        return output

    # ── Heuristics (can be overridden by subclasses) ─────────────

    @staticmethod
    def _clarify_goal(desc: str, task: dict[str, Any]) -> str:
        """Clarify what exactly needs to happen."""
        lang = task.get('language', 'unknown')
        files = task.get('files', [])
        parts = [f'Execute: {desc[:200]}']
        if files:
            parts.append(f'Affected files: {", ".join(files[:5])}')
        if lang != 'unknown':
            parts.append(f'Language: {lang}')
        return ' | '.join(parts)

    @staticmethod
    def _assess_risks(desc: str, task: dict[str, Any]) -> list[Risk]:
        """Assess risks based on task description."""
        risks: list[Risk] = []
        dl = desc.lower()

        if any(kw in dl for kw in ['delete', 'drop', 'remove', 'rm ', 'destroy']):
            risks.append(
                Risk(
                    'Destructive operation',
                    RiskLevel.HIGH,
                    0.7,
                    'May permanently remove data',
                )
            )
        if any(kw in dl for kw in ['deploy', 'production', 'prod', 'live']):
            risks.append(
                Risk(
                    'Production deployment',
                    RiskLevel.HIGH,
                    0.6,
                    'May affect live users',
                )
            )
        if any(kw in dl for kw in ['docker', 'container', 'network']):
            risks.append(
                Risk(
                    'Infrastructure operation',
                    RiskLevel.MEDIUM,
                    0.4,
                    'May affect system resources',
                )
            )
        if any(kw in dl for kw in ['test', 'testing']):
            risks.append(
                Risk(
                    'Test execution',
                    RiskLevel.MEDIUM,
                    0.3,
                    'Tests may have side effects',
                )
            )
        if len(desc) > 500:
            risks.append(
                Risk(
                    'Long task',
                    RiskLevel.MEDIUM,
                    0.3,
                    'May exceed time or token budget',
                )
            )
        if any(kw in dl for kw in ['sudo', 'chmod', 'chown', 'root']):
            risks.append(
                Risk(
                    'Privileged operation',
                    RiskLevel.CRITICAL,
                    0.8,
                    'Escalated privileges required',
                )
            )

        return risks

    @staticmethod
    def _generate_plan(name: str, desc: str, task: dict[str, Any]) -> list[str]:
        """Generate step-by-step execution plan."""
        steps = [f'Understand: {desc[:100]}']
        lang = task.get('language', '')
        if lang:
            steps.append(f'Prepare {lang} environment')
        steps.append('Execute the task')
        if task.get('action') in ('code', 'research'):
            steps.append('Verify output quality')
        steps.append('Report result')
        return steps

    @staticmethod
    def _estimate_tokens(desc: str, steps: list[str]) -> int:
        base = len(desc) // 4 + 100
        step_cost = len(steps) * 50
        return min(base + step_cost, 100_000)

    @staticmethod
    def _estimate_time(desc: str, steps: list[str]) -> float:
        base = len(desc) / 100  # ~1s per 100 chars
        step_time = len(steps) * 2.0
        return min(base + step_time, 600.0)

    @staticmethod
    def _estimate_tools(desc: str, task: dict[str, Any]) -> list[str]:
        """Estimate tools needed — enhanced with SDK ToolRegistry when available."""
        tools = ['python3']
        dl = desc.lower()
        if any(kw in dl for kw in ['docker', 'container']):
            tools.append('docker')
        if any(kw in dl for kw in ['npm', 'node', 'javascript', 'react']):
            tools.append('node')
        if any(kw in dl for kw in ['git', 'clone', 'push', 'commit']):
            tools.append('git')
        if any(kw in dl for kw in ['deploy', 'http', 'api', 'curl']):
            tools.append('curl')

        # Use SDK ToolRegistry for intelligent tool suggestions
        try:
            from wren.harness.sdk_wiring import get_sdk_context

            ctx = get_sdk_context()
            for tool_def in ctx.registry.list_all():
                # Check if task matches tool's best_for patterns
                for pattern in tool_def.best_for:
                    if any(kw in dl for kw in pattern.split()):
                        if tool_def.name not in tools:
                            tools.append(tool_def.name)
                        break
        except Exception:
            pass  # SDK not available, use fallback heuristics

        return tools[:8]

    @staticmethod
    def _rollback_plan(name: str, desc: str) -> str:
        dl = desc.lower()
        if any(kw in dl for kw in ['file', 'write', 'create', 'edit']):
            return 'Revert file changes via git checkout or backup'
        if any(kw in dl for kw in ['deploy', 'install', 'update']):
            return 'Rollback to previous version'
        if any(kw in dl for kw in ['delete', 'drop', 'remove']):
            return 'Restore from backup or confirm before proceeding'
        return 'No automatic rollback — manual verification required'
