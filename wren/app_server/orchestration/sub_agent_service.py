"""Sub-agent service: spawns actual sub-conversations for delegated tasks.

Uses the existing `POST /api/v1/app-conversations` endpoint with
`parent_conversation_id` to create child conversations that share the
parent's sandbox, git config, and LLM model. Results are collected
by reading the sub-conversation's events.
"""

import asyncio
import logging
import time
from typing import Any

import httpx

from wren.app_server.orchestration.working_memory import WorkingMemory

_logger = logging.getLogger(__name__)


class SubAgentResult:
    """Result of a sub-agent task execution."""

    def __init__(
        self,
        sub_conversation_id: str,
        task_name: str,
        status: str = 'pending',
        result_summary: str | None = None,
        error: str | None = None,
        events_count: int = 0,
    ):
        self.sub_conversation_id = sub_conversation_id
        self.task_name = task_name
        self.status = status
        self.result_summary = result_summary
        self.error = error
        self.events_count = events_count
        self.created_at = time.time()
        self.completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            'sub_conversation_id': self.sub_conversation_id,
            'task_name': self.task_name,
            'status': self.status,
            'result_summary': self.result_summary,
            'error': self.error,
            'events_count': self.events_count,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
        }


class SubAgentService:
    """Spawns and manages sub-conversations for delegated tasks.

    Each sub-conversation runs in the same sandbox as the parent,
    inheriting its git config, LLM model, and workspace. The parent
    polls sub-conversation status and collects results.

    Uses loopback HTTP to the app-server's own REST API so no deep
    DI wiring is needed.
    """

    def __init__(
        self,
        app_server_url: str = 'http://localhost:3000',
        session_api_key: str | None = None,
        working_memory: WorkingMemory | None = None,
        poll_interval: float = 2.0,
        max_poll_time: float = 600.0,
    ):
        self._app_server_url = app_server_url.rstrip('/')
        self._session_api_key = session_api_key
        self._wm = working_memory or WorkingMemory()
        self._poll_interval = poll_interval
        self._max_poll_time = max_poll_time
        self._http = httpx.AsyncClient(timeout=30.0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def spawn_sub_task(
        self,
        parent_conversation_id: str,
        task_name: str,
        task_description: str,
        acceptance_criteria: list[str] | None = None,
        agent_type: str = 'default',
    ) -> SubAgentResult:
        """Spawn a sub-conversation for a single task.

        Posts to POST /api/v1/app-conversations with parent_conversation_id.
        The sub-conversation inherits sandbox, git, and LLM from parent.
        """
        headers = self._headers()
        payload = {
            'parent_conversation_id': parent_conversation_id,
            'agent_type': agent_type,
            'initial_message': {
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': self._build_sub_task_prompt(
                            task_name, task_description, acceptance_criteria
                        ),
                    }
                ],
            },
        }

        try:
            response = await self._http.post(
                f'{self._app_server_url}/api/v1/app-conversations',
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            sub_conv_id = data.get('conversation_id') or data.get('id', '')

            result = SubAgentResult(
                sub_conversation_id=sub_conv_id,
                task_name=task_name,
            )
            self._wm.add_decision(
                f'Spawned sub-agent for {task_name} (conv={sub_conv_id[:12]}...)',
                context='sub_agent_service',
            )
            _logger.info('SubAgent: spawned %s → conv=%s', task_name, sub_conv_id)
            return result

        except httpx.HTTPStatusError as e:
            _logger.error('SubAgent spawn failed for %s: %s', task_name, e)
            return SubAgentResult(
                sub_conversation_id='',
                task_name=task_name,
                status='failed',
                error=f'HTTP {e.response.status_code}: {e.response.text[:200]}',
            )
        except httpx.RequestError as e:
            _logger.error('SubAgent request failed for %s: %s', task_name, e)
            return SubAgentResult(
                sub_conversation_id='',
                task_name=task_name,
                status='failed',
                error=str(e),
            )

    async def spawn_sub_tasks_parallel(
        self,
        parent_conversation_id: str,
        tasks: list[dict[str, Any]],
    ) -> list[SubAgentResult]:
        """Spawn multiple sub-tasks in parallel.

        Each task dict: name, description, acceptance_criteria (optional).
        """
        coros = [
            self.spawn_sub_task(
                parent_conversation_id=parent_conversation_id,
                task_name=t['name'],
                task_description=t['description'],
                acceptance_criteria=t.get('acceptance_criteria'),
            )
            for t in tasks
        ]
        return await asyncio.gather(*coros)

    async def poll_sub_conversation(
        self,
        sub_conversation_id: str,
    ) -> dict[str, Any]:
        """Poll a sub-conversation until completion or timeout."""
        deadline = time.time() + self._max_poll_time
        url = f'{self._app_server_url}/api/v1/app-conversations/{sub_conversation_id}'

        while time.time() < deadline:
            try:
                resp = await self._http.get(url, headers=self._headers())
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get('execution_status') or data.get(
                        'status', 'running'
                    )
                    if status.upper() in (
                        'COMPLETED',
                        'STOPPED',
                        'ERROR',
                        'STUCK',
                        'CANCELLED',
                        'FAILED',
                    ):
                        return data
                elif resp.status_code == 404:
                    return {
                        'status': 'completed',
                        'note': 'sub-conversation not found (may have completed and been cleaned up)',
                    }
            except httpx.RequestError as e:
                _logger.debug('SubAgent poll error: %s', e)

            await asyncio.sleep(self._poll_interval)

        return {'status': 'timeout', 'sub_conversation_id': sub_conversation_id}

    async def collect_sub_task_result(
        self,
        result: SubAgentResult,
    ) -> SubAgentResult:
        """Wait for a sub-task to complete and collect its result."""
        if not result.sub_conversation_id:
            result.status = 'failed'
            return result

        status_data = await self.poll_sub_conversation(result.sub_conversation_id)
        raw_status = str(status_data.get('status', 'unknown')).upper()

        if raw_status in ('COMPLETED', 'STOPPED'):
            result.status = 'completed'
            result.result_summary = (
                status_data.get('title')
                or status_data.get('summary')
                or 'Task completed'
            )
        elif raw_status in ('ERROR', 'STUCK', 'FAILED', 'TIMEOUT'):
            result.status = 'failed'
            result.error = (
                status_data.get('error')
                or status_data.get('last_error')
                or f'Sub-conversation ended with status {raw_status}'
            )
        else:
            result.status = 'timeout'
            result.error = 'Sub-conversation did not complete within timeout'

        result.completed_at = time.time()
        self._wm.add_progress(
            step=result.task_name,
            status=result.status,
            detail=f'{result.result_summary or result.error or ""}',
        )
        return result

    async def execute_sub_tasks(
        self,
        parent_conversation_id: str,
        tasks: list[dict[str, Any]],
        sequential: bool = False,
    ) -> list[SubAgentResult]:
        """Execute multiple sub-tasks and collect all results.

        Args:
            parent_conversation_id: Parent conversation ID
            tasks: List of task dicts (name, description, acceptance_criteria)
            sequential: If True, run tasks one at a time (ordered).
                        If False, run all in parallel.

        Returns:
            List of SubAgentResult with final statuses
        """
        if sequential:
            results = []
            for t in tasks:
                r = await self.spawn_sub_task(
                    parent_conversation_id,
                    t['name'],
                    t['description'],
                    t.get('acceptance_criteria'),
                )
                r = await self.collect_sub_task_result(r)
                results.append(r)
            return results
        else:
            results = await self.spawn_sub_tasks_parallel(parent_conversation_id, tasks)
            return await asyncio.gather(
                *[self.collect_sub_task_result(r) for r in results]
            )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_sub_task_prompt(
        self,
        name: str,
        description: str,
        acceptance_criteria: list[str] | None = None,
    ) -> str:
        parts = [f'# Task: {name}', '', description, '']
        if acceptance_criteria:
            parts.append('## Acceptance Criteria')
            for c in acceptance_criteria:
                parts.append(f'- {c}')
            parts.append('')
        parts.append(
            'Complete this task autonomously. Report your result, '
            'any files changed, and any issues encountered.'
        )
        return '\n'.join(parts)

    def _headers(self) -> dict[str, str]:
        h = {'Content-Type': 'application/json'}
        if self._session_api_key:
            h['X-Session-API-Key'] = self._session_api_key
        return h

    async def close(self) -> None:
        await self._http.aclose()
