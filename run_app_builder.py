#!/usr/bin/env python3
"""
WREN APP BUILDER — Standalone CLI Runner

A production-grade agentic wrapper that converts high-level project specs into
fully realized, multi-file software projects by chaining API calls to an LLM.

Features:
  - Zero external dependencies (pure Python stdlib)
  - 3-stage pipeline: Blueprint → Generate → Validate & Correct
  - Graceful shutdown on Ctrl+C / SIGTERM
  - State persistence for crash recovery / resume
  - Colorized terminal output
  - Works with any OpenAI-compatible API (OpenAI, OpenRouter, local, etc.)

Usage:
  python run_app_builder.py --prompt "Build a 3D solar system explorer" --api-key "sk-..."
  python run_app_builder.py -p "Todo app" -k "sk-..." -o ./my-project
  python run_app_builder.py -p "Portfolio" -k "sk-..." --base-url "https://openrouter.ai/api/v1"

Environment variables (can be used instead of CLI args):
  LLM_API_KEY    — API key
  LLM_MODEL      — Model name (default: gpt-4o)
  LLM_BASE_URL   — Custom API base URL
"""

import os
import signal
import sys
import types

# ═════════════════════════════════════════════════════════════════════════════
#  Early exit for --help / -h (before any imports)
# ═════════════════════════════════════════════════════════════════════════════

if '--help' in sys.argv or '-h' in sys.argv:
    print(r"""
╔══════════════════════════════════════════════════════════════╗
║           WREN APP BUILDER — Automated Project             ║
║           Generation Pipeline CLI                           ║
╚══════════════════════════════════════════════════════════════╝

Converts a high-level description into a complete, multi-file project
using a 3-stage LLM-driven pipeline with zero external dependencies.

USAGE:
  python run_app_builder.py --prompt "<description>" --api-key "<key>" [options]

REQUIRED:
  --prompt, -p   Project description (e.g., "Build a 3D portfolio site")
  --api-key, -k  LLM API key (e.g., OpenAI sk-... or OpenRouter key)

OPTIONS:
  --model, -m       LLM model name                     [default: gpt-4o]
  --base-url        Custom API base URL                [default: OpenAI]
  --output, -o      Output directory                   [default: ./wren-generations]
  --no-validate     Skip validation & correction stage
  --no-resume       Do not resume from saved state

ENVIRONMENT VARIABLES:
  LLM_API_KEY    Alternative to --api-key
  LLM_MODEL      Alternative to --model
  LLM_BASE_URL   Alternative to --base-url

EXAMPLES:
  python run_app_builder.py \\
    --prompt "Build a 3D solar system explorer with Three.js" \\
    --api-key "sk-..." \\
    --output ./solar-system

  python run_app_builder.py \\
    -p "Full-stack todo app with React + FastAPI + SQLite" \\
    -k "sk-..." \\
    -o ./todo-app \\
    --no-validate

  # Using OpenRouter free tier
  python run_app_builder.py \\
    -p "Portfolio website with dark mode" \\
    -k "sk-or-..." \\
    --base-url "https://openrouter.ai/api/v1" \\
    --model "openrouter/free"

REQUIREMENTS:
  Python 3.12+ with NO external packages — uses only stdlib (urllib + asyncio)
""")
    sys.exit(0)

# ═════════════════════════════════════════════════════════════════════════════
#  Module stub setup — bypass wren/__init__.py heavy deps (pydantic, fastapi)
# ═════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = SCRIPT_DIR  # run_app_builder.py is at project root
WREN_DIR = os.path.join(PROJECT_ROOT, 'wren')

# Ensure project root is in path so 'from wren.app_builder...' can find wren/
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Create module stub — prevents wren/__init__.py from executing its imports
# The stub's __path__ points to the real wren/ directory so submodules load correctly
if 'wren' not in sys.modules:
    _wren_stub = types.ModuleType('wren')
    _wren_stub.__path__ = [WREN_DIR]
    _wren_stub.__file__ = os.path.join(WREN_DIR, '__init__.py')
    sys.modules['wren'] = _wren_stub

# ═════════════════════════════════════════════════════════════════════════════
#  Import the pipeline
# ═════════════════════════════════════════════════════════════════════════════

try:
    import asyncio
    from wren.app_builder.automated_runner import (
        run_pipeline,
        AutomatedProjectGenerator,
        ProjectResult,
    )
    from wren.app_builder.llm_client import LLMClient
except ImportError as exc:
    print(f"  ❌ Import error: {exc}", file=sys.stderr)
    print("", file=sys.stderr)
    print("  Make sure you're running from the project root directory:", file=sys.stderr)
    print(f"    cd {PROJECT_ROOT}", file=sys.stderr)
    print("  The expected structure is:", file=sys.stderr)
    print("    ./run_app_builder.py", file=sys.stderr)
    print("    ./wren/app_builder/", file=sys.stderr)
    sys.exit(1)

# ═════════════════════════════════════════════════════════════════════════════
#  Graceful shutdown handler
# ═════════════════════════════════════════════════════════════════════════════

_shutdown_requested = False
_running_tasks: list[asyncio.Task] = []


def _handle_signal(signum: int, frame) -> None:
    """Handle SIGINT (Ctrl+C) and SIGTERM gracefully."""
    global _shutdown_requested
    if _shutdown_requested:
        # Second signal → force quit
        print("\n  ⚡ Forced exit.", file=sys.stderr)
        sys.exit(1)
    _shutdown_requested = True
    print("\n  ⏳ Shutdown requested — finishing current file... (press Ctrl+C again to force)", file=sys.stderr)
    # Cancel all running tasks
    for task in _running_tasks:
        task.cancel()


# ═════════════════════════════════════════════════════════════════════════════
#  Main entry point
# ═════════════════════════════════════════════════════════════════════════════


def main() -> None:
    """Parse arguments and run the generation pipeline."""
    import argparse

    # ── Parse arguments ────────────────────────────────────────
    parser = argparse.ArgumentParser(
        description="Wren Automated Multi-File Project Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # We handle --help ourselves above
    )
    parser.add_argument("--prompt", "-p", default=None, help="Project description")
    parser.add_argument("--api-key", "-k", default=None, help="LLM API key")
    parser.add_argument("--model", "-m", default=None, help="LLM model name")
    parser.add_argument("--base-url", default=None, help="Custom API base URL")
    parser.add_argument("--output", "-o", default=None, help="Output directory")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation")
    parser.add_argument("--no-resume", action="store_true", help="Don't resume from state")

    args = parser.parse_args()

    # ── Resolve configuration (CLI args > env vars > defaults) ──
    api_key = args.api_key or os.environ.get("LLM_API_KEY") or ""
    prompt = args.prompt or ""
    model = args.model or os.environ.get("LLM_MODEL") or "gpt-4o"
    base_url = args.base_url or os.environ.get("LLM_BASE_URL") or None
    output = args.output or "./wren-generations"

    # Validate required arguments
    if not prompt:
        print("  ❌ Error: --prompt is required", file=sys.stderr)
        print("  Usage: python run_app_builder.py --prompt '<description>' --api-key '<key>'", file=sys.stderr)
        sys.exit(1)

    if not api_key:
        print("  ❌ Error: --api-key is required", file=sys.stderr)
        print("  Set it via --api-key or the LLM_API_KEY environment variable.", file=sys.stderr)
        sys.exit(1)

    if not model:
        model = "gpt-4o"

    # ── Register signal handlers for graceful shutdown ─────────
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    # ── Run the pipeline ───────────────────────────────────────
    async def _run() -> int:
        global _running_tasks

        runner = AutomatedProjectGenerator(
            api_key=api_key,
            model=model,
            base_url=base_url,
            output_dir=output,
            validate=not args.no_validate,
            resume=not args.no_resume,
        )

        main_task = asyncio.create_task(runner.run(prompt))
        _running_tasks.append(main_task)

        try:
            result = await main_task
        except asyncio.CancelledError:
            print("\n  ⚠️  Pipeline cancelled by user.", file=sys.stderr)
            return 130
        except KeyboardInterrupt:
            print("\n  ⚠️  Interrupted by user.", file=sys.stderr)
            return 130
        except Exception as exc:
            print(f"\n  ❌ Pipeline failed: {exc}", file=sys.stderr)
            return 1
        finally:
            try:
                await runner.close()
            except Exception:
                pass

        return 0 if result.success else 1

    exit_code = asyncio.run(_run())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
