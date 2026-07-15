"""Coding harness (v2) — proper child agent spawned by MetaOrchestrator.

Executes coding tasks with critique + quality gates. All
communication through the message bus.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from wren.harness.agents.base import ChildAgent
from wren.harness.message_bus import AgentMessage, MessagePriority, MessageType
from wren.harness.reflection.quality_gates import QualityGates
from wren.harness.reflection.self_critique import SelfCritiqueAgent

_logger = logging.getLogger(__name__)


class CodingHarness(ChildAgent):
    """Child agent that writes, reviews, and verifies code."""

    def __init__(self, agent_id: str = '') -> None:
        super().__init__(agent_id or 'coding_harness', 'coding')
        self._critiquer = SelfCritiqueAgent()
        self._quality = QualityGates()

    async def _on_init(self) -> None:
        _logger.debug('CodingHarness: init')

    async def _execute(self, task: dict[str, Any]) -> dict[str, Any]:
        description = task.get('description', task.get('task', ''))
        language = task.get('language', 'python')
        files = task.get('files', [])
        _logger.info('CodingHarness: task="%s" lang=%s', description[:60], language)

        start = time.time()

        # Publish task request to bus → agent
        if self._bus:
            req = AgentMessage(
                source=self.agent_id,
                msg_type=MessageType.TASK_REQUEST,
                priority=MessagePriority.HIGH,
                payload={
                    'task': description,
                    'files': files,
                    'language': language,
                    'action': 'code',
                },
            )
            resp = await self._bus.publish_and_wait(
                req, token=self._token, timeout_s=120.0
            )
            code_output = resp.payload.get('output', '') if resp else ''
            files_changed = resp.payload.get('files_changed', []) if resp else []
        else:
            code_output = f'# Simulated code for: {description}'
            files_changed = files

        # Critique
        critique = self._critiquer.critique_code(code_output, language=language)

        # Quality gates
        import asyncio

        qctx: dict[str, Any] = {
            'response': code_output,
            'critique_score': critique.score,
            'blockers': [str(f) for f in critique.blockers],
        }
        quality = await self._quality.run_all(qctx)

        result = {
            'success': quality.passed,
            'output': code_output,
            'files_changed': files_changed,
            'critique_score': critique.score,
            'critique_findings': len(critique.findings),
            'quality_passed': quality.passed,
            'duration_s': round(time.time() - start, 2),
        }

        # Publish result
        if self._bus:
            await self._bus.publish(
                AgentMessage(
                    source=self.agent_id,
                    msg_type=MessageType.TASK_RESULT,
                    payload={'task': description, **result},
                ),
                token=self._token,
            )

        _logger.info(
            'CodingHarness: done success=%s score=%.2f',
            result['success'],
            critique.score,
        )
        return result

    async def _on_shutdown(self) -> None:
        _logger.debug('CodingHarness: shutdown')
