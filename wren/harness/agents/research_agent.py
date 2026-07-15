"""Research agent (v2) — proper child agent spawned by MetaOrchestrator.

Autonomous web research with source tracking. All communication
through the message bus.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from wren.harness.agents.base import ChildAgent
from wren.harness.message_bus import AgentMessage, MessagePriority, MessageType

_logger = logging.getLogger(__name__)


class ResearchAgent(ChildAgent):
    """Child agent that researches topics via the message bus."""

    def __init__(self, agent_id: str = '') -> None:
        uid = agent_id or f'research_{uuid.uuid4().hex[:8]}'
        super().__init__(uid, 'research')

    async def _on_init(self) -> None:
        _logger.debug('ResearchAgent: init')

    async def _execute(self, task: dict[str, Any]) -> dict[str, Any]:
        query = task.get('description', task.get('task', ''))
        depth = task.get('depth', 'standard')
        _logger.info('ResearchAgent: query="%s" depth=%s', query[:60], depth)

        start = time.time()

        if self._bus:
            req = AgentMessage(
                source=self.agent_id,
                msg_type=MessageType.TASK_REQUEST,
                priority=MessagePriority.MEDIUM,
                payload={
                    'task': f'Research: {query}',
                    'depth': depth,
                    'action': 'research',
                },
            )
            resp = await self._bus.publish_and_wait(
                req, token=self._token, timeout_s=60.0
            )
            if resp:
                result = {
                    'success': resp.payload.get('success', False),
                    'summary': resp.payload.get('summary', ''),
                    'sources': resp.payload.get('sources', []),
                    'key_findings': resp.payload.get('key_findings', []),
                    'confidence': resp.payload.get('confidence', 0.5),
                    'duration_s': round(time.time() - start, 2),
                }
            else:
                result = {
                    'success': False,
                    'error': 'No response',
                    'duration_s': round(time.time() - start, 2),
                }
        else:
            result = {
                'success': True,
                'summary': f'Simulated research for: {query}',
                'sources': [],
                'key_findings': [],
                'confidence': 0.5,
                'duration_s': round(time.time() - start, 2),
            }

        _logger.info('ResearchAgent: done success=%s', result['success'])
        return result

    async def _on_shutdown(self) -> None:
        _logger.debug('ResearchAgent: shutdown')

    # ── Convenience (called by parent for quick lookups) ─────────

    async def search_and_summarise(self, query: str, max_sources: int = 5) -> str:
        """Quick search → summary pipeline."""
        result = await self._execute({'description': query})
        if not result.get('success'):
            return f'Research failed: {result.get("error", "unknown")}'
        lines = [f'## {query}', '', result.get('summary', ''), '', '### Sources']
        for s in result.get('sources', [])[:max_sources]:
            lines.append(f'- {s}')
        return '\n'.join(lines)
