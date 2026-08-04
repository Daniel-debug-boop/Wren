"""Wren Backend - Production FastAPI Server.

Serves all API endpoints that the frontend needs.
Start with: uvicorn backend.main:app --host 0.0.0.0 --port 3000
"""

from __future__ import annotations

import json
import logging
import os

import httpx
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.routers import (
    api_keys,
    auth,
    conversations,
    generation,
    health,
    secrets,
    settings,
    skills,
    terminal,
    terminal_ws,
    git,
    users,
    workspace,
)
from backend.services.llm_service import LLMService
from backend.services.storage import Storage
from backend.services.terminal_service import exec_command

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
_logger = logging.getLogger('wren-backend')

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title='Wren AI Backend',
    description='Production backend for Wren AI - code generation, conversations, and LLM management',
    version='1.0.0',
    docs_url='/docs' if os.getenv('ENABLE_DOCS', 'false').lower() in ('true', '1') else None,
    redoc_url='/redoc' if os.getenv('ENABLE_DOCS', 'false').lower() in ('true', '1') else None,
)

# -- CORS --
# In production, restrict CORS to your frontend domain via WREN_CORS_ORIGINS
_cors_origins_raw = os.getenv('WREN_CORS_ORIGINS', '')
if _cors_origins_raw:
    _cors_origins = [o.strip() for o in _cors_origins_raw.split(',') if o.strip()]
else:
    _cors_origins = ['*']  # Default open for development

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# -- Global Error Handler --
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    _logger.exception('Unhandled exception: %s', exc)
    # Never expose internal error details to the client
    status_code = getattr(exc, 'status_code', 500)
    if status_code < 400 or status_code >= 600:
        status_code = 500
    return JSONResponse(
        status_code=status_code,
        content={'detail': 'Internal server error'},
    )


# ── Include Routers ──────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(settings.router)
app.include_router(secrets.router)
app.include_router(conversations.router)
app.include_router(generation.router)
app.include_router(auth.router)
app.include_router(api_keys.router)
app.include_router(skills.router)
app.include_router(terminal.router)
app.include_router(terminal_ws.router)
app.include_router(git.router)
app.include_router(users.router)
app.include_router(workspace.router)


# ── Startup Event ────────────────────────────────────────────────────────────
@app.on_event('startup')
async def startup():
    _logger.info('Wren backend starting on port %s', os.environ.get('PORT', '3000'))


# ── Direct Run ───────────────────────────────────────────────────────────────
# ── WebSocket: real-time agent chat streaming ────────────────────────────

SYSTEM_PROMPT = (
    'You are Wren, a premium AI engineering agent. Help users build '
    'production-ready software: web apps, games, 3D experiences, backend '
    'services. Be precise, write clean code, and explain decisions briefly. '
    'Respond in markdown with code blocks where relevant.'
)


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    """Stream real LLM token deltas to the workspace chat.

    Supports commands:
      auth        - authenticate with API key
      message     - send a chat message
      exec        - execute a terminal command
      run         - run a code snippet
    """
    await websocket.accept()
    storage_ws = Storage.get_instance()
    ws_workspace_root = os.getenv('WORKSPACE_BASE', './workspace')
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get('type') == 'auth':
                api_key = msg.get('payload', {}).get('apiKey', '')
                if api_key:
                    storage_ws.set_secret('api_key', api_key)
                await websocket.send_json(
                    {
                        'type': 'status',
                        'payload': {
                            'state': 'idle',
                            'thought': 'Connected. '
                            + (
                                'Ready to build with a real model.'
                                if api_key
                                else 'Add an API key in Settings for real AI responses.'
                            ),
                        },
                    }
                )

            elif msg.get('type') == 'message':
                payload = msg.get('payload', {})
                content = payload.get('content', '')
                conv_id = payload.get('conversationId')

                if not content.strip():
                    continue

                # Ensure a conversation exists
                if not conv_id:
                    conv_id = storage_ws.create_conversation(
                        content[:48] + ('…' if len(content) > 48 else '')
                    )['conversation_id']

                storage_ws.add_message(conv_id, 'user', content)

                await websocket.send_json(
                    {
                        'type': 'status',
                        'payload': {
                            'state': 'thinking',
                            'thought': 'Analyzing your request…',
                        },
                    }
                )

                # Build history from storage
                history = storage_ws.get_messages(conv_id)[-20:]
                settings_data = storage_ws.get_settings()
                secrets_data = storage_ws.get_secrets()
                llm_config = settings_data.get('llm_config', {})
                api_key = secrets_data.get('api_key', '') or secrets_data.get(
                    'OPENROUTER_API_KEY', ''
                )
                model = llm_config.get('model', 'openai/gpt-4o-mini')
                base_url = llm_config.get('base_url') or 'https://openrouter.ai/api/v1'
                temperature = llm_config.get('temperature', 0.7)
                max_tokens = llm_config.get('max_tokens', 4096)

                llm = LLMService(api_key=api_key, base_url=base_url)
                if not llm.is_configured():
                    await websocket.send_json(
                        {
                            'type': 'error',
                            'payload': {
                                'message': 'No API key configured. Open Settings → LLM Configuration and add your API key.'
                            },
                        }
                    )
                    await websocket.send_json(
                        {
                            'type': 'status',
                            'payload': {
                                'state': 'error',
                                'thought': 'No API key configured',
                            },
                        }
                    )
                    continue

                messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
                for m in history:
                    messages.append({'role': m['role'], 'content': m['content']})

                full = ''
                try:
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        resp = await client.post(
                            f'{llm.base_url}/chat/completions',
                            headers=llm._headers,
                            json={
                                'model': model,
                                'messages': messages,
                                'temperature': temperature,
                                'max_tokens': max_tokens,
                                'stream': True,
                            },
                        )
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            if line.startswith('data: '):
                                data_str = line[6:].strip()
                                if data_str == '[DONE]':
                                    break
                                try:
                                    chunk = json.loads(data_str)
                                    delta = (
                                        chunk.get('choices', [{}])[0]
                                        .get('delta', {})
                                        .get('content', '')
                                    )
                                    if delta:
                                        full += delta
                                        await websocket.send_json(
                                            {
                                                'type': 'delta',
                                                'payload': {'content': delta},
                                            }
                                        )
                                except json.JSONDecodeError:
                                    continue
                except httpx.HTTPStatusError as e:
                    await websocket.send_json(
                        {
                            'type': 'error',
                            'payload': {
                                'message': f'Provider error {e.response.status_code}'
                            },
                        }
                    )
                    await websocket.send_json(
                        {'type': 'status', 'payload': {'state': 'error'}}
                    )
                    continue
                except httpx.HTTPError as e:
                    await websocket.send_json(
                        {
                            'type': 'error',
                            'payload': {'message': f'Connection error: {e}'},
                        }
                    )
                    await websocket.send_json(
                        {'type': 'status', 'payload': {'state': 'error'}}
                    )
                    continue

                if not full.strip():
                    full = 'I received your message but produced no output. Try rephrasing or check the model settings.'

                storage_ws.add_message(conv_id, 'assistant', full)
                await websocket.send_json(
                    {
                        'type': 'message',
                        'payload': {
                            'content': full,
                            'actions': [
                                {
                                    'type': 'think',
                                    'thought': 'Analyzed requirements and generated a response',
                                    'timestamp': 0,
                                }
                            ],
                            'conversationId': conv_id,
                        },
                    }
                )
                await websocket.send_json(
                    {'type': 'status', 'payload': {'state': 'complete'}}
                )

            elif msg.get('type') == 'exec':
                # Terminal command execution via WebSocket
                exec_payload = msg.get('payload', {})
                command = exec_payload.get('command', '')
                if not command.strip():
                    continue

                await websocket.send_json(
                    {
                        'type': 'action',
                        'payload': {
                            'type': 'running',
                            'thought': f'Running: {command[:60]}',
                        },
                    }
                )

                from backend.services.terminal_service import exec_command

                result = await exec_command(
                    command=command,
                    working_dir=ws_workspace_root,
                    workspace_root=ws_workspace_root,
                    timeout=exec_payload.get('timeout', 30),
                )

                if result.get('stdout'):
                    await websocket.send_json(
                        {
                            'type': 'terminal',
                            'payload': {'line': result['stdout']},
                        }
                    )
                if result.get('stderr'):
                    await websocket.send_json(
                        {
                            'type': 'terminal',
                            'payload': {'line': result['stderr']},
                        }
                    )

                exit_code = result.get('exit_code', -1)
                await websocket.send_json(
                    {
                        'type': 'status',
                        'payload': {
                            'state': 'idle' if exit_code == 0 else 'error',
                            'thought': f'Exit code: {exit_code}',
                        },
                    }
                )

            elif msg.get('type') == 'run':
                # Code execution via WebSocket
                run_payload = msg.get('payload', {})
                language = run_payload.get('language', 'python')
                code = run_payload.get('code', '')
                if not code.strip():
                    continue

                await websocket.send_json(
                    {
                        'type': 'action',
                        'payload': {
                            'type': 'running',
                            'thought': f'Running {language} code...',
                        },
                    }
                )

                from backend.services.terminal_service import run_script

                result = await run_script(
                    language=language,
                    code=code,
                    working_dir=ws_workspace_root,
                    workspace_root=ws_workspace_root,
                )

                if result.get('stdout'):
                    await websocket.send_json(
                        {
                            'type': 'terminal',
                            'payload': {'line': result['stdout']},
                        }
                    )
                if result.get('stderr'):
                    await websocket.send_json(
                        {
                            'type': 'terminal',
                            'payload': {'line': result['stderr']},
                        }
                    )

                exit_code = result.get('exit_code', -1)
                await websocket.send_json(
                    {
                        'type': 'status',
                        'payload': {
                            'state': 'idle' if exit_code == 0 else 'error',
                            'thought': f'Exit code: {exit_code}',
                        },
                    }
                )

            else:
                await websocket.send_json(
                    {
                        'type': 'error',
                        'payload': {
                            'message': f'Unknown message type: {msg.get("type")}'
                        },
                    }
                )

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        _logger.exception(f'WebSocket error: {exc}')
        try:
            await websocket.send_json(
                {'type': 'error', 'payload': {'message': str(exc)}}
            )
        except Exception:
            pass


if __name__ == '__main__':
    import uvicorn

    port = int(os.environ.get('PORT', '3000'))
    uvicorn.run('backend.main:app', host='0.0.0.0', port=port, reload=True)
