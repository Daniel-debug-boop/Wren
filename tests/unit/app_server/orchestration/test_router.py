"""Tests for the orchestration REST API router.

These are lightweight tests that verify the router is properly configured
(prefix, tags, registered routes) without spinning up a full server.
"""

import pytest

pytest.importorskip('fastapi')

from wren.app_server.orchestration.router import router


class TestOrchestrationRouter:
    def test_router_prefix(self):
        """Test the router has the correct prefix."""
        assert router.prefix == '/api/orchestration'

    def test_router_tags(self):
        """Test the router has the correct tags."""
        assert 'orchestration' in router.tags

    def test_routes_registered(self):
        """Test that all expected routes are registered.

        Uses substring matching because FastAPI route.path includes the
        router prefix (e.g. '/api/orchestration/memory').
        """
        route_paths = {route.path for route in router.routes}

        expected_substrings = [
            '/memory',
            '/memory/decision',
            '/memory/reflection',
            '/memory/summary',
            '/manager/init',
            '/manager/decompose',
            '/manager/plan',
            '/manager/status',
            '/manager/summary',
            '/manager/start-task',
            '/manager/complete-task',
            '/manager/finalize',
            '/reflect',
            '/lessons',
            '/sub-agent/spawn',
            '/sub-agent/execute',
            '/error/classify',
            '/error/retry',
            '/error/solutions',
        ]
        for substring in expected_substrings:
            assert any(
                substring in p for p in route_paths
            ), f'Route containing "{substring}" not found'

    def test_router_methods(self):
        """Test that routes have expected HTTP methods.

        Uses substring matching for paths since FastAPI route.path
        includes the router prefix.
        """
        route_map = {}
        for route in router.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                for method in route.methods:
                    route_map.setdefault(route.path, []).append(method)

        # At least one route matching '/memory' should have GET
        memory_get = [
            p for p in route_map if '/memory' in p and 'GET' in route_map[p]
        ]
        assert len(memory_get) > 0

        # At least one route matching 'decision' should have POST
        decision_post = [
            p
            for p in route_map
            if 'decision' in p
            and 'POST' in route_map[p]
        ]
        assert len(decision_post) > 0

        # At least one route matching '/memory' should have DELETE
        memory_delete = [
            p for p in route_map if '/memory' in p and 'DELETE' in route_map[p]
        ]
        assert len(memory_delete) > 0
