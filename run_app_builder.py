#!/usr/bin/env python3
"""
Standalone runner for Wren App Builder CLI.

This bypasses the wren/__init__.py import chain (which needs pydantic, fastapi, etc.)
by patching sys.modules before the wren package is loaded.
"""
import sys
import types
import os

# Show --help even without httpx
if '--help' in sys.argv or '-h' in sys.argv:
    print("""
╔══════════════════════════════════════════════════════════════╗
║           WREN APP BUILDER — CLI Runner                    ║
╚══════════════════════════════════════════════════════════════╝

USAGE:
  python run_app_builder.py --prompt "<description>" --api-key "<key>" [options]

ARGS:
  --prompt, -p   High-level project description (e.g., "Build a 3D portfolio site")
  --api-key, -k  LLM API key (e.g., OpenAI sk-...)
  --model, -m    LLM model name (default: gpt-4o)
  --base-url     Custom API base URL (default: OpenAI)
  --output, -o   Output directory (default: ./wren-generations)
  --no-validate  Skip validation & correction stage
  --no-resume    Do not resume from saved state

EXAMPLES:
  python run_app_builder.py -p "Build a 3D solar system explorer" -k "sk-..."
  python run_app_builder.py -p "Todo app with Firebase auth" -k "sk-..." -o ./my-project

REQUIREMENTS:
  None! Uses only Python stdlib (urllib + asyncio)
""")
    sys.exit(0)

# Add the wren directory to sys.path so app_builder can be found
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WREN_DIR = os.path.join(SCRIPT_DIR, 'wren')
sys.path.insert(0, WREN_DIR)

# Create a minimal wren module stub — prevents wren/__init__.py from executing
# This is needed because wren/__init__.py imports many heavy dependencies (pydantic, etc.)
# that aren't needed just for the app_builder module.
wren_stub = types.ModuleType('wren')
wren_stub.__path__ = [WREN_DIR]
wren_stub.__file__ = os.path.join(WREN_DIR, '__init__.py')
sys.modules['wren'] = wren_stub

# No external deps needed — llm_client.py now uses only stdlib (urllib)
# Now import the CLI — only triggers app_builder submodules, not wren/__init__.py
from wren.app_builder.automated_runner import main

if __name__ == '__main__':
    main()
