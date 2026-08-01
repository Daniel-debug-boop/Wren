"""
Unit tests for the Wren backend (wren/server.py).

Run with:
    cd wren && pip install -r requirements.txt
    poetry run pytest tests/unit/test_server.py -v
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# ── Path & env setup BEFORE importing the server ──────────────────────
TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

_TMP_DB = Path(tempfile.mkdtemp()) / 'test_wren.db'
os.environ['WREN_DB_PATH'] = str(_TMP_DB)
# Workspace rooted in a temp dir so file tests never touch the repo
_TMP_WORKSPACE = Path(tempfile.mkdtemp())
os.environ['WREN_WORKSPACE'] = str(_TMP_WORKSPACE)

from wren import app as server  # noqa: E402


@pytest.fixture(scope='module')
def client():
    """TestClient with lifespan (initialises the SQLite schema)."""
    with TestClient(server.app) as c:
        yield c


@pytest.fixture(autouse=True)
def _reset_state():
    """Isolate tests: wipe in-memory state between tests."""
    server.conversations = {}
    server.app_settings = server.Settings()
    # Fresh workspace files per test
    for f in _TMP_WORKSPACE.iterdir():
        if f.is_file():
            f.unlink()
    yield


# ── Health ────────────────────────────────────────────────────────────


def test_health_check(client):
    res = client.get('/api/v1/alive')
    assert res.status_code == 200
    body = res.json()
    assert body['status'] == 'ok'
    assert body['version']


def test_status(client):
    res = client.get('/api/v1/status')
    assert res.status_code == 200
    body = res.json()
    assert body['status'] == 'ok'
    assert body['api_key_set'] is False


# ── Conversations ─────────────────────────────────────────────────────


def test_conversation_crud(client):
    # Create
    res = client.post('/api/v1/conversations', json={'title': 'Build a todo app'})
    assert res.status_code == 200
    conv_id = res.json()['id']
    assert conv_id

    # List
    res = client.get('/api/v1/conversations')
    assert res.status_code == 200
    assert any(c['id'] == conv_id for c in res.json())

    # Get
    res = client.get(f'/api/v1/conversations/{conv_id}')
    assert res.status_code == 200
    assert res.json()['title'] == 'Build a todo app'
    assert res.json()['messages'] == []

    # Delete
    res = client.delete(f'/api/v1/conversations/{conv_id}')
    assert res.status_code == 200
    res = client.get(f'/api/v1/conversations/{conv_id}')
    assert res.status_code == 404


def test_conversation_not_found(client):
    res = client.get('/api/v1/conversations/nope')
    assert res.status_code == 404


# ── Settings ──────────────────────────────────────────────────────────


def test_settings_roundtrip(client):
    res = client.put(
        '/api/v1/settings',
        json={
            'provider': 'openai',
            'model': 'gpt-4o',
            'api_key': 'sk-test-123',
            'temperature': 0.5,
            'max_tokens': 2048,
        },
    )
    assert res.status_code == 200

    res = client.get('/api/v1/settings')
    body = res.json()
    assert body['provider'] == 'openai'
    assert body['model'] == 'gpt-4o'
    assert body['temperature'] == 0.5
    assert body['max_tokens'] == 2048
    assert body['api_key_set'] is True
    # The raw key must NEVER be returned to the browser
    assert 'sk-test-123' not in json.dumps(body)
    assert body['api_key'] == ''


def test_settings_never_wipe_key_with_empty_payload(client):
    client.put(
        '/api/v1/settings',
        json={'provider': 'openai', 'model': 'gpt-4o', 'api_key': 'sk-keep-me'},
    )
    # Empty api_key must not wipe the stored key
    client.put(
        '/api/v1/settings',
        json={'provider': 'openai', 'model': 'gpt-4o', 'api_key': ''},
    )
    res = client.get('/api/v1/settings')
    assert res.json()['api_key_set'] is True


# ── Workspace file API ────────────────────────────────────────────────


def test_workspace_tree(client):
    (_TMP_WORKSPACE / 'hello.txt').write_text('hi', encoding='utf-8')
    (_TMP_WORKSPACE / 'src').mkdir(exist_ok=True)
    (_TMP_WORKSPACE / 'src' / 'app.py').write_text("print('x')", encoding='utf-8')

    res = client.get('/api/v1/workspace/tree')
    assert res.status_code == 200
    body = res.json()
    assert body['tree']['type'] == 'directory'
    names = {c['name'] for c in body['tree']['children']}
    assert 'hello.txt' in names
    assert 'src' in names


def test_workspace_read_write(client):
    res = client.put(
        '/api/v1/workspace/file',
        json={'path': 'new-file.py', 'content': 'x = 42\n'},
    )
    assert res.status_code == 200

    res = client.get('/api/v1/workspace/file', params={'path': 'new-file.py'})
    assert res.status_code == 200
    assert res.json()['content'] == 'x = 42\n'

    # Reading a missing file → 404
    res = client.get('/api/v1/workspace/file', params={'path': 'nope.txt'})
    assert res.status_code == 404


def test_workspace_path_traversal_blocked(client):
    res = client.get(
        '/api/v1/workspace/file',
        params={'path': '../../etc/passwd'},
    )
    assert res.status_code == 400


# ── LLM error handling ────────────────────────────────────────────────


def test_send_message_requires_api_key(client):
    res = client.post('/api/v1/conversations', json={'title': 't'})
    conv_id = res.json()['id']

    res = client.post(
        f'/api/v1/conversations/{conv_id}/messages',
        json={'role': 'user', 'content': 'hello'},
    )
    assert res.status_code == 400
    assert 'API key' in res.json()['detail']


def test_send_message_streams_response(monkeypatch, client):
    res = client.post('/api/v1/conversations', json={'title': 't'})
    conv_id = res.json()['id']

    async def fake_stream(settings, messages):
        yield 'Real '
        yield 'streamed '
        yield 'response'

    monkeypatch.setattr(server, 'stream_llm', fake_stream)

    res = client.post(
        f'/api/v1/conversations/{conv_id}/messages',
        json={'role': 'user', 'content': 'hello'},
    )
    assert res.status_code == 200
    assert res.json()['content'] == 'Real streamed response'

    # Conversation now has user + assistant messages persisted
    res = client.get(f'/api/v1/conversations/{conv_id}')
    roles = [m['role'] for m in res.json()['messages']]
    assert roles == ['user', 'assistant']


# ── Messages list endpoint ───────────────────────────────────────────


def test_conversation_messages_endpoint(client):
    res = client.post('/api/v1/conversations', json={'title': 't'})
    conv_id = res.json()['conversation_id']

    res = client.get(f'/api/v1/conversations/{conv_id}/messages')
    assert res.status_code == 200
    assert res.json() == []

    res = client.get('/api/v1/conversations/missing/messages')
    assert res.status_code == 404


def test_conversation_list_aliases(client):
    res = client.post('/api/v1/conversations', json={'title': 'Alias test'})
    assert res.status_code == 200
    body = res.json()
    assert body['conversation_id'] == body['id']

    res = client.get('/api/v1/conversations')
    conv = next(c for c in res.json() if c['title'] == 'Alias test')
    assert conv['conversation_id'] == conv['id']
    assert conv['status'] == 'stopped'
    assert 'created_at' in conv


# ── Settings POST alias ──────────────────────────────────────────────


def test_settings_post_alias(client):
    res = client.post(
        '/api/v1/settings',
        json={'provider': 'openai', 'model': 'gpt-4o-mini', 'api_key': 'sk-post-alias'},
    )
    assert res.status_code == 200
    res = client.get('/api/v1/settings')
    assert res.json()['model'] == 'gpt-4o-mini'
    assert res.json()['api_key_set'] is True


# ── API Keys ─────────────────────────────────────────────────────────


def test_api_keys_crud(client):
    res = client.get('/api/v1/api-keys')
    assert res.status_code == 200
    assert res.json() == []

    res = client.post('/api/v1/api-keys', json={'name': 'CI Key'})
    assert res.status_code == 200
    key = res.json()
    assert key['id']
    assert key['key_preview'].startswith('wren_'[:4])
    # The full key is only returned once at creation
    assert key['key'].startswith('wren_')

    res = client.get('/api/v1/api-keys')
    assert len(res.json()) == 1
    listed = res.json()[0]
    assert 'key' not in listed  # never leaks the full key on list

    res = client.delete(f'/api/v1/api-keys/{key["id"]}')
    assert res.status_code == 200
    res = client.delete(f'/api/v1/api-keys/{key["id"]}')
    assert res.status_code == 404


def test_api_key_requires_name(client):
    res = client.post('/api/v1/api-keys', json={'name': '   '})
    assert res.status_code == 400


# ── Skills ───────────────────────────────────────────────────────────


def test_skills_list_and_toggle(client):
    res = client.get('/api/v1/skills')
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    names = {s['name'] for s in res.json()}
    assert 'code-review' in names

    res = client.post('/api/v1/skills/code-review/toggle', json={'enabled': False})
    assert res.status_code == 200
    assert res.json()['enabled'] is False

    res = client.post('/api/v1/skills/does-not-exist/toggle', json={'enabled': True})
    assert res.status_code == 404


# ── Auto-generation pipeline ─────────────────────────────────────────


def test_generation_requires_prompt(client):
    res = client.post('/api/v1/auto-generations', json={'prompt': ''})
    assert res.status_code == 400


def test_generation_pipeline(monkeypatch, client):
    async def fake_join(settings, messages):
        # Return stage-specific content based on the system prompt
        sys_prompt = messages[0].content if messages else ''
        if 'Architect' in sys_prompt:
            return '## Architecture\nReact + FastAPI'
        if 'Planner' in sys_prompt:
            return '## Plan\n1. Scaffold\n2. Build'
        if 'Writer' in sys_prompt:
            return "## Code\n```python\nprint('hi')\n```"
        return '## Review\nLooks solid'

    monkeypatch.setattr(server, 'join_response', fake_join)

    res = client.post('/api/v1/auto-generations', json={'prompt': 'build a todo app'})
    assert res.status_code == 200
    task_id = res.json()['task_id']
    assert task_id

    # Poll until complete (with mocked LLM it's fast)
    import time

    for _ in range(50):
        res = client.get(f'/api/v1/auto-generations/{task_id}/status')
        status = res.json()
        if status['status'] in ('completed', 'error'):
            break
        time.sleep(0.02)

    assert status['status'] == 'completed'
    assert status['progress'] == 100

    res = client.get(f'/api/v1/auto-generations/{task_id}/result')
    result = res.json()
    assert result['success'] is True
    assert 'React + FastAPI' in result['architecture']
    assert "print('hi')" in result['code']
    assert result['review']


def test_generation_error_without_api_key(client):
    # No API key configured → pipeline must surface an honest error
    res = client.post('/api/v1/auto-generations', json={'prompt': 'build something'})
    task_id = res.json()['task_id']

    import time

    for _ in range(50):
        res = client.get(f'/api/v1/auto-generations/{task_id}/status')
        status = res.json()
        if status['status'] in ('completed', 'error'):
            break
        time.sleep(0.02)

    assert status['status'] == 'error'
    assert 'API key' in (status.get('error') or '')

    res = client.get(f'/api/v1/auto-generations/{task_id}/result')
    assert res.json()['success'] is False


def test_generation_not_found(client):
    res = client.get('/api/v1/auto-generations/nope/status')
    assert res.status_code == 404


# ── WebSocket ─────────────────────────────────────────────────────────


def test_websocket_streams_deltas():
    import asyncio

    async def fake_stream(settings, messages):
        yield 'delta-1'
        yield 'delta-2'

    server.stream_llm = fake_stream

    async def run():
        from starlette.testclient import TestClient as StarletteClient

        with StarletteClient(server.app) as c:
            with c.websocket_connect('/ws') as ws:
                ws.send_json({'type': 'auth', 'payload': {'apiKey': 'sk-test'}})
                status = ws.receive_json()
                assert status['type'] == 'status'

                ws.send_json(
                    {
                        'type': 'message',
                        'payload': {
                            'content': 'build a thing',
                            'conversationId': 'conv-ws',
                        },
                    }
                )
                messages = []
                while True:
                    msg = ws.receive_json()
                    messages.append(msg)
                    if (
                        msg['type'] == 'status'
                        and msg['payload']['state'] == 'complete'
                    ):
                        break
                deltas = [
                    m['payload']['content'] for m in messages if m['type'] == 'delta'
                ]
                assert deltas == ['delta-1', 'delta-2']
                final = next(m for m in messages if m['type'] == 'message')
                assert final['payload']['content'] == 'delta-1delta-2'
                assert final['payload']['conversationId'] == 'conv-ws'

    asyncio.run(run())
