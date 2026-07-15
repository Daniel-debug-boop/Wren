"""Configuration loader — YAML file + environment variable overrides.

Uses stdlib json/tomllib if available; falls back to environment
variables only. The canonical path is OPENHANDS_HARNESS_CONFIG or
./harness.yaml.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from wren.harness.resource_budget import BudgetLimit


@dataclass
class HarnessConfig:
    budget_limits: BudgetLimit = field(default_factory=BudgetLimit)
    max_concurrent_children: int = 10
    child_timeout_s: float = 300.0
    vector_persist_path: str = '/tmp/wren/harness_vectors.json'
    auto_start_bus: bool = True
    auto_start_dark_factory: bool = True
    enable_hitl: bool = True
    hitl_timeout_s: float = 300.0
    db_path: str = '/tmp/wren/harness.db'
    auth_secret: str = ''
    bus_rate_limit: int = 100
    log_level: str = 'INFO'
    api_host: str = '127.0.0.1'
    api_port: int = 8750
    api_rate_limit: int = 100
    api_rate_window_s: float = 60.0
    telemetry_enabled: bool = True

    @classmethod
    def load(cls, path: str = '') -> HarnessConfig:
        """Load config from file, fallback to env vars, then defaults.

        Tries:
          1. Path from OPENHANDS_HARNESS_CONFIG env var
          2. Path argument
          3. ./harness.yaml
          4. ./config/harness.yaml
          5. Pure env vars
        """
        paths = [
            os.environ.get('OPENHANDS_HARNESS_CONFIG', ''),
            path,
            './harness.yaml',
            './harness.json',
            './config/harness.yaml',
        ]
        data: dict[str, Any] = {}

        for p in paths:
            if not p:
                continue
            try:
                with open(p) as f:
                    if p.endswith('.json'):
                        data = json.load(f)
                    else:
                        import yaml

                        data = yaml.safe_load(f) or {}
                break
            except (FileNotFoundError, ImportError):
                continue
            except Exception:
                continue

        # Env var overrides
        env_overrides = {
            'db_path': 'OPENHANDS_HARNESS_DB_PATH',
            'auth_secret': 'OPENHANDS_HARNESS_AUTH_SECRET',
            'log_level': 'OPENHANDS_HARNESS_LOG_LEVEL',
            'api_host': 'OPENHANDS_HARNESS_API_HOST',
            'api_port': 'OPENHANDS_HARNESS_API_PORT',
            'api_rate_limit': 'OPENHANDS_HARNESS_API_RATE_LIMIT',
            'api_rate_window_s': 'OPENHANDS_HARNESS_API_RATE_WINDOW_S',
        }
        for key, env_key in env_overrides.items():
            val = os.environ.get(env_key)
            if val is not None:
                data[key] = val

        cfg = cls()
        for key, val in data.items():
            if hasattr(cfg, key) and val is not None:
                setattr(cfg, key, val)

        # Parse budget_limits if provided as dict
        budget_dict = data.get('budget_limits', {})
        if isinstance(budget_dict, dict):
            cfg.budget_limits = BudgetLimit(
                max_tokens=budget_dict.get('max_tokens', 100000),
                max_memory_mb=budget_dict.get('max_memory_mb', 512),
                max_time_s=budget_dict.get('max_time_s', 600),
                max_concurrent_agents=budget_dict.get('max_concurrent_agents', 5),
            )

        return cfg

    def to_dict(self) -> dict[str, Any]:
        return {
            'max_concurrent_children': self.max_concurrent_children,
            'child_timeout_s': self.child_timeout_s,
            'budget': {
                'max_tokens': self.budget_limits.max_tokens,
                'max_memory_mb': self.budget_limits.max_memory_mb,
                'max_time_s': self.budget_limits.max_time_s,
            },
            'db_path': self.db_path,
            'api_host': self.api_host,
            'api_port': self.api_port,
            'log_level': self.log_level,
        }
