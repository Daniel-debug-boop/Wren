"""Tests for the harness REST API router configuration."""

import pytest

pytest.importorskip('wren.harness')

from wren.app_server.orchestration.harness_router import router


class TestHarnessRouter:
    def test_router_prefix(self):
        assert router.prefix == '/api/orchestration/harness'

    def test_router_tags(self):
        assert 'harness' in router.tags

    def test_routes_registered(self):
        """Test that all expected routes are registered."""
        routes = {route.path for route in router.routes}
        expected = [
            '/process-goal',
            '/spawn-agent',
            '/assign-task',
            '/kill-agent',
            '/status',
            '/health',
            '/children',
            '/think',
            '/session/close',
        ]
        for path in expected:
            found = any(path in r for r in routes)
            assert found, f'Route {path} not found in {routes}'
