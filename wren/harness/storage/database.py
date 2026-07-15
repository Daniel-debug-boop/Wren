"""SQLite storage backend — ACID persistence for all harness subsystems.

Schema is versioned and auto-migrated on first import. Every table
uses WAL mode for concurrent read performance.

Tables:
  - harness_meta          Schema version + key/value metadata
  - harness_children      Child agent registry (persisted across crashes)
  - harness_task_graph    Task graph nodes + edges
  - harness_facts         Registered facts for FactChecker
  - harness_logs          Structured telemetry log
  - harness_vectors       Embeddings + content for VectorStore
  - harness_metrics       Prometheus-style metric counters
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from typing import Any

_logger = logging.getLogger(__name__)

SCHEMA_VERSION = 2


def _dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict[str, Any]:
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


class _Database:
    """Thread-safe SQLite database with WAL mode."""

    SCHEMA = {
        1: """
        CREATE TABLE IF NOT EXISTS harness_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS harness_children (
            agent_id TEXT PRIMARY KEY,
            agent_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'created',
            task_name TEXT DEFAULT '',
            result TEXT DEFAULT '',
            error TEXT DEFAULT '',
            updated_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS harness_task_graph (
            task_id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS harness_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim TEXT UNIQUE NOT NULL,
            confidence REAL NOT NULL DEFAULT 1.0,
            source TEXT DEFAULT '',
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS harness_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            module TEXT DEFAULT '',
            data TEXT DEFAULT '',
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS harness_vectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            embedding TEXT NOT NULL DEFAULT '[]',
            tags TEXT DEFAULT '',
            namespace TEXT DEFAULT 'default',
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS harness_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            value REAL NOT NULL DEFAULT 0.0,
            updated_at REAL NOT NULL
        );
        """,
        2: """
        CREATE INDEX IF NOT EXISTS idx_harness_vectors_namespace ON harness_vectors(namespace);
        CREATE INDEX IF NOT EXISTS idx_harness_logs_level ON harness_logs(level);
        CREATE INDEX IF NOT EXISTS idx_harness_children_status ON harness_children(status);
        """,
    }

    def __init__(self, path: str = ':memory:') -> None:
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False, timeout=30)
        self._conn.row_factory = _dict_factory
        self._conn.execute('PRAGMA journal_mode=WAL')
        self._conn.execute('PRAGMA foreign_keys=ON')
        self._migrate()

    def _migrate(self) -> None:
        with self._lock:
            # Check current version — handle fresh database with no tables
            try:
                cur = self._conn.execute(
                    "SELECT value FROM harness_meta WHERE key='schema_version'"
                )
                row = cur.fetchone()
                version = int(row['value']) if row else 0
            except sqlite3.OperationalError:
                # No harness_meta table yet — brand new database
                version = 0

            for v in range(version + 1, max(self.SCHEMA) + 1):
                statements = self.SCHEMA.get(v, '').strip()
                if statements:
                    self._conn.executescript(statements)
                # Ensure meta table exists after schema 1
                self._conn.execute(
                    "INSERT OR REPLACE INTO harness_meta (key, value) VALUES ('schema_version', ?)",
                    (str(v),),
                )
                _logger.info('Schema migrated to version %d', v)
            self._conn.commit()

    # ── Children ─────────────────────────────────────────────────

    def child_save(
        self,
        agent_id: str,
        agent_type: str,
        status: str,
        *,
        task_name: str = '',
        result: Any = None,
        error: str = '',
    ) -> None:
        with self._lock:
            self._conn.execute(
                """INSERT OR REPLACE INTO harness_children
                   (agent_id, agent_type, status, task_name, result, error, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    agent_id,
                    agent_type,
                    status,
                    task_name,
                    json.dumps(result) if result else '',
                    error,
                    time.time(),
                ),
            )
            self._conn.commit()

    def child_get(self, agent_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                'SELECT * FROM harness_children WHERE agent_id = ?', (agent_id,)
            ).fetchone()
        return row

    def child_all(self) -> list[dict[str, Any]]:
        with self._lock:
            return self._conn.execute(
                'SELECT * FROM harness_children ORDER BY updated_at DESC'
            ).fetchall()

    def child_delete(self, agent_id: str) -> None:
        with self._lock:
            self._conn.execute(
                'DELETE FROM harness_children WHERE agent_id = ?', (agent_id,)
            )
            self._conn.commit()

    # ── Task Graph ───────────────────────────────────────────────

    def task_save(self, task_id: str, data: dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute(
                'INSERT OR REPLACE INTO harness_task_graph (task_id, data, updated_at) VALUES (?, ?, ?)',
                (task_id, json.dumps(data), time.time()),
            )
            self._conn.commit()

    def task_get(self, task_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                'SELECT * FROM harness_task_graph WHERE task_id = ?', (task_id,)
            ).fetchone()
        return json.loads(row['data']) if row else None

    def task_all(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                'SELECT * FROM harness_task_graph ORDER BY updated_at DESC'
            ).fetchall()
        return [json.loads(r['data']) for r in rows]

    # ── Facts ────────────────────────────────────────────────────

    def fact_add(self, claim: str, confidence: float = 1.0, source: str = '') -> None:
        with self._lock:
            self._conn.execute(
                'INSERT OR IGNORE INTO harness_facts (claim, confidence, source, created_at) VALUES (?, ?, ?, ?)',
                (claim, confidence, source, time.time()),
            )
            self._conn.commit()

    def fact_all(self) -> list[dict[str, Any]]:
        with self._lock:
            return self._conn.execute(
                'SELECT * FROM harness_facts ORDER BY created_at DESC'
            ).fetchall()

    def fact_delete(self, claim: str) -> None:
        with self._lock:
            self._conn.execute('DELETE FROM harness_facts WHERE claim = ?', (claim,))
            self._conn.commit()

    # ── Logs ─────────────────────────────────────────────────────

    def log_write(
        self, level: str, message: str, module: str = '', data: dict | None = None
    ) -> None:
        with self._lock:
            self._conn.execute(
                'INSERT INTO harness_logs (level, message, module, data, created_at) VALUES (?, ?, ?, ?, ?)',
                (
                    level.upper(),
                    message[:500],
                    module,
                    json.dumps(data) if data else '{}',
                    time.time(),
                ),
            )
            self._conn.commit()

    def log_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return self._conn.execute(
                'SELECT * FROM harness_logs ORDER BY created_at DESC LIMIT ?', (limit,)
            ).fetchall()

    # ── Vectors ──────────────────────────────────────────────────

    def vector_save(
        self,
        key: str,
        content: str,
        embedding: list[float],
        tags: str = '',
        namespace: str = 'default',
    ) -> None:
        with self._lock:
            self._conn.execute(
                """INSERT OR REPLACE INTO harness_vectors
                   (key, content, embedding, tags, namespace, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (key, content, json.dumps(embedding), tags, namespace, time.time()),
            )
            self._conn.commit()

    def vector_all(self, namespace: str = 'default') -> list[dict[str, Any]]:
        with self._lock:
            return self._conn.execute(
                'SELECT * FROM harness_vectors WHERE namespace = ? ORDER BY created_at DESC',
                (namespace,),
            ).fetchall()

    def vector_search(
        self, query: str, namespace: str = 'default'
    ) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                'SELECT * FROM harness_vectors WHERE namespace = ? AND content LIKE ?',
                (namespace, f'%{query}%'),
            ).fetchall()
        return rows

    def vector_delete(self, key: str) -> None:
        with self._lock:
            self._conn.execute('DELETE FROM harness_vectors WHERE key = ?', (key,))
            self._conn.commit()

    def vector_delete_namespace(self, namespace: str) -> None:
        with self._lock:
            self._conn.execute(
                'DELETE FROM harness_vectors WHERE namespace = ?', (namespace,)
            )
            self._conn.commit()

    # ── Metrics ──────────────────────────────────────────────────

    def metric_incr(self, name: str, value: float = 1.0) -> None:
        with self._lock:
            self._conn.execute(
                """INSERT INTO harness_metrics (name, value, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(name) DO UPDATE SET value = value + ?, updated_at = ?""",
                (name, value, time.time(), value, time.time()),
            )
            self._conn.commit()

    def metric_set(self, name: str, value: float) -> None:
        with self._lock:
            self._conn.execute(
                """INSERT OR REPLACE INTO harness_metrics (name, value, updated_at)
                   VALUES (?, ?, ?)""",
                (name, value, time.time()),
            )
            self._conn.commit()

    def all_metrics(self) -> dict[str, float]:
        with self._lock:
            rows = self._conn.execute(
                'SELECT name, value FROM harness_metrics'
            ).fetchall()
        return {r['name']: r['value'] for r in rows}

    def metric_delete(self, name: str) -> None:
        with self._lock:
            self._conn.execute('DELETE FROM harness_metrics WHERE name = ?', (name,))
            self._conn.commit()

    # ── Meta ─────────────────────────────────────────────────────

    def meta_get(self, key: str, default: str = '') -> str:
        with self._lock:
            row = self._conn.execute(
                'SELECT value FROM harness_meta WHERE key = ?', (key,)
            ).fetchone()
        return row['value'] if row else default

    def meta_set(self, key: str, value: str) -> None:
        with self._lock:
            self._conn.execute(
                'INSERT OR REPLACE INTO harness_meta (key, value) VALUES (?, ?)',
                (key, value),
            )
            self._conn.commit()

    # ── Connection ───────────────────────────────────────────────

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    def close(self) -> None:
        with self._lock:
            self._conn.commit()
            self._conn.close()


# Module-level singleton — all subsystems share this
# Path from env var, fallback to file in temp, then :memory:
import os as _os

_DB_PATH = _os.environ.get('OPENHANDS_HARNESS_DB_PATH', '/tmp/wren/harness.db')
if _DB_PATH:
    _os.makedirs(_os.path.dirname(_DB_PATH), exist_ok=True)
DB = _Database(_DB_PATH)
