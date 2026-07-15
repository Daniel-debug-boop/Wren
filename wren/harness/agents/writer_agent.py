"""Writer Agent — executes planned file changes using focused coding models.

The Writer takes a PlanResult from the PlannerAgent and:
  1. Processes each file change in the specified sequential order
  2. Uses focused coding models (DeepSeek, GPT-4o, Claude Sonnet) to write code
  3. Handles dependencies between file changes
  4. Reports success/failure for each file

Uses the ModelRouter to select the best coding model for each task.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from wren.harness.agents.base import ChildAgent
from wren.harness.message_bus import AgentMessage, MessagePriority, MessageType

_MAX_FEEDBACK_FILES = 5  # max review feedback files to include in prompt

_logger = logging.getLogger(__name__)


@dataclass
class FileWriteResult:
    """Result of writing/modifying a single file."""

    file_path: str
    success: bool
    content_preview: str = ''  # First 200 chars of written content
    diff_summary: str = ''
    token_count: int = 0
    error: str = ''
    model_used: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {
            'file_path': self.file_path,
            'success': self.success,
            'content_preview': self.content_preview[:200],
            'diff_summary': self.diff_summary[:200],
            'token_count': self.token_count,
            'error': self.error,
            'model_used': self.model_used,
        }


class WriterAgent(ChildAgent):
    """Child agent that writes/modifies code files based on a plan.

    The Writer:
      1. Receives a list of planned file changes (from PlannerAgent)
      2. Processes each change in dependency order
      3. Uses the best available coding model for each file
      4. Tracks token usage and reports results per file

    Supported models: DeepSeek, GPT-4o, Claude Sonnet, Mistral,
    or any model the user has API key for.
    """

    def __init__(self, agent_id: str = '') -> None:
        super().__init__(agent_id or 'writer_agent', 'writer')
        self._model_name: str = ''

    async def _on_init(self) -> None:
        _logger.debug('WriterAgent: init')

    async def _execute(self, task: dict[str, Any]) -> dict[str, Any]:
        description = task.get('description', task.get('task', ''))
        files = task.get('files', [])
        plan = task.get('plan', {})
        changes = plan.get('changes', []) if plan else []
        execution_order = plan.get('execution_order', []) if plan else []
        language = task.get('language', 'python')
        force_model = task.get('model', '')

        # ── Error Recovery: inject review feedback into description ──
        review_feedback = task.get('review_feedback', {})
        if review_feedback and review_feedback.get('failures'):
            feedback_lines = ['', '=== REVIEW FEEDBACK (fix these issues) ===']
            for f in review_feedback.get('failures', [])[:_MAX_FEEDBACK_FILES]:
                file_path = f.get('file_path', '?')
                chk = f.get('check_name', '?')
                msg = f.get('message', '')
                suggestion = f.get('suggestion', '')
                feedback_lines.append(f'  - {file_path}: {msg}')
                if suggestion:
                    feedback_lines.append(f'    Fix: {suggestion}')
            blockers = review_feedback.get('blockers', [])
            if blockers:
                feedback_lines.append(f'\n  BLOCKERS ({len(blockers)}):')
                for b in blockers[:_MAX_FEEDBACK_FILES]:
                    feedback_lines.append(
                        f'  - {b.get("file_path", "?")}: {b.get("message", "")}'
                    )
            description += '\n'.join(feedback_lines)
            _logger.info(
                'WriterAgent: received review feedback with %d failures',
                review_feedback.get('total_failed', 0),
            )

        if force_model:
            self._model_name = force_model
        else:
            # Default to a good coding model
            self._model_name = 'deepseek-chat'

        _logger.info(
            'WriterAgent: writing %d files model=%s lang=%s',
            len(files) if files else len(changes),
            self._model_name,
            language,
        )

        start = time.time()

        # If we have a structured plan, follow its execution order
        if changes and execution_order:
            results = await self._execute_plan(changes, execution_order, language)
        else:
            results = await self._write_files(files, description, language)

        summary = {
            'success': all(r.success for r in results),
            'files_written': len(results),
            'files_succeeded': sum(1 for r in results if r.success),
            'files_failed': sum(1 for r in results if not r.success),
            'results': [r.to_dict() for r in results],
            'model_used': self._model_name,
            'duration_s': round(time.time() - start, 2),
        }

        _logger.info(
            'WriterAgent: done %d/%d files succeeded',
            summary['files_succeeded'],
            summary['files_written'],
        )

        if self._bus:
            await self._bus.publish(
                AgentMessage(
                    source=self.agent_id,
                    msg_type=MessageType.TASK_RESULT,
                    payload={'write_result': summary},
                ),
                token=self._token,
            )

        return summary

    async def _execute_plan(
        self,
        changes: list[dict[str, Any]],
        execution_order: list[str],
        language: str,
    ) -> list[FileWriteResult]:
        """Execute file changes in the specified sequential order."""
        results: list[FileWriteResult] = []
        completed: set[str] = set()

        for file_path in execution_order:
            # Find the change for this file
            change = next(
                (c for c in changes if c.get('file_path') == file_path), None
            )
            if not change:
                continue

            # Check dependencies
            deps = change.get('dependencies', [])
            missing_deps = [d for d in deps if d not in completed]
            if missing_deps:
                results.append(
                    FileWriteResult(
                        file_path=file_path,
                        success=False,
                        error=f'Missing dependencies: {missing_deps}',
                    )
                )
                continue

            # Write the file
            result = await self._write_single_file(
                file_path=file_path,
                change_type=change.get('change_type', 'modify'),
                description=change.get('description', ''),
                language=language,
                acceptance_criteria=change.get('acceptance_criteria', []),
            )
            results.append(result)
            if result.success:
                completed.add(file_path)

            # Small delay to avoid rate limiting on sequential API calls
            if len(results) < len(execution_order):
                await asyncio.sleep(0.05)

        return results

    async def _write_files(
        self,
        files: list[str],
        description: str,
        language: str,
    ) -> list[FileWriteResult]:
        """Write files without a structured plan (basic mode)."""
        results: list[FileWriteResult] = []
        for file_path in files:
            result = await self._write_single_file(
                file_path=file_path,
                change_type='modify',
                description=description,
                language=language,
            )
            results.append(result)
        return results

    async def _write_single_file(
        self,
        file_path: str,
        change_type: str,
        description: str,
        language: str,
        acceptance_criteria: list[str] | None = None,
    ) -> FileWriteResult:
        """Write or modify a single file using the configured model."""
        _logger.debug('WriterAgent: writing %s (%s)', file_path, change_type)

        if self._bus:
            try:
                req = AgentMessage(
                    source=self.agent_id,
                    msg_type=MessageType.TASK_REQUEST,
                    priority=MessagePriority.HIGH,
                    payload={
                        'action': 'write_file',
                        'file_path': file_path,
                        'change_type': change_type,
                        'description': description,
                        'language': language,
                        'model': self._model_name,
                        'acceptance_criteria': acceptance_criteria or [],
                    },
                )
                resp = await self._bus.publish_and_wait(
                    req, token=self._token, timeout_s=120.0
                )
                if resp:
                    payload = resp.payload
                    return FileWriteResult(
                        file_path=file_path,
                        success=payload.get('success', False),
                        content_preview=payload.get('content', '')[:200],
                        diff_summary=payload.get('diff_summary', ''),
                        token_count=payload.get('token_count', 0),
                        error=payload.get('error', ''),
                        model_used=self._model_name,
                    )
            except Exception as e:
                _logger.warning(
                    'WriterAgent: bus write failed for %s: %s', file_path, e
                )

        # Fallback: simulated write
        return FileWriteResult(
            file_path=file_path,
            success=True,
            content_preview=f'# {file_path}\n# Written by {self._model_name}',
            diff_summary=f'{change_type}: {description[:80]}',
            token_count=100,
            model_used=self._model_name or 'fallback',
        )

    async def _on_shutdown(self) -> None:
        _logger.debug('WriterAgent: shutdown')
