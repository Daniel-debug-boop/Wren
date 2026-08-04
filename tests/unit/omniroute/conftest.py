"""Pytest fixtures and configuration for OmniRoute tests.

This conftest imports the real ``wren`` package at load time so every
test module can ``from wren import ...``. ``wren/__init__.py`` is fully
lazy (heavy deps load on attribute access), so importing it is cheap.
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so wren packages resolve
_project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Import the real (lazy) wren package instead of a bare module stub.
# A stub without the lazy ``__getattr__`` from wren/__init__.py poisons
# ``sys.modules['wren']`` for every other test directory in the same
# session (e.g. ``from wren import Event`` starts failing in app_server
# tests once this conftest has been loaded first).
if 'wren' not in sys.modules:
    import wren  # noqa: F401
