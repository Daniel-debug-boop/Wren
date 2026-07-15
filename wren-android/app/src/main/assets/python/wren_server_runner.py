"""
Wren AI server runner for Android.

Called from Kotlin via Chaquopy's Python bridge.
Starts the FastAPI/uvicorn server on a background thread.

The Wren backend code is bundled in assets/python/wren/
and the pre-built React frontend in assets/www/.
"""

import os
import sys
import json
import logging
import threading
import uvicorn
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('wren.android')

# ── Paths ----------------------------------------------------------------
# Resolved at runtime from the Android app's files dir
FILES_DIR = os.environ.get('WREN_FILES_DIR', '/data/data/com.wren.android/files')
WREN_SRC = os.path.join(FILES_DIR, 'wren')
FRONTEND_DIR = os.path.join(FILES_DIR, 'www')

# ── Server state ---------------------------------------------------------
_server = None
_stop_event = threading.Event()


def _make_app():
    """Build and return a FastAPI app that serves the Wren API + frontend."""
    sys.path.insert(0, WREN_SRC)

    # --- Backend API (Wren's FastAPI app) ---
    try:
        from wren.server.listen import app as wren_app
    except ImportError:
        # Fallback: minimal stub so the WebView at least shows something
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse

        wren_app = FastAPI(title='Wren AI')

        @wren_app.get('/api/health')
        async def health():
            return {'status': 'ok', 'version': '1.0.0'}

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


def start_server(port: int = 12000):
    """
    Start the uvicorn server on a daemon thread.
    Called from Kotlin via Python.getInstance().
    """
    global _server
    _stop_event.clear()

    app = _make_app()

    config = uvicorn.Config(
        app,
        host='127.0.0.1',
        port=port,
        log_level='info',
        loop='asyncio',
    )
    _server = uvicorn.Server(config)

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
        'port': 12000,
    }
