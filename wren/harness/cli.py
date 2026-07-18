#!/usr/bin/env python3
"""CLI entry point for the harness orchestrator.

Usage:
    python3 -m wren.harness.cli --goal "Build a web app"
    python3 -m wren.harness.cli serve              # HTTP API mode
    python3 -m wren.harness.cli health              # Health check
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time

from wren.harness.meta_orchestrator import MetaOrchestrator
from wren.harness.config import HarnessConfig as Cfg
# from wren.harness.telemetry import T  # noqa: F401
from wren.harness.health import HealthChecker


def _setup_logging(level: str = 'INFO') -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        stream=sys.stderr,
    )


async def _run_goal(cfg: Cfg, goal: str) -> None:
    orch = MetaOrchestrator('cli', config=cfg)
    try:
        await orch.start()
        result = await orch.process_goal(goal)
        print('\n=== RESULT ===')
        print(f'Goal:         {goal[:80]}')
        print(f'Tasks:        {result.get("task_count", 0)}')
        print(
            f'Children:     {result.get("children_spawned", 0)} spawned, '
            f'{result.get("children_completed", 0)} completed'
        )
        print(f'Reflection:   passed={result.get("reflection", {}).get("passed", "?")}')
        print(f'Duration:     {round(time.time() - orch._state.started_at, 1)}s')
    finally:
        await orch.shutdown()


async def _run_serve(cfg: Cfg) -> None:
    """Run HTTP API server."""
    try:
        from wren.harness.api import HarnessAPI

        api = HarnessAPI(config=cfg)
        await api.run()
    except ImportError as e:
        print(f'Cannot start API server: {e}', file=sys.stderr)
        print(
            'Install dependencies: pip install "fastapi[standard]" uvicorn',
            file=sys.stderr,
        )
        sys.exit(1)


async def _run_health(verbose: bool = False) -> None:
    hc = HealthChecker()
    report = hc.check_all()
    d = report.to_dict()
    print(f'Status:  {d["status"]}')
    print(f'Version: {d["version"]}')
    print(f'Uptime:  {d["uptime_s"]}s')
    if verbose:
        for name, check in d.get('checks', {}).items():
            status = check.get('status', '?')
            print(f'  {name}: {status}')
    sys.exit(0 if d['status'] == 'healthy' else 1)


def main() -> None:
    parser = argparse.ArgumentParser(description='OpenHands Harness Orchestrator')
    parser.add_argument('--config', default='', help='Path to YAML config file')
    parser.add_argument(
        '--log-level', default='', help='Log level (DEBUG/INFO/WARN/ERROR)'
    )

    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('health', help='Run health check')

    goal_parser = sub.add_parser('goal', help='Process a goal')
    goal_parser.add_argument('goal', help='Goal description')

    serve_parser = sub.add_parser('serve', help='Start HTTP API server')
    serve_parser.add_argument('--host', default='', help='Bind address')
    serve_parser.add_argument('--port', type=int, default=0, help='Bind port')

    args = parser.parse_args()
    cfg = Cfg.load(args.config)

    if args.log_level:
        cfg.log_level = args.log_level
    _setup_logging(cfg.log_level)

    if args.command == 'health':
        asyncio.run(_run_health(verbose=True))
    elif args.command == 'goal':
        asyncio.run(_run_goal(cfg, args.goal))
    elif args.command == 'serve':
        if args.host:
            cfg.api_host = args.host
        if args.port:
            cfg.api_port = args.port
        asyncio.run(_run_serve(cfg))


if __name__ == '__main__':
    main()
