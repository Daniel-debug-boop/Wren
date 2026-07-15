"""Unified persistence facade — single import for all storage needs.

Wraps _Database with convenience methods used by every subsystem.
This is the ONLY file outside storage/ that should import database.py directly.
"""

from __future__ import annotations

import json
import time
from typing import Any

from wren.harness.storage.database import DB


class Store:
    """Convenience wrapper around _Database for harness subsystems.

    All methods are class-level so subsystems can call them without
    instantiating a Store object.
    """

    # ── Children ─────────────────────────────────────────────────

    @classmethod
    def save_child(
        cls,
        agent_id: str,
        agent_type: str,
        status: str,
        *,
        task_name: str = '',
        result: Any = None,
        error: str = '',
    ) -> None:
        DB.child_save(
            agent_id,
            agent_type,
            status,
            task_name=task_name,
            result=result,
            error=error,
        )

    @classmethod
    def get_child(cls, agent_id: str) -> dict[str, Any] | None:
        return DB.child_get(agent_id)

    @classmethod
    def all_children(cls) -> list[dict[str, Any]]:
        return DB.child_all()

    @classmethod
    def delete_child(cls, agent_id: str) -> None:
        DB.child_delete(agent_id)

    # ── Task Graph ───────────────────────────────────────────────

    @classmethod
    def save_task(cls, task_id: str, data: dict[str, Any]) -> None:
        DB.task_save(task_id, data)

    @classmethod
    def get_task(cls, task_id: str) -> dict[str, Any] | None:
        return DB.task_get(task_id)

    @classmethod
    def all_tasks(cls) -> list[dict[str, Any]]:
        return DB.task_all()

    # ── Facts ────────────────────────────────────────────────────

    @classmethod
    def add_fact(cls, claim: str, confidence: float = 1.0, source: str = '') -> None:
        DB.fact_add(claim, confidence, source)

    @classmethod
    def all_facts(cls) -> list[dict[str, Any]]:
        return DB.fact_all()

    @classmethod
    def delete_fact(cls, claim: str) -> None:
        DB.fact_delete(claim)

    # ── Logs ─────────────────────────────────────────────────────

    @classmethod
    def write_log(
        cls, level: str, message: str, module: str = '', data: dict | None = None
    ) -> None:
        DB.log_write(level, message, module, data)

    @classmethod
    def recent_logs(cls, limit: int = 50) -> list[dict[str, Any]]:
        return DB.log_recent(limit)

    # ── Vectors ──────────────────────────────────────────────────

    @classmethod
    def save_vector(
        cls,
        key: str,
        content: str,
        embedding: list[float],
        tags: str = '',
        namespace: str = 'default',
    ) -> None:
        DB.vector_save(key, content, embedding, tags, namespace)

    @classmethod
    def all_vectors(cls, namespace: str = 'default') -> list[dict[str, Any]]:
        return DB.vector_all(namespace)

    @classmethod
    def search_vectors(
        cls, query: str, namespace: str = 'default'
    ) -> list[dict[str, Any]]:
        return DB.vector_search(query, namespace)

    @classmethod
    def delete_vector(cls, key: str) -> None:
        DB.vector_delete(key)

    @classmethod
    def delete_vector_namespace(cls, namespace: str) -> None:
        DB.vector_delete_namespace(namespace)

    # ── Metrics ──────────────────────────────────────────────────

    @classmethod
    def incr_metric(cls, name: str, value: float = 1.0) -> None:
        DB.metric_incr(name, value)

    @classmethod
    def set_metric(cls, name: str, value: float) -> None:
        DB.metric_set(name, value)

    @classmethod
    def all_metrics(cls) -> dict[str, float]:
        return DB.all_metrics()
