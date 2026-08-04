"""Terminal execution service with security sandbox.

Provides subprocess execution with:
- Command timeout enforcement
- Workspace confinement
- Blocked dangerous commands
- Output streaming via async generators
"""

from __future__ import annotations

import asyncio
import logging
import os
import shlex
from pathlib import Path
from typing import Any, AsyncGenerator

_logger = logging.getLogger(__name__)

# Commands that are blocked in the sandbox for security
_BLOCKED_COMMANDS: set[str] = {
    'rm', 'rmdir', 'mkfs', 'dd', 'format',
    'shutdown', 'reboot', 'halt', 'poweroff',
    'sudo', 'su', 'chmod', 'chown', 'chgrp',
    'mount', 'umount',
    'iptables', 'ip6tables', 'nft',
    'useradd', 'userdel', 'usermod', 'groupadd', 'groupdel',
    'passwd', 'shadow',
    'crontab',
    'systemctl', 'service',
    'docker', 'docker-compose', 'podman',
    'kubectl', 'helm',
    'nc', 'ncat', 'netcat',
    'ssh', 'scp', 'rsync',
    'wget', 'curl',  # Can be unblocked per-session if needed
    'python', 'python3', 'node', 'npm', 'npx',  # Re-allowed via run_script
}

# Patterns that indicate dangerous operations in arguments
_DANGEROUS_PATTERNS = [
    '>', '/dev/', '/proc/', '/sys/',
    '>/etc/', '| rm ', '| sudo ',
    '--force', '-rf', '-fr',
]

# Default timeout for command execution
DEFAULT_TIMEOUT = 30  # seconds
MAX_TIMEOUT = 120  # seconds
MAX_OUTPUT_BYTES = 1024 * 1024  # 1MB output limit


def _is_command_blocked(command: str) -> tuple[bool, str]:
    """Check if a command should be blocked.

    Returns (blocked, reason).
    """
    parts = command.strip().split()
    if not parts:
        return False, ''

    # Get the base command name (handle paths like /usr/bin/sudo)
    base_cmd = os.path.basename(parts[0])

    if base_cmd in _BLOCKED_COMMANDS:
        return True, f'Command "{base_cmd}" is blocked in the sandbox'

    # Check for pipes to dangerous commands
    if '|' in command:
        segments = command.split('|')
        for segment in segments[1:]:
            seg_cmd = segment.strip().split()[0] if segment.strip() else ''
            seg_base = os.path.basename(seg_cmd)
            if seg_base in _BLOCKED_COMMANDS:
                return True, f'Piped command "{seg_base}" is blocked'

    # Check for dangerous argument patterns
    cmd_lower = command.lower()
    for pattern in _DANGEROUS_PATTERNS:
        if pattern in cmd_lower:
            return True, f'Dangerous pattern "{pattern}" detected in command'

    return False, ''


def _validate_working_dir(working_dir: str, workspace_root: str) -> str:
    """Ensure the working directory is within the workspace."""
    work = Path(working_dir).resolve()
    root = Path(workspace_root).resolve()
    try:
        work.relative_to(root)
        return str(work)
    except ValueError:
        _logger.warning(
            'Working dir %s outside workspace %s, using workspace root',
            working_dir, workspace_root,
        )
        return str(root)


async def exec_command(
    command: str,
    working_dir: str,
    workspace_root: str,
    timeout: float = DEFAULT_TIMEOUT,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Execute a shell command with security sandboxing.

    Args:
        command: The shell command to execute.
        working_dir: Working directory for execution.
        workspace_root: Workspace root for confinement.
        timeout: Execution timeout in seconds.
        env: Additional environment variables.

    Returns:
        Dict with stdout, stderr, exit_code, timed_out.
    """
    # Security checks
    blocked, reason = _is_command_blocked(command)
    if blocked:
        return {
            'stdout': '',
            'stderr': f'Command blocked: {reason}',
            'exit_code': -1,
            'timed_out': False,
            'command': command,
        }

    # Constrain working directory
    safe_dir = _validate_working_dir(working_dir, workspace_root)
    timeout = min(timeout, MAX_TIMEOUT)

    # Build environment
    exec_env = os.environ.copy()
    exec_env['TERM'] = 'dumb'  # Disable color codes in output
    if env:
        exec_env.update(env)

    _logger.info('Executing: %s (dir=%s, timeout=%s)', command, safe_dir, timeout)

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=safe_dir,
            env=exec_env,
            # Limit output buffer to prevent memory issues
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )
            timed_out = False
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            stdout_bytes = b''
            stderr_bytes = b'Command timed out after %.0f seconds' % timeout
            timed_out = True

        # Decode and truncate output
        stdout = stdout_bytes.decode('utf-8', errors='replace')[:MAX_OUTPUT_BYTES]
        stderr = stderr_bytes.decode('utf-8', errors='replace')[:MAX_OUTPUT_BYTES]

        return {
            'stdout': stdout,
            'stderr': stderr,
            'exit_code': proc.returncode or 0,
            'timed_out': timed_out,
            'command': command,
        }

    except Exception as e:
        _logger.error('Command execution failed: %s', e)
        return {
            'stdout': '',
            'stderr': f'Execution error: {type(e).__name__}: {e}',
            'exit_code': -1,
            'timed_out': False,
            'command': command,
        }


async def exec_command_streaming(
    command: str,
    working_dir: str,
    workspace_root: str,
    timeout: float = DEFAULT_TIMEOUT,
    env: dict[str, str] | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """Execute a command and stream output line by line.

    Yields dicts with type (stdout/stderr/exit/error) and content.
    """
    blocked, reason = _is_command_blocked(command)
    if blocked:
        yield {'type': 'error', 'content': f'Command blocked: {reason}'}
        return

    safe_dir = _validate_working_dir(working_dir, workspace_root)
    timeout = min(timeout, MAX_TIMEOUT)

    exec_env = os.environ.copy()
    exec_env['TERM'] = 'dumb'
    if env:
        exec_env.update(env)

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=safe_dir,
            env=exec_env,
        )

        async def _read_stream(
            stream: asyncio.StreamReader | None, stream_type: str
        ) -> None:
            if stream is None:
                return
            while True:
                line = await stream.readline()
                if not line:
                    break
                yield {'type': stream_type, 'content': line.decode('utf-8', errors='replace')}

        # Read stdout and stderr concurrently
        output_lines: list[dict[str, str]] = []
        try:
            # Use wait_for for the overall timeout
            done = False
            start = asyncio.get_event_loop().time()
            while not done:
                elapsed = asyncio.get_event_loop().time() - start
                if elapsed > timeout:
                    proc.kill()
                    await proc.wait()
                    yield {'type': 'error', 'content': f'\nCommand timed out after {timeout:.0f}s'}
                    return

                remaining = timeout - elapsed
                try:
                    line = await asyncio.wait_for(
                        proc.stdout.readline(),  # type: ignore
                        timeout=min(remaining, 1.0),
                    )
                    if line:
                        decoded = line.decode('utf-8', errors='replace')
                        yield {'type': 'stdout', 'content': decoded}
                        continue
                except asyncio.TimeoutError:
                    if proc.returncode is not None:
                        done = True
                        continue
                    # Check if process is still running
                    if proc.returncode is not None:
                        done = True
                        continue
                    # Process still running, keep waiting
                    continue
                # No more stdout
                done = True

            # Read remaining stderr
            stderr_data = await proc.stderr.read()  # type: ignore
            if stderr_data:
                yield {'type': 'stderr', 'content': stderr_data.decode('utf-8', errors='replace')}

            yield {'type': 'exit', 'content': str(proc.returncode or 0)}

        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            yield {'type': 'error', 'content': f'\nCommand timed out after {timeout:.0f}s'}

    except Exception as e:
        yield {'type': 'error', 'content': f'Execution error: {e}'}


async def run_script(
    language: str,
    code: str,
    working_dir: str,
    workspace_root: str,
    timeout: float = 60,
) -> dict[str, Any]:
    """Run a code snippet directly in the appropriate runtime.

    Supported languages: python, node/javascript, bash/sh.
    """
    # Map language to command prefix
    runners: dict[str, list[str]] = {
        'python': ['python3', '-c'],
        'py': ['python3', '-c'],
        'python3': ['python3', '-c'],
        'javascript': ['node', '-e'],
        'js': ['node', '-e'],
        'node': ['node', '-e'],
        'bash': ['bash', '-c'],
        'sh': ['sh', '-c'],
        'shell': ['bash', '-c'],
    }

    lang_lower = language.lower()
    runner = runners.get(lang_lower)
    if not runner:
        return {
            'stdout': '',
            'stderr': f'Unsupported language: {language}. Supported: {", ".join(runners.keys())}',
            'exit_code': -1,
            'timed_out': False,
            'command': f'{language} <code>',
        }

    # For python -c, we write to a temp file if code is too long
    if len(code) > 1000 or '\n' in code:
        # Write to temp file and run that
        suffix = '.py' if lang_lower.startswith('py') else '.js' if lang_lower in ('js', 'javascript', 'node') else '.sh'
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode='w', suffix=suffix, dir=workspace_root, delete=False
        ) as f:
            f.write(code)
            tmp_path = f.name
        try:
            if suffix == '.py':
                cmd = f'python3 {shlex.quote(tmp_path)}'
            elif suffix == '.js':
                cmd = f'node {shlex.quote(tmp_path)}'
            else:
                cmd = f'bash {shlex.quote(tmp_path)}'
            return await exec_command(cmd, working_dir, workspace_root, timeout)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    else:
        cmd_parts = runner + [code]
        command = ' '.join(shlex.quote(p) for p in cmd_parts)
        return await exec_command(command, working_dir, workspace_root, timeout)
