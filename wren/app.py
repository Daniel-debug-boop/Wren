"""
Wren AI Backend Server
FastAPI application with REST API, WebSocket streaming, real LLM provider
calls (OpenAI-compatible + Anthropic), SQLite persistence, a workspace
file API, API key management, and a multi-agent auto-generation pipeline.
"""

import asyncio
import json
import os
import sqlite3
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Optional

import httpx
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Configuration ────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv('WREN_DB_PATH', BASE_DIR / 'data' / 'wren.db'))
WORKSPACE_ROOT = Path(os.getenv('WREN_WORKSPACE', BASE_DIR.parent)).resolve()
SKILLS_DIR = BASE_DIR.parent / 'skills'

SYSTEM_PROMPT = (
    'You are Wren, a premium AI engineering agent. You help users build '
    'production-ready software: web apps, games, 3D experiences, backend '
    'services. Be precise, write clean code, and explain your decisions '
    'briefly. Respond in markdown with code blocks where relevant.'
)

PIPELINE_STAGE_PROMPTS = {
    'architect': (
        'You are the Architect agent in a software generation pipeline. '
        "Design a complete system architecture for the user's request. "
        'Cover: tech stack, component hierarchy, data models, API contracts, '
        'and file layout. Be concrete and concise (max 400 words).'
    ),
    'planner': (
        'You are the Planner agent. Based on the architecture, produce a '
        'step-by-step implementation plan: ordered tasks, dependencies, '
        'and which files to create or edit. Be concrete (max 400 words).'
    ),
    'writer': (
        'You are the Writer agent. Write the complete, production-ready '
        'implementation following the plan. Include all source files as '
        'markdown code blocks with filenames. Make the code complete and runnable.'
    ),
    'reviewer': (
        'You are the Reviewer agent. Review the generated code for bugs, '
        'security issues, edge cases, and best practices. List concrete '
        'improvements (max 300 words).'
    ),
}


class LLMError(Exception):
    """Raised when the LLM provider call fails."""


# ── Models ───────────────────────────────────────────────────────────


class Message(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str


class Conversation(BaseModel):
    id: Optional[str] = None
    title: str = 'New Conversation'
    messages: list[Message] = []


class Settings(BaseModel):
    api_key: Optional[str] = None
    model: str = 'gpt-4o'
    base_url: Optional[str] = None
    provider: str = 'openai'
    temperature: float = 0.7
    max_tokens: int = 4096
    theme: str = 'dark'
    font_size: int = 14
    tab_size: int = 2
    word_wrap: bool = True


class StatusResponse(BaseModel):
    status: str
    version: str
    uptime: float


class SendMessageRequest(BaseModel):
    content: str


class FileWriteRequest(BaseModel):
    path: str
    content: str


class ApiKeyCreate(BaseModel):
    name: str


class GenerationRequest(BaseModel):
    prompt: str
    model: Optional[str] = None


class SkillToggle(BaseModel):
    enabled: bool


# ── Database (SQLite) ────────────────────────────────────────────────


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                actions TEXT,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                key TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS skills (
                name TEXT PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 1
            );
            """
        )


def _row_to_conversation(row: sqlite3.Row) -> dict:
    return {
        'id': row['id'],
        'title': row['title'],
        'created_at': row['created_at'],
        'updated_at': row['updated_at'],
    }


def load_conversations() -> dict[str, dict]:
    with get_db() as conn:
        rows = conn.execute(
            'SELECT * FROM conversations ORDER BY updated_at DESC'
        ).fetchall()
        return {r['id']: _row_to_conversation(r) for r in rows}


def load_messages(conversation_id: str) -> list[Message]:
    with get_db() as conn:
        rows = conn.execute(
            'SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC',
            (conversation_id,),
        ).fetchall()
        return [Message(role=r['role'], content=r['content']) for r in rows]


def load_messages_full(conversation_id: str) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            'SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC',
            (conversation_id,),
        ).fetchall()
        return [
            {
                'id': r['id'],
                'role': r['role'],
                'content': r['content'],
                'actions': json.loads(r['actions']) if r['actions'] else [],
                'timestamp': datetime.fromtimestamp(r['created_at']).isoformat(),
            }
            for r in rows
        ]


def persist_conversation(conv_id: str, title: str) -> None:
    now = datetime.now().timestamp()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO conversations (id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                updated_at = excluded.updated_at
            """,
            (conv_id, title, now, now),
        )


def persist_message(
    conv_id: str, role: str, content: str, actions: Optional[list] = None
) -> str:
    msg_id = str(uuid.uuid4())
    now = datetime.now().timestamp()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO messages (id, conversation_id, role, content, actions, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (msg_id, conv_id, role, content, json.dumps(actions or []), now),
        )
        conn.execute(
            'UPDATE conversations SET updated_at = ? WHERE id = ?',
            (now, conv_id),
        )
    return msg_id


def delete_conversation_row(conv_id: str) -> None:
    with get_db() as conn:
        conn.execute('DELETE FROM messages WHERE conversation_id = ?', (conv_id,))
        conn.execute('DELETE FROM conversations WHERE id = ?', (conv_id,))


def load_settings() -> dict:
    with get_db() as conn:
        rows = conn.execute('SELECT key, value FROM settings').fetchall()
        return {r['key']: json.loads(r['value']) for r in rows}


def save_settings(settings: Settings) -> None:
    with get_db() as conn:
        for key, value in settings.model_dump().items():
            conn.execute(
                """
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, json.dumps(value)),
            )


def load_api_keys() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            'SELECT * FROM api_keys ORDER BY created_at DESC'
        ).fetchall()
        return [
            {
                'id': r['id'],
                'name': r['name'],
                'key_preview': r['key'][:8] + '…',
                'created_at': datetime.fromtimestamp(r['created_at']).isoformat(),
            }
            for r in rows
        ]


def delete_api_key_row(key_id: str) -> bool:
    with get_db() as conn:
        cur = conn.execute('DELETE FROM api_keys WHERE id = ?', (key_id,))
        return cur.rowcount > 0


def load_skill_enabled(name: str) -> bool:
    with get_db() as conn:
        row = conn.execute(
            'SELECT enabled FROM skills WHERE name = ?', (name,)
        ).fetchone()
        return bool(row['enabled']) if row else True


def save_skill_enabled(name: str, enabled: bool) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO skills (name, enabled) VALUES (?, ?)
            ON CONFLICT(name) DO UPDATE SET enabled = excluded.enabled
            """,
            (name, int(enabled)),
        )


# ── LLM Provider Layer ───────────────────────────────────────────────


def _normalise_model(provider: str, model: str) -> str:
    """Strip provider prefixes for providers that don't want them."""
    if provider == 'anthropic' and model.startswith('anthropic/'):
        return model.split('/', 1)[1]
    if provider == 'openai' and model.startswith('openai/'):
        return model.split('/', 1)[1]
    return model


async def _stream_openai_compatible(
    settings: Settings, messages: list[Message]
) -> AsyncIterator[str]:
    base = (settings.base_url or 'https://api.openai.com/v1').rstrip('/')
    url = f'{base}/chat/completions'
    headers = {
        'Authorization': f'Bearer {settings.api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': _normalise_model(settings.provider, settings.model),
        'messages': [m.model_dump() for m in messages],
        'temperature': settings.temperature,
        'max_tokens': settings.max_tokens,
        'stream': True,
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=15.0)) as client:
        try:
            async with client.stream(
                'POST', url, json=payload, headers=headers
            ) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise LLMError(
                        f'Provider returned HTTP {resp.status_code}: '
                        f'{body[:300].decode(errors="replace")}'
                    )
                async for line in resp.aiter_lines():
                    if not line.startswith('data:'):
                        continue
                    data = line[5:].strip()
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk['choices'][0]['delta'].get('content', '')
                        if delta:
                            yield delta
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
        except httpx.HTTPError as exc:
            raise LLMError(f'Connection to provider failed: {exc}') from exc


async def _stream_anthropic(
    settings: Settings, messages: list[Message]
) -> AsyncIterator[str]:
    base = (settings.base_url or 'https://api.anthropic.com').rstrip('/')
    url = f'{base}/v1/messages'
    headers = {
        'x-api-key': settings.api_key or '',
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': _normalise_model(settings.provider, settings.model),
        'max_tokens': settings.max_tokens,
        'temperature': settings.temperature,
        'stream': True,
        'messages': [
            {'role': m.role, 'content': m.content}
            for m in messages
            if m.role in ('user', 'assistant')
        ],
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=15.0)) as client:
        try:
            async with client.stream(
                'POST', url, json=payload, headers=headers
            ) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise LLMError(
                        f'Anthropic returned HTTP {resp.status_code}: '
                        f'{body[:300].decode(errors="replace")}'
                    )
                async for line in resp.aiter_lines():
                    if not line.startswith('data:'):
                        continue
                    try:
                        event = json.loads(line[5:].strip())
                        if event.get('type') == 'content_block_delta':
                            delta = event.get('delta', {}).get('text', '')
                            if delta:
                                yield delta
                    except json.JSONDecodeError:
                        continue
        except httpx.HTTPError as exc:
            raise LLMError(f'Connection to Anthropic failed: {exc}') from exc


def _build_messages(conversation_id: str, user_content: str) -> list[Message]:
    history = load_messages(conversation_id)
    # Trim to last 20 messages to bound context
    history = history[-20:]
    return [
        Message(role='system', content=SYSTEM_PROMPT),
        *history,
        Message(role='user', content=user_content),
    ]


async def stream_llm(settings: Settings, messages: list[Message]) -> AsyncIterator[str]:
    """Stream a real LLM response as text deltas."""
    if not settings.api_key:
        raise LLMError(
            'No API key configured. Open Settings → LLM Configuration and '
            'add your API key (OpenAI, Anthropic, or OpenRouter).'
        )
    if settings.provider == 'anthropic':
        async for delta in _stream_anthropic(settings, messages):
            yield delta
    else:
        async for delta in _stream_openai_compatible(settings, messages):
            yield delta


async def join_response(settings: Settings, messages: list[Message]) -> str:
    parts = [part async for part in stream_llm(settings, messages)]
    return ''.join(parts)


async def generate_response(
    settings: Settings, conversation_id: str, user_content: str
) -> str:
    messages = _build_messages(conversation_id, user_content)
    return await join_response(settings, messages)


# ── Workspace File API helpers ───────────────────────────────────────


def _safe_path(relative: str) -> Path:
    """Resolve a workspace-relative path, guarding against traversal."""
    target = (WORKSPACE_ROOT / relative).resolve()
    if not str(target).startswith(str(WORKSPACE_ROOT)):
        raise HTTPException(status_code=400, detail='Path escapes workspace root')
    return target


def _build_tree(path: Path, depth: int = 0, max_depth: int = 5) -> Optional[dict]:
    if depth > max_depth:
        return None
    if path.is_file():
        return {
            'name': path.name,
            'path': str(path.relative_to(WORKSPACE_ROOT)),
            'type': 'file',
        }
    if path.is_dir():
        children = []
        for entry in sorted(
            path.iterdir(), key=lambda e: (e.is_file(), e.name.lower())
        ):
            if entry.name in (
                '.git',
                'node_modules',
                'build',
                'dist',
                '__pycache__',
                '.react-router',
                '.gradle',
                '.kotlin',
                '.venv',
                'venv',
                '.next',
                '.parcel-cache',
                '.wren',
                'coverage',
                '.husky',
                '.pytest_cache',
                '.mypy_cache',
                '.ruff_cache',
                '.gitignore',
            ):
                continue
            if entry.name.startswith('.') and entry.is_file():
                continue
            child = _build_tree(entry, depth + 1, max_depth)
            if child is not None:
                children.append(child)
        return {
            'name': path.name or WORKSPACE_ROOT.name,
            'path': str(path.relative_to(WORKSPACE_ROOT)),
            'type': 'directory',
            'children': children,
        }
    return None


# ── App State ────────────────────────────────────────────────────────

conversations: dict[str, dict] = {}
app_settings = Settings()
start_time = datetime.now()
active_connections: set[WebSocket] = set()
generation_tasks: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    global conversations, app_settings
    conversations = load_conversations()
    stored = load_settings()
    if stored:
        app_settings = Settings(**stored)
    print(f'[Wren] Backend started | db={DB_PATH} | workspace={WORKSPACE_ROOT}')
    print(
        f'[Wren] LLM provider={app_settings.provider} model={app_settings.model} '
        f'key={"set" if app_settings.api_key else "NOT SET"}'
    )
    yield
    print('[Wren] Backend shutting down')


app = FastAPI(
    title='Wren AI API',
    version='1.2.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# ── REST Endpoints ───────────────────────────────────────────────────


@app.get('/api/v1/alive')
async def health_check():
    uptime = (datetime.now() - start_time).total_seconds()
    return StatusResponse(status='ok', version='1.2.0', uptime=uptime)


@app.get('/api/v1/status')
async def status():
    return {
        'status': 'ok',
        'version': '1.2.0',
        'uptime': (datetime.now() - start_time).total_seconds(),
        'conversations': len(conversations),
        'settings_provider': app_settings.provider,
        'api_key_set': bool(app_settings.api_key),
    }


# ── Conversations ────────────────────────────────────────────────────


@app.get('/api/v1/conversations')
async def list_conversations():
    return [
        {
            'id': cid,
            'conversation_id': cid,
            'title': conv['title'],
            'message_count': len(load_messages(cid)),
            'created_at': datetime.fromtimestamp(conv['created_at']).isoformat(),
            'updated_at': datetime.fromtimestamp(conv['updated_at']).isoformat(),
            'status': 'stopped',
        }
        for cid, conv in sorted(
            conversations.items(), key=lambda x: x[1]['updated_at'], reverse=True
        )
    ]


@app.post('/api/v1/conversations')
async def create_conversation(conv: Optional[Conversation] = None):
    conv_id = str(uuid.uuid4())
    title = conv.title if conv and conv.title else 'New Conversation'
    persist_conversation(conv_id, title)
    conversations[conv_id] = load_conversations()[conv_id]
    return {
        'id': conv_id,
        'conversation_id': conv_id,
        'title': title,
        'status': 'stopped',
        'created_at': datetime.now().isoformat(),
    }


@app.get('/api/v1/conversations/{conv_id}')
async def get_conversation(conv_id: str):
    conv = conversations.get(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail='Conversation not found')
    return {
        'id': conv['id'],
        'conversation_id': conv['id'],
        'title': conv['title'],
        'messages': [m.model_dump() for m in load_messages(conv_id)],
    }


@app.get('/api/v1/conversations/{conv_id}/messages')
async def list_conversation_messages(conv_id: str):
    if conv_id not in conversations:
        raise HTTPException(status_code=404, detail='Conversation not found')
    return load_messages_full(conv_id)


@app.delete('/api/v1/conversations/{conv_id}')
async def delete_conversation(conv_id: str):
    if conv_id not in conversations:
        raise HTTPException(status_code=404, detail='Conversation not found')
    delete_conversation_row(conv_id)
    conversations.pop(conv_id, None)
    return {'status': 'deleted'}


@app.post('/api/v1/conversations/{conv_id}/messages')
async def send_message(conv_id: str, msg: SendMessageRequest):
    if conv_id not in conversations:
        raise HTTPException(status_code=404, detail='Conversation not found')
    persist_message(conv_id, 'user', msg.content)
    try:
        response_content = await generate_response(app_settings, conv_id, msg.content)
    except LLMError as exc:
        persist_message(
            conv_id,
            'system',
            f'⚠️ {exc}',
            [
                {
                    'type': 'error',
                    'thought': 'LLM call failed',
                    'timestamp': datetime.now().timestamp(),
                }
            ],
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    actions = [
        {
            'type': 'think',
            'thought': 'Analyzed requirements and generated a response',
            'timestamp': datetime.now().timestamp(),
        },
    ]
    persist_message(conv_id, 'assistant', response_content, actions)
    return {
        'id': str(uuid.uuid4()),
        'role': 'assistant',
        'content': response_content,
        'actions': actions,
        'timestamp': datetime.now().isoformat(),
    }


# ── Settings ─────────────────────────────────────────────────────────


@app.get('/api/v1/settings')
async def get_settings():
    data = app_settings.model_dump()
    data['api_key_set'] = bool(app_settings.api_key)
    data['api_key'] = ''  # never return the raw key
    return data


@app.put('/api/v1/settings')
async def update_settings(settings: Settings):
    global app_settings
    incoming = settings.model_dump()
    # Never overwrite a real key with an empty/masked placeholder
    if not incoming.get('api_key'):
        incoming['api_key'] = app_settings.api_key
    app_settings = Settings(**incoming)
    save_settings(app_settings)
    return {'status': 'updated', 'provider': settings.provider, 'model': settings.model}


@app.post('/api/v1/settings')
async def update_settings_post(settings: Settings):
    """POST alias (some clients use POST instead of PUT)."""
    return await update_settings(settings)


@app.get('/api/v1/models')
async def list_models():
    return {
        'providers': {
            'openai': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
            'anthropic': ['claude-sonnet-4-20250514', 'claude-3-5-sonnet-20241022'],
            'openrouter': [
                'openrouter/auto',
                'openai/gpt-4o',
                'anthropic/claude-sonnet-4',
            ],
            'google': ['gemini-2.0-flash', 'gemini-1.5-pro'],
            'groq': ['llama-3.3-70b-versatile'],
            'mistral': ['mistral-large-latest'],
        }
    }


# ── API Keys ─────────────────────────────────────────────────────────


@app.get('/api/v1/api-keys')
async def list_api_keys():
    return load_api_keys()


@app.post('/api/v1/api-keys')
async def create_api_key(req: ApiKeyCreate):
    if not req.name.strip():
        raise HTTPException(status_code=400, detail='Key name is required')
    key_id = str(uuid.uuid4())
    key_value = f'wren_{uuid.uuid4().hex}{uuid.uuid4().hex}'
    now = datetime.now().timestamp()
    with get_db() as conn:
        conn.execute(
            'INSERT INTO api_keys (id, name, key, created_at) VALUES (?, ?, ?, ?)',
            (key_id, req.name.strip(), key_value, now),
        )
    return {
        'id': key_id,
        'name': req.name.strip(),
        'key': key_value,
        'key_preview': key_value[:8] + '…',
        'created_at': datetime.fromtimestamp(now).isoformat(),
    }


@app.delete('/api/v1/api-keys/{key_id}')
async def delete_api_key(key_id: str):
    if not delete_api_key_row(key_id):
        raise HTTPException(status_code=404, detail='API key not found')
    return {'status': 'deleted'}


# ── Skills ───────────────────────────────────────────────────────────


def _skill_description(path: Path) -> str:
    try:
        text = path.read_text(encoding='utf-8', errors='replace')
        # First non-empty line after optional frontmatter
        lines = text.splitlines()
        start = 0
        if lines and lines[0].strip() == '---':
            for i, line in enumerate(lines[1:], start=1):
                if line.strip() == '---':
                    start = i + 1
                    break
        for line in lines[start:]:
            line = line.strip()
            if line and not line.startswith('#'):
                return line[:140]
        return ''
    except Exception:
        return ''


@app.get('/api/v1/skills')
async def list_skills():
    items = []
    if SKILLS_DIR.is_dir():
        for f in sorted(SKILLS_DIR.glob('*.md')):
            name = f.stem
            items.append(
                {
                    'name': name,
                    'description': _skill_description(f),
                    'enabled': load_skill_enabled(name),
                }
            )
    return items


@app.post('/api/v1/skills/{name}/toggle')
async def toggle_skill(name: str, req: SkillToggle):
    if not (SKILLS_DIR / f'{name}.md').is_file():
        raise HTTPException(status_code=404, detail='Skill not found')
    save_skill_enabled(name, req.enabled)
    return {'name': name, 'enabled': req.enabled}


# ── Workspace File API ───────────────────────────────────────────────


@app.get('/api/v1/workspace/tree')
async def workspace_tree():
    tree = _build_tree(WORKSPACE_ROOT)
    return {'root': WORKSPACE_ROOT.name, 'tree': tree}


@app.get('/api/v1/workspace/file')
async def workspace_read(path: str):
    target = _safe_path(path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail=f'File not found: {path}')
    try:
        content = target.read_text(encoding='utf-8', errors='replace')
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f'Failed to read file: {exc}'
        ) from exc
    return {'path': path, 'content': content}


@app.put('/api/v1/workspace/file')
async def workspace_write(req: FileWriteRequest):
    target = _safe_path(req.path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text(req.content, encoding='utf-8')
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f'Failed to write file: {exc}'
        ) from exc
    return {'status': 'saved', 'path': req.path}


# ── Auto-Generation Pipeline ─────────────────────────────────────────


async def _run_generation(task_id: str, prompt: str) -> None:
    task = generation_tasks[task_id]
    outputs: dict[str, str] = {}
    stage_keys = ['architect', 'planner', 'writer', 'reviewer']
    try:
        for i, stage in enumerate(stage_keys):
            task.update(
                {
                    'status': 'running',
                    'stage': stage,
                    'progress': int((i / len(stage_keys)) * 100),
                    'message': f'{stage.capitalize()} agent working…',
                }
            )
            messages = [
                Message(role='system', content=PIPELINE_STAGE_PROMPTS[stage]),
                Message(role='user', content=prompt),
            ]
            outputs[stage] = await join_response(app_settings, messages)
        task.update(
            {
                'status': 'completed',
                'stage': 'complete',
                'progress': 100,
                'message': 'Generation complete',
                'result': outputs,
            }
        )
    except LLMError as exc:
        task.update({'status': 'error', 'error': str(exc)})
    except Exception as exc:  # pragma: no cover
        task.update({'status': 'error', 'error': f'Unexpected error: {exc}'})


@app.post('/api/v1/auto-generations')
async def start_generation(req: GenerationRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail='Prompt is required')
    task_id = str(uuid.uuid4())
    generation_tasks[task_id] = {
        'status': 'queued',
        'stage': None,
        'progress': 0,
        'message': 'Queued',
        'error': None,
        'result': None,
    }
    asyncio.create_task(_run_generation(task_id, req.prompt.strip()))
    return {'task_id': task_id}


@app.get('/api/v1/auto-generations/{task_id}/status')
async def generation_status(task_id: str):
    task = generation_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Generation task not found')
    return {
        'task_id': task_id,
        'status': task['status'],
        'stage': task.get('stage'),
        'progress': task.get('progress', 0),
        'message': task.get('message', ''),
        'error': task.get('error'),
    }


@app.get('/api/v1/auto-generations/{task_id}/result')
async def generation_result(task_id: str):
    task = generation_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Generation task not found')
    if task['status'] == 'error':
        return {'success': False, 'error': task.get('error') or 'Generation failed'}
    result = task.get('result') or {}
    return {
        'success': True,
        'architecture': result.get('architect', ''),
        'plan': result.get('planner', ''),
        'code': result.get('writer', ''),
        'review': result.get('reviewer', ''),
    }


# ── WebSocket ────────────────────────────────────────────────────────


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get('type') == 'auth':
                api_key = msg.get('payload', {}).get('apiKey', '')
                if api_key and api_key != app_settings.api_key:
                    app_settings.api_key = api_key
                    save_settings(app_settings)
                await websocket.send_json(
                    {
                        'type': 'status',
                        'payload': {
                            'state': 'idle',
                            'thought': 'Connected. '
                            + (
                                'Ready to build with a real model.'
                                if app_settings.api_key
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

                # Get or create conversation
                if conv_id and conv_id not in conversations:
                    persist_conversation(
                        conv_id, content[:48] + ('…' if len(content) > 48 else '')
                    )
                    conversations[conv_id] = load_conversations()[conv_id]
                if not conv_id:
                    conv_id = str(uuid.uuid4())
                    persist_conversation(
                        conv_id, content[:48] + ('…' if len(content) > 48 else '')
                    )
                    conversations[conv_id] = load_conversations()[conv_id]

                persist_message(conv_id, 'user', content)

                await websocket.send_json(
                    {
                        'type': 'status',
                        'payload': {
                            'state': 'thinking',
                            'thought': 'Analyzing your request…',
                        },
                    }
                )

                messages = _build_messages(conv_id, content)
                full = ''
                try:
                    async for delta in stream_llm(app_settings, messages):
                        full += delta
                        await websocket.send_json(
                            {'type': 'delta', 'payload': {'content': delta}}
                        )
                except LLMError as exc:
                    await websocket.send_json(
                        {
                            'type': 'error',
                            'payload': {'message': str(exc)},
                        }
                    )
                    persist_message(
                        conv_id,
                        'system',
                        f'⚠️ {exc}',
                        [
                            {
                                'type': 'error',
                                'thought': 'LLM call failed',
                                'timestamp': datetime.now().timestamp(),
                            }
                        ],
                    )
                    await websocket.send_json(
                        {
                            'type': 'status',
                            'payload': {'state': 'error', 'thought': str(exc)[:120]},
                        }
                    )
                    continue

                if not full.strip():
                    full = 'I received your message but produced no output. Try rephrasing or check the model settings.'

                actions = [
                    {
                        'type': 'think',
                        'thought': 'Analyzed requirements and generated a response',
                        'timestamp': datetime.now().timestamp(),
                    },
                ]
                persist_message(conv_id, 'assistant', full, actions)

                await websocket.send_json(
                    {
                        'type': 'message',
                        'payload': {
                            'content': full,
                            'actions': actions,
                            'conversationId': conv_id,
                        },
                    }
                )
                await websocket.send_json(
                    {
                        'type': 'status',
                        'payload': {'state': 'complete'},
                    }
                )

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        print(f'[Wren] WebSocket error: {exc}')
        try:
            await websocket.send_json(
                {'type': 'error', 'payload': {'message': str(exc)}}
            )
        except Exception:
            pass
    finally:
        active_connections.discard(websocket)


# ── Main ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import uvicorn

    host = os.getenv('BACKEND_HOST', '0.0.0.0')
    port = int(os.getenv('BACKEND_PORT', '3000'))

    print(f'[Wren] Starting server on {host}:{port}')
    uvicorn.run('wren.app:app', host=host, port=port, reload=True)
