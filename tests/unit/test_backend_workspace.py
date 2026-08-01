"""Tests for the real Wren backend (backend/main.py) workspace file API."""

import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# Isolate storage + workspace from the developer's machine
_TMP_HOME = Path(tempfile.mkdtemp())
os.environ['HOME'] = str(_TMP_HOME)
_TMP_WORKSPACE = Path(tempfile.mkdtemp())
os.environ['WREN_WORKSPACE'] = str(_TMP_WORKSPACE)

from backend.main import app  # noqa: E402
from backend.routers import workspace as workspace_router  # noqa: E402


@pytest.fixture(scope='module')
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _fresh_workspace():
    for f in _TMP_WORKSPACE.iterdir():
        if f.is_file():
            f.unlink()
    yield


def test_health(client):
    res = client.get('/api/v1/alive')
    assert res.status_code == 200
    assert res.json()['status'] == 'ok'


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

    res = client.get('/api/v1/workspace/file', params={'path': 'nope.txt'})
    assert res.status_code == 404


def test_workspace_traversal_blocked(client):
    res = client.get(
        '/api/v1/workspace/file',
        params={'path': '../../etc/passwd'},
    )
    assert res.status_code == 400


def test_workspace_root_env_respected():
    assert workspace_router.WORKSPACE_ROOT == _TMP_WORKSPACE
