"""Tests for middleware: CacheControl, RateLimit, CORS."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import PlainTextResponse

from wren.app_server.middleware import (
    CacheControlMiddleware,
    InMemoryRateLimiter,
    LocalhostCORSMiddleware,
    RateLimitMiddleware,
)


# ── CacheControlMiddleware ────────────────────────────────────────


class TestCacheControlMiddleware:
    """Tests for CacheControlMiddleware."""

    def _make_app(self) -> FastAPI:
        app = FastAPI()
        app.add_middleware(CacheControlMiddleware)

        @app.get('/api/v1/test')
        async def test_route():
            return PlainTextResponse('ok')

        @app.get('/assets/{path:path}')
        async def assets_route():
            return PlainTextResponse('ok')

        return app

    def test_api_routes_get_no_cache_headers(self):
        app = self._make_app()
        client = TestClient(app)
        resp = client.get('/api/v1/test')
        assert resp.status_code == 200
        assert (
            resp.headers['cache-control']
            == 'no-cache, no-store, must-revalidate, max-age=0'
        )
        assert resp.headers['pragma'] == 'no-cache'
        assert resp.headers['expires'] == '0'

    def test_assets_get_immutable_cache(self):
        app = self._make_app()
        client = TestClient(app)
        resp = client.get('/assets/app.js')
        assert resp.status_code == 200
        assert resp.headers['cache-control'] == 'public, max-age=2592000, immutable'


# ── InMemoryRateLimiter ───────────────────────────────────────────


class TestInMemoryRateLimiter:
    """Tests for InMemoryRateLimiter."""

    def test_allows_requests_under_limit(self):
        limiter = InMemoryRateLimiter(requests=3, seconds=60)
        request = MagicMock()
        request.client.host = '127.0.0.1'

        result = asyncio.get_event_loop().run_until_complete(limiter(request))
        assert result is True

    def test_history_tracks_requests(self):
        limiter = InMemoryRateLimiter(requests=5, seconds=10)
        request = MagicMock()
        request.client.host = '10.0.0.1'

        for _ in range(3):
            asyncio.get_event_loop().run_until_complete(limiter(request))

        assert len(limiter.history['10.0.0.1']) == 3

    def test_different_hosts_independent(self):
        limiter = InMemoryRateLimiter(requests=1, seconds=60)
        req1 = MagicMock()
        req1.client.host = '1.1.1.1'
        req2 = MagicMock()
        req2.client.host = '2.2.2.2'

        asyncio.get_event_loop().run_until_complete(limiter(req1))
        asyncio.get_event_loop().run_until_complete(limiter(req2))

        assert len(limiter.history['1.1.1.1']) == 1
        assert len(limiter.history['2.2.2.2']) == 1

    def test_clean_old_requests(self):
        limiter = InMemoryRateLimiter(requests=2, seconds=1)
        key = 'test-host'
        # Simulate old requests
        limiter.history[key] = [
            datetime.now(timezone.utc) - timedelta(seconds=5),
            datetime.now(timezone.utc) - timedelta(seconds=5),
        ]

        limiter._clean_old_requests(key)
        assert len(limiter.history[key]) == 0

    def test_rejects_when_over_limit(self):
        limiter = InMemoryRateLimiter(requests=2, seconds=60)
        request = MagicMock()
        request.client.host = '192.168.1.1'

        # Fill to the limit
        for _ in range(2):
            asyncio.get_event_loop().run_until_complete(limiter(request))

        # Third request should be rejected
        result = asyncio.get_event_loop().run_until_complete(limiter(request))
        assert result is False

    def test_get_retry_after(self):
        limiter = InMemoryRateLimiter(requests=1, seconds=60)
        request = MagicMock()
        request.client.host = '10.0.0.0'

        # No requests yet
        assert limiter.get_retry_after(request) == 0

        # After one request
        asyncio.get_event_loop().run_until_complete(limiter(request))
        retry = limiter.get_retry_after(request)
        assert 59 <= retry <= 60


# ── RateLimitMiddleware ───────────────────────────────────────────


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware."""

    def _make_app(self, rate_limiter: InMemoryRateLimiter | None = None) -> FastAPI:
        app = FastAPI()
        limiter = rate_limiter or InMemoryRateLimiter(requests=100, seconds=60)
        app.add_middleware(RateLimitMiddleware, rate_limiter=limiter)

        @app.get('/api/v1/test')
        async def test_route():
            return PlainTextResponse('ok')

        @app.get('/assets/{path:path}')
        async def assets_route():
            return PlainTextResponse('ok')

        @app.post('/api/v1/sandboxes/{id}/resume')
        async def resume_route():
            return PlainTextResponse('ok')

        return app

    def test_normal_request_passes(self):
        app = self._make_app()
        client = TestClient(app)
        resp = client.get('/api/v1/test')
        assert resp.status_code == 200

    def test_assets_bypass_rate_limit(self):
        limiter = InMemoryRateLimiter(requests=0, seconds=60)
        app = self._make_app(rate_limiter=limiter)
        client = TestClient(app)
        # Assets should bypass rate limiting even with 0 requests allowed
        resp = client.get('/assets/app.js')
        assert resp.status_code == 200

    def test_resume_bypasses_rate_limit(self):
        limiter = InMemoryRateLimiter(requests=0, seconds=60)
        app = self._make_app(rate_limiter=limiter)
        client = TestClient(app)
        # Sandbox resume should bypass rate limiting
        resp = client.post('/api/v1/sandboxes/test-session/resume')
        assert resp.status_code == 200

    def test_rate_limited_returns_429(self):
        limiter = InMemoryRateLimiter(requests=1, seconds=60)
        app = self._make_app(rate_limiter=limiter)
        client = TestClient(app)

        # First request passes
        resp = client.get('/api/v1/test')
        assert resp.status_code == 200

        # Second request exceeds limit
        resp = client.get('/api/v1/test')
        assert resp.status_code == 429
        assert 'retry-after' in resp.headers


# ── LocalhostCORSMiddleware ───────────────────────────────────────


class TestLocalhostCORSMiddleware:
    """Tests for LocalhostCORSMiddleware."""

    def _make_app(self, cors_origins: list[str] | None = None) -> FastAPI:
        app = FastAPI()

        with patch('wren.app_server.middleware.get_global_config') as mock_config:
            config = MagicMock()
            config.permitted_cors_origins = cors_origins or []
            mock_config.return_value = config
            app.add_middleware(LocalhostCORSMiddleware)

        @app.get('/api/v1/test')
        async def test_route():
            return PlainTextResponse('ok')

        return app

    def test_localhost_origin_allowed(self):
        app = self._make_app()
        client = TestClient(app)
        resp = client.get(
            '/api/v1/test',
            headers={'Origin': 'http://localhost:3000'},
        )
        assert resp.status_code == 200
        assert 'access-control-allow-origin' in resp.headers

    def test_127_0_0_1_origin_allowed(self):
        app = self._make_app()
        client = TestClient(app)
        resp = client.get(
            '/api/v1/test',
            headers={'Origin': 'http://127.0.0.1:3000'},
        )
        assert resp.status_code == 200
        assert 'access-control-allow-origin' in resp.headers

    def test_configured_origin_allowed(self):
        """When no CORS origins are configured, non-localhost is blocked (dev mode)."""
        app = self._make_app(cors_origins=[])
        client = TestClient(app)
        resp = client.get(
            '/api/v1/test',
            headers={'Origin': 'https://example.com'},
        )
        assert resp.status_code == 200
        # Non-localhost origin blocked when no origins configured
        assert 'access-control-allow-origin' not in resp.headers

    def test_non_localhost_blocked_when_no_origins_configured(self):
        """Non-localhost origins must be blocked when no CORS origins are configured."""
        app = self._make_app(cors_origins=[])
        client = TestClient(app)
        resp = client.get(
            '/api/v1/test',
            headers={'Origin': 'https://evil.com'},
        )
        assert resp.status_code == 200
        assert 'access-control-allow-origin' not in resp.headers
