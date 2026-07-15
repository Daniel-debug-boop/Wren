"""Self-memory loop: post-task reflection, lesson extraction, and persistent learning.

After each task phase completes, the agent reflects on what worked, what didn't,
and what to change. Reflections are persisted to the FableMemory system for
cross-session recall and to working memory for in-session awareness.
"""

import logging
import time
from typing import Any

from wren.app_server.orchestration.working_memory import WorkingMemory
from wren.server.memory.fable_memory import FableMemoryManager

_logger = logging.getLogger(__name__)


class SelfMemoryLoop:
    """Post-task reflection and persistent learning loop.

    Usage:
        loop = SelfMemoryLoop(project_root='/path')
        report = await loop.reflect(
            task_description='Deploy PostgreSQL',
            outcome='success',
            observations='Used docker-compose, worked first try',
            tags=['deploy', 'docker'],
        )
    """

    def __init__(
        self,
        project_root: str | None = None,
        working_memory: WorkingMemory | None = None,
        fable_memory: FableMemoryManager | None = None,
    ):
        self._wm = working_memory or WorkingMemory(project_root)
        self._fable = fable_memory or FableMemoryManager(
            storage_path=(
                f'{project_root or "."}/.wren/fable_memory.json'
                if project_root
                else '~/.wren/fable_memory.json'
            ),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def reflect(
        self,
        task_description: str,
        outcome: str,
        observations: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run the full reflection cycle for a completed task."""
        summary = self._build_summary(task_description, outcome, observations)
        lessons = self._extract_lessons(outcome, observations)

        # Store in working memory (in-session awareness)
        self._wm.add_reflection(summary, tags=tags)

        # Store lessons in FableMemory (cross-session persistence)
        lesson_ids = []
        for lesson in lessons:
            lid = await self._fable.update_lesson(
                short_summary=lesson,
                tags=tags,
            )
            if lid:
                lesson_ids.append(lid)

        # Update preferences if outcome was particularly good or bad
        if outcome == 'success':
            key = f'strategy.{tags[0] if tags else "general"}'
            await self._fable.set_preference(
                key=key,
                value=f'Use this approach for {task_description}',
            )
        elif outcome == 'failure':
            key = f'pitfall.{tags[0] if tags else "general"}'
            await self._fable.set_preference(
                key=key,
                value=f'Avoid this approach for {task_description}',
            )

        result = {
            'summary': summary,
            'lessons': lessons,
            'lesson_ids': lesson_ids,
            'outcome': outcome,
            'timestamp': time.time(),
        }
        _logger.info('SelfMemoryLoop.reflect: %s', result)
        return result

    async def compile_context(self, task_context: str = '') -> str:
        """Compile relevant memories into a system prompt block."""
        return await self._fable.compile_system_instruction(
            context_query=task_context,
        )

    def recent_lessons(self, limit: int = 5) -> list[str]:
        reflections = self._wm.query('reflection', limit=limit)
        return [r['content'] for r in reflections]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_summary(
        self,
        task_description: str,
        outcome: str,
        observations: str,
    ) -> str:
        return (
            f'Task: {task_description} | '
            f'Outcome: {outcome} | '
            f'Observations: {observations[:200]}'
        )

    def _extract_lessons(self, outcome: str, observations: str) -> list[str]:
        """Extract actionable lessons from observations.

        In a full implementation this would use an LLM call. For now,
        we do simple keyword-based extraction.
        """
        lessons = []
        obs_lower = observations.lower()

        if outcome == 'success':
            # Extract what worked
            if 'docker' in obs_lower:
                lessons.append(
                    'Docker-based deployments are reliable; prefer docker-compose'
                )
            if 'mcp' in obs_lower:
                lessons.append(
                    'MCP server auto-discovery works; add to marketplace on success'
                )
            if 'pip' in obs_lower or 'npm' in obs_lower:
                lessons.append(
                    'Package installation via pip/npm is straightforward sandboxed'
                )
            lessons.append(f'Strategy succeeded: {observations[:100]}')
        elif outcome == 'failure':
            if 'not found' in obs_lower or 'missing' in obs_lower:
                lessons.append(
                    'Check tool availability before execution; use ToolInventory'
                )
            if 'timeout' in obs_lower:
                lessons.append('Increase timeouts for first-time setup operations')
            if 'permission' in obs_lower or 'denied' in obs_lower:
                lessons.append(
                    'Sandbox permissions must be checked before file operations'
                )
            lessons.append(f'Avoid: {observations[:100]}')

        return lessons
