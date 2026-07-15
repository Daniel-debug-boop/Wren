"""Execution sandbox — subprocess-based shell, code, and container execution.

Commands are executed via asyncio subprocess. Results are also
published on the message bus for observability.
"""

from __future__ import annotations

import asyncio
import logging
import shlex
import time
from dataclasses import dataclass, field
from typing import Any

from wren.harness.message_bus import (
    AgentMessage,
    MessageBus,
    MessagePriority,
    MessageType,
)

_logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    success: bool = False
    stdout: str = ''
    stderr: str = ''
    exit_code: int = -1
    duration_s: float = 0.0
    error: str = ''


class ExecutionSandbox:
    """Subprocess-based sandboxed execution environment.

    Runs shell commands directly via asyncio.create_subprocess_shell.
    Results are also published on the message bus for observability.
    """

    def __init__(self, message_bus: MessageBus, budget: Any = None) -> None:
        self._bus = message_bus
        self._budget = budget
        self._name = 'sandbox'

    # ── Shell ────────────────────────────────────────────────────

    async def shell(
        self,
        command: str,
        timeout_s: float = 30.0,
        workdir: str = '',
    ) -> ExecutionResult:
        """Execute a shell command directly via subprocess."""
        # Budget check: reject shell commands if budget exhausted
        if self._budget:
            try:
                self._budget.check('shell_calls', 1.0)
            except Exception as e:
                return ExecutionResult(
                    success=False,
                    error=f'Budget limit: {e}',
                    duration_s=0.0,
                )

        start = time.time()
        _logger.debug('Sandbox shell: %s', command[:120])

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir or None,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout_s
            )
            exit_code = proc.returncode or -1
            result = ExecutionResult(
                success=exit_code == 0,
                stdout=stdout.decode(errors='replace'),
                stderr=stderr.decode(errors='replace'),
                exit_code=exit_code,
                duration_s=time.time() - start,
            )
        except asyncio.TimeoutError:
            if proc:
                proc.kill()
                await proc.wait()
            result = ExecutionResult(
                success=False,
                error=f'Command timed out after {timeout_s}s',
                duration_s=time.time() - start,
            )
        except FileNotFoundError as e:
            result = ExecutionResult(
                success=False,
                error=f'Command not found: {e}',
                duration_s=time.time() - start,
            )
        except Exception as e:
            result = ExecutionResult(
                success=False,
                error=str(e),
                duration_s=time.time() - start,
            )

        # Publish result on bus for observability
        try:
            await self._bus.publish(
                AgentMessage(
                    source=self._name,
                    msg_type=MessageType.TASK_RESULT,
                    priority=MessagePriority.LOW,
                    payload={
                        'action': 'shell_result',
                        'command': command[:200],
                        'success': result.success,
                        'exit_code': result.exit_code,
                        'stdout_len': len(result.stdout),
                        'stderr_len': len(result.stderr),
                        'duration_s': round(result.duration_s, 2),
                    },
                )
            )
        except Exception:
            pass  # Don't fail if bus publish fails

        return result

    # ── Browser ──────────────────────────────────────────────────

    async def browser_navigate(
        self, url: str, timeout_s: float = 15.0
    ) -> ExecutionResult:
        """Navigate a browser to URL."""
        return await self.shell(
            f'python3 -m webbrowser -t "{url}"', timeout_s=timeout_s
        )

    async def browser_screenshot(self, url: str = '') -> ExecutionResult:
        """Take a screenshot (requires playwright)."""
        cmd = 'playwright screenshot'
        if url:
            cmd += f' "{url}"'
        return await self.shell(cmd, timeout_s=20.0)

    # ── Code interpreter ─────────────────────────────────────────

    async def python(
        self,
        code: str,
        timeout_s: float = 30.0,
    ) -> ExecutionResult:
        """Execute Python code directly."""
        return await self.shell(
            f'python3 -c {shlex.quote(code)}',
            timeout_s=timeout_s,
        )

    async def python_file(
        self,
        filepath: str,
        args: str = '',
        timeout_s: float = 30.0,
    ) -> ExecutionResult:
        """Execute a Python file."""
        return await self.shell(
            f'python3 {filepath} {args}',
            timeout_s=timeout_s,
        )

    # ── Container ────────────────────────────────────────────────

    async def container_run(
        self,
        image: str,
        command: str,
        timeout_s: float = 60.0,
    ) -> ExecutionResult:
        """Run a command in a container."""
        return await self.shell(
            f'docker run --rm {image} {command}',
            timeout_s=timeout_s,
        )
