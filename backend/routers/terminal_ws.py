"""WebSocket terminal endpoint for real interactive PTY.

Provides a WebSocket endpoint at /ws/terminal that bridges xterm.js
in the frontend to a real PTY process on the backend.

Protocol:
  Client -> Server:
    {"type": "input", "data": "<keystrokes>"}
    {"type": "resize", "cols": 80, "rows": 24}
    {"type": "ping"}

  Server -> Client:
    {"type": "output", "data": "<terminal output>"}
    {"type": "exit", "code": 0}
    {"type": "error", "message": "..."}
    {"type": "pong"}
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.pty_service import PTYProcess

_logger = logging.getLogger(__name__)

router = APIRouter(tags=['terminal-ws'])

# Active terminal sessions keyed by WebSocket id
_sessions: dict[str, PTYProcess] = {}


@router.websocket('/ws/terminal')
async def terminal_websocket(websocket: WebSocket) -> None:
    """Real interactive terminal via WebSocket + PTY.

    Each connection gets its own PTY process running the user's shell.
    Input from the client is written to the PTY, and output from the
    PTY is streamed back to the client.
    """
    await websocket.accept()
    session_id = str(id(websocket))

    # Get workspace root from env
    workspace_root = os.getenv('WORKSPACE_BASE', os.getcwd())

    # Determine shell
    shell = os.getenv('WREN_SHELL', os.environ.get('SHELL', '/bin/bash'))

    # Create PTY process
    pty_proc = PTYProcess(
        working_dir=workspace_root,
        shell=shell,
        cols=80,
        rows=24,
    )

    _sessions[session_id] = pty_proc

    try:
        # Spawn the PTY
        pty_proc.spawn()
        _logger.info('Terminal session started: %s (pid=%s)', session_id, pty_proc.child_pid)

        # Start reading from PTY in background
        reader_task = asyncio.create_task(_read_pty_loop(websocket, pty_proc))

        # Handle incoming messages from client
        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    # Treat raw text as terminal input (for compatibility)
                    await pty_proc.write(raw.encode('utf-8'))
                    continue

                msg_type = msg.get('type', '')

                if msg_type == 'input':
                    data = msg.get('data', '')
                    if data:
                        await pty_proc.write(data.encode('utf-8'))

                elif msg_type == 'resize':
                    cols = msg.get('cols', 80)
                    rows = msg.get('rows', 24)
                    pty_proc.resize(cols, rows)

                elif msg_type == 'ping':
                    await websocket.send_json({'type': 'pong'})

                else:
                    _logger.debug('Unknown terminal message type: %s', msg_type)

        except WebSocketDisconnect:
            _logger.info('Terminal client disconnected: %s', session_id)
        except Exception as e:
            _logger.error('Terminal WebSocket error: %s', e)

        # Cancel reader
        reader_task.cancel()
        try:
            await reader_task
        except asyncio.CancelledError:
            pass

    except Exception as e:
        _logger.exception('Terminal session failed: %s', e)
        try:
            await websocket.send_json({
                'type': 'error',
                'message': f'Terminal error: {e}',
            })
        except Exception:
            pass
    finally:
        # Clean up
        pty_proc.close()
        _sessions.pop(session_id, None)
        _logger.info('Terminal session closed: %s', session_id)
        try:
            await websocket.close()
        except Exception:
            pass


async def _read_pty_loop(websocket: WebSocket, pty_proc: PTYProcess) -> None:
    """Background task that reads PTY output and sends it to the WebSocket."""
    try:
        while pty_proc.is_running:
            data = await pty_proc.read()
            if data:
                try:
                    await websocket.send_json({
                        'type': 'output',
                        'data': data.decode('utf-8', errors='replace'),
                    })
                except Exception:
                    break
            else:
                # No data yet, yield control
                await asyncio.sleep(0.01)

        # PTY process exited
        try:
            exit_code = 0
            if pty_proc.child_pid:
                import os
                try:
                    _, status = os.waitpid(pty_proc.child_pid, os.WNOHANG)
                    exit_code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
                except ChildProcessError:
                    pass
            await websocket.send_json({
                'type': 'exit',
                'code': exit_code,
            })
        except Exception:
            pass

    except asyncio.CancelledError:
        pass
    except Exception as e:
        _logger.error('PTY read loop error: %s', e)
