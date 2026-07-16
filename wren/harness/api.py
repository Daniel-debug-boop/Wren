"""HTTP API server for the harness orchestrator.

FastAPI-based with endpoints for:
  - POST /goal         Process a goal
  - GET  /status       Orchestrator status
  - GET  /health       Full health check
  - GET  /children     List active children
  - POST /children     Spawn a child agent
  - GET  /bus/stats    Message bus statistics
  - GET  /bus/dead     Dead-letter queue
  - GET  /metrics      Prometheus-format metrics
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any

from wren.harness.meta_orchestrator import MetaOrchestrator
from wren.harness.config import HarnessConfig as Cfg
from wren.harness.telemetry import T

_logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """Simple in-memory rate-limiter that adds X-RateLimit-* headers.

    Uses a sliding-window counter per client IP.  Default: 100 req / 60 s.
    """

    def __init__(self, limit: int = 100, window_s: float = 60.0) -> None:
        self._limit = limit
        self._window_s = window_s
        self._counts: dict[str, list[float]] = defaultdict(list)

    def check(self, client_ip: str) -> dict[str, str]:
        now = time.time()
        cutoff = now - self._window_s
        self._counts[client_ip] = [t for t in self._counts[client_ip] if t > cutoff]
        count = len(self._counts[client_ip])
        remaining = max(0, self._limit - count)
        reset_ts = int(now + self._window_s)
        self._counts[client_ip].append(now)
        return {
            'X-RateLimit-Limit': str(self._limit),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(reset_ts),
        }


class HarnessAPI:
    """HTTP API wrapper around MetaOrchestrator.

    Exposes FastAPI endpoints. Run with:
        await api.run()   # starts uvicorn
    """

    def __init__(self, config: Cfg | None = None) -> None:
        self._cfg = config or Cfg.load()
        self._orch = MetaOrchestrator('api', config=self._cfg)
        self._app = None
        self._rate_limiter = RateLimitMiddleware(
            limit=self._cfg.api_rate_limit, window_s=self._cfg.api_rate_window_s
        )

    def _rate_headers(self) -> dict[str, str]:
        return self._rate_limiter.check('127.0.0.1')

    def _build_app(self):
        """Build FastAPI app with all routes."""
        from fastapi import FastAPI, HTTPException, Response
        from pydantic import BaseModel

        app = FastAPI(
            title='OpenHands Harness API',
            version='2.0.0',
            description='Meta-Orchestrator for child agent management',
        )

        class GoalRequest(BaseModel):
            goal: str

        class SpawnRequest(BaseModel):
            agent_type: str
            task_desc: str = ''

        orch = self._orch
        _rate_headers = self._rate_headers  # noqa: F841

        @app.on_event('startup')
        async def startup():
            await orch.start()

        @app.on_event('shutdown')
        async def shutdown():
            await orch.shutdown()

        @app.post('/goal')
        async def process_goal(req: GoalRequest) -> dict[str, Any]:
            try:
                result = await orch.process_goal(req.goal)
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get('/status')
        async def status() -> dict[str, Any]:
            return orch.status()

        @app.get('/health')
        async def health() -> dict[str, Any]:
            return orch.health_check()

        @app.get('/children')
        async def list_children() -> list[dict[str, Any]]:
            return [h.to_dict() for h in orch.list_children()]

        @app.post('/children')
        async def spawn_child(req: SpawnRequest) -> dict[str, Any]:
            handle = await orch.spawn_agent(req.agent_type, req.task_desc)
            return handle.to_dict()

        @app.delete('/children/{agent_id}')
        async def kill_child(agent_id: str) -> dict[str, str]:
            await orch.kill_agent(agent_id)
            return {'status': 'killed', 'agent_id': agent_id}

        @app.get('/bus/stats')
        async def bus_stats() -> dict[str, Any]:
            return orch._bus.stats()

        @app.get('/bus/dead')
        async def dead_letter() -> list[dict[str, Any]]:
            return orch._bus.dead_letter_queue()

        @app.get('/metrics', response_class=Response)
        async def metrics() -> Response:
            s = orch._state
            body = (
                '# HELP harness_goals_processed Total goals processed\n'
                '# TYPE harness_goals_processed counter\n'
                f'harness_goals_processed {s.goals_processed}\n'
                '# HELP harness_children_spawned Total child agents spawned\n'
                '# TYPE harness_children_spawned counter\n'
                f'harness_children_spawned {s.children_spawned}\n'
                '# HELP harness_children_completed Children that completed successfully\n'
                '# TYPE harness_children_completed counter\n'
                f'harness_children_completed {s.children_completed}\n'
                '# HELP harness_children_failed Children that failed\n'
                '# TYPE harness_children_failed counter\n'
                f'harness_children_failed {s.children_failed}\n'
                '# HELP harness_errors Total orchestration errors\n'
                '# TYPE harness_errors counter\n'
                f'harness_errors {s.errors}\n'
                '# HELP harness_uptime_seconds Seconds since orchestrator start\n'
                '# TYPE harness_uptime_seconds gauge\n'
                f'harness_uptime_seconds {time.time() - s.started_at}\n'
            )
            return Response(content=body, media_type='text/plain; charset=utf-8')

        self._app = app

    async def run(self) -> None:
        """Start the API server."""
        self._build_app()
        host = self._cfg.api_host
        port = int(self._cfg.api_port)

        _logger.info('HarnessAPI: starting on %s:%s', host, port)
        T.info('api.start', f'host={host} port={port}')

        import uvicorn

        config = uvicorn.Config(self._app, host=host, port=port, log_level='info')
        server = uvicorn.Server(config)
        await server.serve()
