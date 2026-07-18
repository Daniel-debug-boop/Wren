"""Tests for health checker."""

import pytest
from wren.harness.health import HealthChecker


class TestHealthChecker:
    def test_check_all_returns_report(self):
        hc = HealthChecker()
        report = hc.check_all()
        d = report.to_dict()
        assert 'status' in d
        assert 'version' in d
        assert 'uptime_s' in d
        assert 'checks' in d

    def test_check_all_healthy(self):
        hc = HealthChecker()
        report = hc.check_all()
        assert report.status in ('healthy', 'degraded')

    def test_database_check(self):
        hc = HealthChecker()
        result = hc._check_db()
        assert result['status'] == 'healthy'
        assert result.get('schema_version') is not None
