"""Session-scoped working memory for tracking task state, decisions, and progress.

Persisted as a JSON file so it survives across sub-agent invocations within
the same project session. Each entry has a type, timestamp, and structured
payload for tool-parseable access.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)

WORKING_MEMORY_DIR = '.wren'
WORKING_MEMORY_FILE = 'working_memory.json'


class WorkingMemory:
    """Lightweight session memory for tracking current task context.

    Stores entries tagged by type (decision, progress, todo, reflection)
    with timestamps. Supports append, query by type, and summarization.
    """

    def __init__(self, project_root: str | None = None):
        self._project_root = Path(project_root or os.getcwd()).expanduser()
        self._mem_path = self._project_root / WORKING_MEMORY_DIR / WORKING_MEMORY_FILE
        self._mem_path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[dict[str, Any]] = []
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(
        self,
        entry_type: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        entry = {
            'id': f'mem_{int(time.time() * 1000)}_{len(self._entries)}',
            'type': entry_type,
            'content': content,
            'metadata': metadata or {},
            'timestamp': time.time(),
        }
        self._entries.append(entry)
        self._flush()
        return entry

    def add_decision(self, decision: str, context: str = '') -> dict[str, Any]:
        return self.add('decision', decision, {'context': context})

    def add_progress(self, step: str, status: str, detail: str = '') -> dict[str, Any]:
        return self.add('progress', step, {'status': status, 'detail': detail})

    def add_todo(
        self, task: str, depends_on: list[str] | None = None
    ) -> dict[str, Any]:
        return self.add(
            'todo', task, {'status': 'pending', 'depends_on': depends_on or []}
        )

    def complete_todo(self, task_id: str, result: str = '') -> dict[str, Any] | None:
        for e in self._entries:
            if e['id'] == task_id and e['type'] == 'todo':
                e['metadata']['status'] = 'completed'
                e['metadata']['completed_at'] = time.time()
                if result:
                    e['metadata']['result'] = result
                self._flush()
                return e
        return None

    def add_reflection(
        self, summary: str, tags: list[str] | None = None
    ) -> dict[str, Any]:
        return self.add('reflection', summary, {'tags': tags or []})

    def query(
        self, entry_type: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        entries = self._entries
        if entry_type:
            entries = [e for e in entries if e['type'] == entry_type]
        return entries[-limit:]

    def get_pending_todos(self) -> list[dict[str, Any]]:
        return [
            e
            for e in self._entries
            if e['type'] == 'todo' and e['metadata'].get('status') == 'pending'
        ]

    def get_completed_todos(self) -> list[dict[str, Any]]:
        return [
            e
            for e in self._entries
            if e['type'] == 'todo' and e['metadata'].get('status') == 'completed'
        ]

    def summary(self) -> str:
        if not self._entries:
            return 'No working memory entries yet.'

        lines = ['## Working Memory', '']
        decisions = self.query('decision', limit=5)
        todos = self.get_pending_todos()
        done = self.get_completed_todos()
        reflections = self.query('reflection', limit=3)

        if decisions:
            lines.append('### Decisions')
            for d in decisions:
                ctx = (
                    f' ({d["metadata"]["context"]})'
                    if d['metadata'].get('context')
                    else ''
                )
                lines.append(f'- {d["content"]}{ctx}')
            lines.append('')

        if todos:
            lines.append('### Pending Tasks')
            for t in todos:
                deps = (
                    f' [depends: {", ".join(t["metadata"]["depends_on"])}]'
                    if t['metadata'].get('depends_on')
                    else ''
                )
                lines.append(f'- {t["content"]}{deps}')
            lines.append('')

        if done:
            lines.append('### Completed Tasks')
            for d in done[-5:]:
                lines.append(f'- {d["content"]}')
            lines.append('')

        if reflections:
            lines.append('### Recent Reflections')
            for r in reflections:
                tags_str = (
                    f' [{", ".join(r["metadata"]["tags"])}]'
                    if r['metadata'].get('tags')
                    else ''
                )
                lines.append(f'- {r["content"]}{tags_str}')
            lines.append('')

        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self._mem_path.exists():
            try:
                with open(self._mem_path) as f:
                    data = json.load(f)
                self._entries = data.get('entries', [])
            except (json.JSONDecodeError, OSError) as e:
                _logger.warning('Failed to load working memory: %s', e)
                self._entries = []

    def _flush(self) -> None:
        try:
            tmp = self._mem_path.with_suffix('.tmp')
            with open(tmp, 'w') as f:
                json.dump({'entries': self._entries}, f, indent=2)
            os.replace(tmp, self._mem_path)
        except OSError as e:
            _logger.warning('Failed to flush working memory: %s', e)

    def clear_session(self) -> None:
        self._entries = []
        self._flush()

    # ------------------------------------------------------------------
    # Conversation-scoped factory (for hooks / event processors)
    # ------------------------------------------------------------------


_instance_registry: dict[str, WorkingMemory] = {}


def get_wm_for_conversation(
    conversation_id: str | None = None,
) -> WorkingMemory:
    """Return a conversation-scoped WorkingMemory instance.

    Shares the same backing directory so REST API and hook processors
    see the same state for a given conversation.
    """
    cid = conversation_id or 'default'
    if cid not in _instance_registry:
        base = Path(os.getcwd()) / '.wren' / 'conversations' / cid
        _instance_registry[cid] = WorkingMemory(project_root=str(base))
    return _instance_registry[cid]


def clear_wm_registry() -> None:
    _instance_registry.clear()
