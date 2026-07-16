import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response
from starlette.types import ASGIApp

from wren.app_server.config import get_global_config

_RESUME_RE = re.compile(r'^/api/v1/sandboxes/[^/]+/resume/?$')


class LocalhostCORSMiddleware(CORSMiddleware):
    """Custom CORS middleware that allows any request from localhost/127.0.0.1 domains,
    while using standard CORS rules for other origins.
    """

    def __init__(self, app: ASGIApp) -> None:
        config = get_global_config()
        allow_origins = tuple(config.permitted_cors_origins)
        super().__init__(
            app,
            allow_origins=allow_origins,
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )

    def is_allowed_origin(self, origin: str) -> bool:
        if origin and not self.allow_origins and not self.allow_origin_regex:
            parsed = urlparse(origin)
            hostname = parsed.hostname or ''

            # Allow any localhost/127.0.0.1 origin regardless of port (development mode)
            if hostname in ['localhost', '127.0.0.1']:
                return True

            # Block non-localhost origins when no specific origins are configured
            logging.getLogger(__name__).warning(
                f'Blocked origin: {origin}. '
                'Set OH_PERMITTED_CORS_ORIGINS for production environments.'
            )
            return False

        # For missing origin or other origins, use the parent class's logic
        result: bool = super().is_allowed_origin(origin)
        return result


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Middleware to disable caching for all routes by adding appropriate headers"""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        if request.url.path.startswith('/assets'):
            # The content of the assets directory has fingerprinted file names so we cache aggressively
            response.headers['Cache-Control'] = 'public, max-age=2592000, immutable'
        else:
            response.headers['Cache-Control'] = (
                'no-cache, no-store, must-revalidate, max-age=0'
            )
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply baseline security headers to every response."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=()'
        )
        # Only set HSTS when the request arrived over HTTPS (e.g. behind a
        # reverse proxy). Browsers ignore HSTS over plain HTTP so this avoids
        # pinning local dev environments to TLS.
        if request.url.scheme == 'https':
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains'
            )
        return response


class InMemoryRateLimiter:
    """Sliding-window rate limiter. Resets on process restart.
    Use RedisRateLimiter for production deployments.
    """

    history: dict[str, list[datetime]]
    max_requests: int
    window_seconds: int

    def __init__(self, requests: int = 30, seconds: int = 60):
        self.max_requests = requests
        self.window_seconds = seconds
        self.history = defaultdict(list)

    def _clean_old_requests(self, key: str) -> None:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.window_seconds)
        self.history[key] = [ts for ts in self.history[key] if ts > cutoff]

    async def __call__(self, request: Request) -> bool:
        key = request.client.host
        self._clean_old_requests(key)

        if len(self.history[key]) >= self.max_requests:
            return False

        self.history[key].append(datetime.now(timezone.utc))
        return True

    def get_retry_after(self, request: Request) -> int:
        """Return seconds until the oldest request in the window expires."""
        key = request.client.host
        self._clean_old_requests(key)
        if not self.history[key]:
            return 0
        oldest = self.history[key][0]
        elapsed = (datetime.now(timezone.utc) - oldest).total_seconds()
        return max(1, int(self.window_seconds - elapsed))


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, rate_limiter: InMemoryRateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not self.is_rate_limited_request(request):
            return await call_next(request)
        ok = await self.rate_limiter(request)
        if not ok:
            retry_after = self.rate_limiter.get_retry_after(request)
            return JSONResponse(
                status_code=429,
                content={'message': 'Too many requests'},
                headers={'Retry-After': str(retry_after)},
            )
        return await call_next(request)

    def is_rate_limited_request(self, request: StarletteRequest) -> bool:
        return not (
            request.url.path.startswith('/assets')
            or self._is_sandbox_resume_request(request)
        )

    def _is_sandbox_resume_request(self, request: StarletteRequest) -> bool:
        return request.method == 'POST' and bool(_RESUME_RE.match(request.url.path))
