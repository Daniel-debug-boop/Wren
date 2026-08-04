"""Real PTY terminal service using Python's pty module.

Allocates a real pseudo-terminal (PTY) for each WebSocket connection,
providing a fully interactive shell experience (bash, zsh, etc.).

Features:
- Real PTY allocation with proper signal handling
- Window resize support (SIGWINCH)
- Workspace directory confinement
- Process cleanup on disconnect
"""

from __future__ import annotations

import asyncio
import fcntl
import logging
import os
import pty
import signal
import struct
import sys
import termios
from typing import Any

_logger = logging.getLogger(__name__)

# Default shell
_DEFAULT_SHELL = os.getenv('WREN_SHELL', '/bin/bash')

# PTY read buffer size
_READ_BUFFER_SIZE = 4096


class PTYProcess:
    """Manages a single PTY process for a terminal session."""

    def __init__(
        self,
        working_dir: str | None = None,
        shell: str | None = None,
        cols: int = 80,
        rows: int = 24,
        env: dict[str, str] | None = None,
    ):
        self.working_dir = working_dir or os.getcwd()
        self.shell = shell or _DEFAULT_SHELL
        self.cols = cols
        self.rows = rows
        self.env = env or {}
        self.master_fd: int | None = None
        self.child_pid: int | None = None
        self._running = False

    def spawn(self) -> int:
        """Spawn the PTY process. Returns the child PID.

        Uses pty.fork() to create a child process with a pseudo-terminal.
        The child runs the specified shell in the working directory.
        """
        # Save original terminal settings
        old_term = None
        if sys.stdin.isatty():
            try:
                old_term = termios.tcgetattr(sys.stdin)
            except termios.error:
                old_term = None

        # Fork with PTY
        child_pid, master_fd = pty.openpty()

        if child_pid == 0:
            # Child process
            try:
                # Set working directory
                os.chdir(self.working_dir)

                # Set environment
                exec_env = os.environ.copy()
                exec_env['TERM'] = 'xterm-256color'
                exec_env['SHELL'] = self.shell
                exec_env['COLORTERM'] = 'truecolor'
                exec_env.update(self.env)

                # Set initial window size
                winsize = struct.pack('HHHH', self.rows, self.cols, 0, 0)
                fcntl.ioctl(sys.stdout.fileno(), termios.TIOCSWINSZ, winsize)

                # Execute shell
                os.execvpe(self.shell, [self.shell, '--login'], exec_env)
            except Exception as e:
                _logger.error('Child process exec failed: %s', e)
                os._exit(1)
        else:
            # Parent process
            self.master_fd = master_fd
            self.child_pid = child_pid
            self._running = True

            # Set the PTY to non-blocking
            flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
            fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            _logger.info(
                'PTY spawned: pid=%d, shell=%s, dir=%s, %dx%d',
                child_pid, self.shell, self.working_dir, self.cols, self.rows,
            )

        return child_pid

    async def read(self) -> bytes:
        """Read output from the PTY. Returns empty bytes on EOF or no data."""
        if self.master_fd is None:
            return b''

        loop = asyncio.get_event_loop()

        try:
            data = await loop.run_in_executor(None, self._blocking_read)
            return data
        except OSError:
            return b''

    def _blocking_read(self) -> bytes:
        """Blocking read from master fd (run in executor)."""
        if self.master_fd is None:
            return b''
        try:
            return os.read(self.master_fd, _READ_BUFFER_SIZE)
        except OSError:
            return b''

    async def write(self, data: bytes) -> None:
        """Write input to the PTY."""
        if self.master_fd is None:
            return

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self._blocking_write, data)
        except OSError as e:
            _logger.warning('PTY write failed: %s', e)

    def _blocking_write(self, data: bytes) -> None:
        """Blocking write to master fd (run in executor)."""
        if self.master_fd is not None:
            os.write(self.master_fd, data)

    def resize(self, cols: int, rows: int) -> None:
        """Resize the PTY window. Sends SIGWINCH to the child process."""
        self.cols = cols
        self.rows = rows
        if self.master_fd is not None:
            winsize = struct.pack('HHHH', rows, cols, 0, 0)
            try:
                fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
                # Send SIGWINCH to child
                if self.child_pid:
                    os.kill(self.child_pid, signal.SIGWINCH)
                _logger.debug('PTY resized to %dx%d', cols, rows)
            except OSError as e:
                _logger.warning('PTY resize failed: %s', e)

    def is_alive(self) -> bool:
        """Check if the child process is still running."""
        if self.child_pid is None:
            return False
        try:
            pid, status = os.waitpid(self.child_pid, os.WNOHANG)
            if pid == 0:
                return True
            # Process has exited
            self._running = False
            return False
        except ChildProcessError:
            self._running = False
            return False

    def close(self) -> None:
        """Close the PTY and clean up resources."""
        self._running = False
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.master_fd = None
        if self.child_pid is not None:
            try:
                os.kill(self.child_pid, signal.SIGTERM)
            except (OSError, ProcessLookupError):
                pass
            try:
                os.waitpid(self.child_pid, 0)
            except ChildProcessError:
                pass
            self.child_pid = None
            _logger.info('PTY process cleaned up')

    @property
    def is_running(self) -> bool:
        return self._running and self.is_alive()
