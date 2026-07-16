import contextlib
import logging
import os
import signal
import warnings

from fastapi.routing import Mount

_logger = logging.getLogger(__name__)

with warnings.catch_warnings():
    warnings.simplefilter('ignore')

from fastapi import (
    FastAPI,
    Request,
)
from fastapi.responses import JSONResponse

from wren.app_server import v1_router
from wren.app_server.config import get_app_lifespan_service
from wren.app_server.integrations.service_types import AuthenticationError
from wren.app_server.mcp.mcp_router import init_tavily_proxy, mcp_server
from wren.app_server.middleware import (
    CacheControlMiddleware,
    InMemoryRateLimiter,
    LocalhostCORSMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from wren.app_server.orchestration.router import router as orchestration_router
from wren.app_server.orchestration.harness_router import router as harness_router
from wren.app_server.design_analyzer_router import router as design_analyzer_router
from wren.app_server.intent_router import router as intent_router
from wren.app_server.settings.provider_router import router as provider_router
from wren.app_server.skill_synthesis_router import router as skill_synthesis_router
from wren.app_server.static import SPAStaticFiles
from wren.app_server.status.status_router import router as health_router
from wren.app_server.version import get_version

# Initialize the Tavily MCP proxy before creating the app
init_tavily_proxy()

mcp_app = mcp_server.http_app(path='/mcp', stateless_http=True)


def combine_lifespans(*lifespans):
    # Create a combined lifespan to manage multiple session managers
    @contextlib.asynccontextmanager
    async def combined_lifespan(app):
        async with contextlib.AsyncExitStack() as stack:
            for lifespan in lifespans:
                await stack.enter_async_context(lifespan(app))
            yield

    return combined_lifespan


lifespans = [mcp_app.lifespan]
app_lifespan_ = get_app_lifespan_service()
if app_lifespan_:
    lifespans.append(app_lifespan_.lifespan)


app = FastAPI(
    title='OpenHands',
    description='OpenHands: Code Less, Make More',
    version=get_version(),
    lifespan=combine_lifespans(*lifespans),
    routes=[Mount(path='/mcp', app=mcp_app)],
)


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=401,
        content=str(exc),
    )


app.include_router(v1_router.router)
app.include_router(health_router)
app.include_router(orchestration_router)
app.include_router(harness_router)
app.include_router(design_analyzer_router)
app.include_router(intent_router)
app.include_router(skill_synthesis_router)
app.include_router(provider_router)

# Middleware and static file setup (merged from listen.py)
if os.getenv('SERVE_FRONTEND', 'true').lower() == 'true':
    if os.path.isdir('./frontend/build'):
        app.mount(
            '/', SPAStaticFiles(directory='./frontend/build', html=True), name='dist'
        )

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LocalhostCORSMiddleware)
app.add_middleware(CacheControlMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    rate_limiter=InMemoryRateLimiter(requests=30, seconds=60),
)


# Graceful shutdown signal handlers
def _handle_shutdown_signal(signum: int, frame) -> None:
    sig_name = signal.Signals(signum).name
    _logger.warning(
        'shutdown.signal_received signal=%s — server shutting down', sig_name
    )


signal.signal(signal.SIGTERM, _handle_shutdown_signal)
signal.signal(signal.SIGINT, _handle_shutdown_signal)
