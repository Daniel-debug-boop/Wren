"""
Wren AI server runner for Android.

Called from Kotlin via Chaquopy's Python bridge.
Starts the FastAPI/uvicorn server on a background thread.

The Wren backend code is bundled in assets/python/wren/
and the pre-built React frontend in assets/www/.
"""

import os
import sys
import logging
import threading
import uvicorn
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('wren.android')

# ── Paths ----------------------------------------------------------------
FILES_DIR = os.environ.get('WREN_FILES_DIR', '/data/data/com.wren.android/files')
WREN_SRC = os.path.join(FILES_DIR, 'wren')
FRONTEND_DIR = os.path.join(FILES_DIR, 'www')

# ── Server state ---------------------------------------------------------
_server = None
_stop_event = threading.Event()
_config = {}  # Stores current settings from Kotlin


def _make_app():
    """Build and return a FastAPI app that serves the Wren API + frontend."""
    sys.path.insert(0, WREN_SRC)

    # Apply settings to environment so the Wren backend can read them
    api_key = _config.get('api_key', '')
    model = _config.get('model', 'wren/o3')
    base_url = _config.get('base_url', '')

    if api_key:
        os.environ['LLM_API_KEY'] = api_key
        os.environ['OPENAI_API_KEY'] = api_key  # Some backends read this
    os.environ['LLM_MODEL'] = model
    if base_url:
        os.environ['LLM_BASE_URL'] = base_url

    logger.info(f'Starting with model={model}, base_url={base_url or "(default)"}')

    # --- Backend API (Wren's FastAPI app) ---
    try:
        from wren.server.listen import app as wren_app
    except ImportError:
        # Fallback: minimal stub so the WebView at least shows something
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse, JSONResponse

        wren_app = FastAPI(title='Wren AI')

        @wren_app.get('/api/health')
        async def health():
            return {
                'status': 'ok',
                'version': '1.0.0',
                'model': model,
                'api_key_set': bool(api_key)
            }

        @wren_app.get('/api/settings')
        async def settings():
            return JSONResponse({
                'model': model,
                'base_url': base_url,
                'api_key_set': bool(api_key),
                'port': _config.get('port', 12000)
            })

        @wren_app.get('/')
        async def index():
            index_path = os.path.join(FRONTEND_DIR, 'index.html')
            if os.path.exists(index_path):
                with open(index_path) as f:
                    return HTMLResponse(f.read())
            return HTMLResponse('<h1>Wren AI</h1><p>Frontend not built yet.</p>')

        logger.warning('Wren backend not found — running in stub mode')
        return wren_app

    # --- Mount frontend static files ---
    from fastapi.staticfiles import StaticFiles

    if os.path.isdir(FRONTEND_DIR):
        wren_app.mount('/static', StaticFiles(directory=FRONTEND_DIR), name='frontend')

    return wren_app


def start_server(config=None):
    """
    Start the uvicorn server on a daemon thread.

    Args:
        config: dict with keys 'port', 'api_key', 'model', 'base_url'
                Can be called from Kotlin as:
                py.getModule('wren_server_runner').callAttr('start_server', config_dict)
    """
    global _server, _config

    # Accept config as Chaquopy Python dict or plain dict
    if config is not None:
        if isinstance(config, dict):
            _config = config
        else:
            logger.warning(f'Unexpected config type {type(config).__name__}, falling back to env vars')
            config = None
    if config is None:
        # Fallback: read from environment (legacy callers)
        _config = {
            'port': int(os.environ.get('WREN_SERVER_PORT', '12000')),
            'api_key': os.environ.get('WREN_LLM_API_KEY', ''),
            'model': os.environ.get('WREN_LLM_MODEL', 'wren/o3'),
            'base_url': os.environ.get('WREN_LLM_BASE_URL', '')
        }

    # Validate port (FIXED: removed syntax error from previous version)
    port = int(_config.get('port', 12000))
    if not (1024 <= port <= 65535):
        logger.warning(f'Invalid port {port}, falling back to 12000')
        port = 12000
        _config['port'] = port

    _stop_event.clear()

    app = _make_app()

    uvicorn_config = uvicorn.Config(
        app,
        host='127.0.0.1',
        port=port,
        log_level='info',
        loop='asyncio',
    )
    _server = uvicorn.Server(uvicorn_config)

    thread = threading.Thread(
        target=_server.run,
        daemon=True,
        name='wren-uvicorn',
    )
    thread.start()
    logger.info(f'Wren AI server started on port {port}')
    return {'status': 'started', 'port': port}


def stop_server():
    """Gracefully stop the server."""
    global _server
    _stop_event.set()
    if _server:
        _server.should_exit = True
        _server = None
    logger.info('Wren AI server stopped')
    return {'status': 'stopped'}


def server_status():
    """Return current server status."""
    return {
        'running': _server is not None and not _stop_event.is_set(),
        'port': _config.get('port', 12000),
        'model': _config.get('model', 'wren/o3'),
        'api_key_set': bool(_config.get('api_key'))
    }
