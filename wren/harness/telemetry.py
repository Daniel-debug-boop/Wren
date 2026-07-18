"""Structured telemetry — structured JSON logging + Prometheus-style
metrics counters.

All harness subsystems emit through here instead of raw print/logging.
"""

from __future__ import annotations

import logging
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Any

from wren.harness.storage.store import Store

_logger = logging.getLogger(__name__)


@dataclass
class TelemetryEvent:
    event: str
    level: str = 'INFO'
    module: str = ''
    message: str = ''
    duration_ms: float = 0.0
    error: str = ''
    tags: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            'event': self.event,
            'level': self.level,
            'module': self.module,
            'message': self.message[:500],
            'duration_ms': round(self.duration_ms, 1),
            'error': self.error[:300] if self.error else '',
            'tags': self.tags,
            'timestamp': round(self.timestamp, 3),
            **self.extra,
        }


class Telemetry:
    """Structured telemetry emitter.

    Writes to:
      1. Python logging (human-readable)
      2. SQLite harness_logs table (queryable)
      3. Prometheus-style counters via Store.incr_metric()
    """

    def __init__(self, module: str = 'harness') -> None:
        self._module = module

    # ── Events ───────────────────────────────────────────────────

    def info(self, event: str, message: str = '', **kw: Any) -> None:
        self._emit('INFO', event, message, **kw)

    def warn(self, event: str, message: str = '', **kw: Any) -> None:
        self._emit('WARN', event, message, **kw)

    def error(
        self, event: str, message: str = '', exc_info: bool = False, **kw: Any
    ) -> None:
        if exc_info:
            kw.setdefault('error', traceback.format_exc(limit=3))
        self._emit('ERROR', event, message, **kw)
        Store.incr_metric('errors_total')

    def metric(self, name: str, value: float = 1.0) -> None:
        """Increment a Prometheus-style counter."""
        Store.incr_metric(name, value)

    def timing(self, name: str, duration_s: float) -> None:
        """Record a timing metric (converted to ms)."""
        Store.set_metric(f'{name}_ms', round(duration_s * 1000, 1))

    # ── Internal ─────────────────────────────────────────────────

    def _emit(self, level: str, event: str, message: str, **kw: Any) -> None:
        ev = TelemetryEvent(
            event=event,
            level=level,
            module=self._module,
            message=message or event,
            error=kw.pop('error', ''),
            duration_ms=kw.pop('duration_ms', 0.0),
            tags=kw.pop('tags', []),
            extra=kw,
        )
        # Python logging
        log_fn = getattr(_logger, level.lower(), _logger.info)
        log_fn('[%s] %s%s', event, message, f' ({kw})' if kw else '')

        # SQLite
        try:
            Store.write_log(level, ev.message, self._module, ev.to_dict())
        except Exception as exc:
            _logger.warning('Telemetry: DB log failed: %s', exc)

        # Console for CRITICAL level
        if level == 'CRITICAL':
            print(f'CRITICAL [{event}] {message}', file=sys.stderr, flush=True)


# Module-level singleton — all subsystems share this
T = Telemetry()
