"""Health check — full system diagnostics endpoint.

Returns structured health report covering all subsystems.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from wren.harness.storage.database import DB


@dataclass
class HealthReport:
    status: str = 'healthy'  # healthy / degraded / down
    uptime_s: float = 0.0
    started_at: float = field(default_factory=time.time)
    checks: dict[str, dict[str, Any]] = field(default_factory=dict)
    version: str = '2.0.0'

    def to_dict(self) -> dict[str, Any]:
        return {
            'status': self.status,
            'version': self.version,
            'uptime_s': round(self.uptime_s, 1),
            'checks': self.checks,
        }


class HealthChecker:
    """Runs diagnostics on all subsystems."""

    def __init__(self) -> None:
        self._started_at = time.time()
        self._report = HealthReport()

    def check_all(self) -> HealthReport:
        self._report = HealthReport(started_at=self._started_at)
        self._report.uptime_s = time.time() - self._started_at

        checks = {
            'database': self._check_db(),
            'metrics': self._check_metrics(),
            'children': self._check_children(),
        }
        self._report.checks = checks

        # Overall status
        failures = [k for k, v in checks.items() if v.get('status') == 'down']
        degraded = [k for k, v in checks.items() if v.get('status') == 'degraded']
        if failures:
            self._report.status = 'down'
        elif degraded:
            self._report.status = 'degraded'

        return self._report

    @staticmethod
    def _check_db() -> dict[str, Any]:
        try:
            row = DB._conn.execute(
                "SELECT value FROM harness_meta WHERE key='schema_version'"
            ).fetchone()
            return {
                'status': 'healthy',
                'schema_version': int(row['value']) if row else 0,
            }
        except Exception as e:
            return {'status': 'down', 'error': str(e)}

    @staticmethod
    def _check_metrics() -> dict[str, Any]:
        try:
            metrics = DB.all_metrics()
            return {'status': 'healthy', 'metric_count': len(metrics)}
        except Exception as e:
            return {'status': 'degraded', 'error': str(e)}

    @staticmethod
    def _check_children() -> dict[str, Any]:
        try:
            children = DB.child_all()
            active = sum(
                1
                for c in children
                if c.get('status') in ('idle', 'busy', 'initializing')
            )
            return {'status': 'healthy', 'total': len(children), 'active': active}
        except Exception as e:
            return {'status': 'degraded', 'error': str(e)}
