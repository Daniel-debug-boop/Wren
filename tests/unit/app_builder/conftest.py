"""Pytest fixtures and configuration for app_builder tests.

This conftest creates a wren module stub BEFORE any test module imports
wren submodules, bypassing wren/__init__.py's heavy dependency chain
(fastapi, pydantic, etc.) that aren't available during unit testing.
"""

import sys
import types
from pathlib import Path

# ── Wren module stub ─────────────────────────────────────────────
# This must run at conftest load time, before any test file imports
# from wren.app_builder or wren.omniroute.

_wren_stub = types.ModuleType('wren')
_wren_stub.__path__ = [str(Path(__file__).resolve().parent.parent.parent.parent / 'wren')]
_wren_stub.__file__ = str(_wren_stub.__path__[0] / '__init__.py')

# Only set if not already present (avoids override in subprocess tests)
if 'wren' not in sys.modules:
    sys.modules['wren'] = _wren_stub

# Ensure the project root is on sys.path so wren packages resolve
_project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
