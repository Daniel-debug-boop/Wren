"""Quota Share Manager — distributes provider quota fairly across API keys.

When a user has multiple API keys for the same provider, Quota-Share
distributes the provider's time-based quota fairly across all keys.
Work-conserving: idle keys lend their slice to active ones.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

_logger = logging.getLogger(__name__)


@dataclass
class KeyQuota:
    """Quota state for a single API key."""
    key_hash: str
    provider: str
    allocation_weight: float = 1.0  # Share of pool (e.g., 50 / 30 / 20)
    tokens_used_5h: int = 0
    tokens_used_7d: int = 0
    requests_5h: int = 0
    cost_5h: float = 0.0
    is_active: bool = True
    last_used: float = 0.0
    cap_tokens: int = 0  # 0 = unlimited


@dataclass
class QuotaPool:
    """A pool of keys for one provider."""
    provider: str
    keys: dict[str, KeyQuota] = field(default_factory=dict)


class QuotaShareManager:
    """Fair quota distribution across multiple API keys.

    Automatically distributes load across keys in a pool.
    Work-conserving: idle keys lend their slice to busy ones.
    """

    def __init__(self) -> None:
        self._pools: dict[str, QuotaPool] = {}  # provider -> pool
        self._window_start_5h: float = time.time()
        self._window_start_7d: float = time.time()

    def register_key(self, provider: str, api_key_hash: str,
                     weight: float = 1.0, cap: int = 0) -> None:
        """Register an API key for quota sharing."""
        pool = self._pools.setdefault(provider, QuotaPool(provider=provider))
        pool.keys[api_key_hash] = KeyQuota(
            key_hash=api_key_hash,
            provider=provider,
            allocation_weight=weight,
            cap_tokens=cap,
        )
        _logger.debug("QuotaShare: registered key %s for %s (weight=%.1f)",
                      api_key_hash[:8], provider, weight)

    def select_best_key(self, provider: str, tokens_needed: int = 0) -> str | None:
        """Select the best API key for a given provider.

        Picks the key with the most remaining quota and availability.
        """
        pool = self._pools.get(provider)
        if not pool or not pool.keys:
            return None

        # Reset windows if needed
        self._rotate_windows()

        # Score each key
        best_key = None
        best_score = -1.0

        for key_hash, quota in pool.keys.items():
            if not quota.is_active:
                continue

            # Check caps
            if quota.cap_tokens > 0 and quota.tokens_used_5h >= quota.cap_tokens:
                continue

            # Score: available weight * inverse usage
            usage_ratio = quota.tokens_used_5h / max(1, quota.cap_tokens) if quota.cap_tokens > 0 else 0
            score = quota.allocation_weight * (1.0 - usage_ratio)

            # Boost for recently used (session stickiness)
            if quota.last_used > 0:
                recency = max(0, 1.0 - (time.time() - quota.last_used) / 300)
                score += recency * 0.2

            if score > best_score:
                best_score = score
                best_key = key_hash

        return best_key

    def record_usage(self, provider: str, api_key_hash: str,
                     tokens: int, cost: float = 0.0) -> None:
        """Record token usage for a key."""
        pool = self._pools.get(provider)
        if not pool:
            return

        quota = pool.keys.get(api_key_hash)
        if not quota:
            return

        quota.tokens_used_5h += tokens
        quota.tokens_used_7d += tokens
        quota.requests_5h += 1
        quota.cost_5h += cost
        quota.last_used = time.time()

    def _rotate_windows(self) -> None:
        """Rotate time windows when they expire."""
        now = time.time()

        # 5-hour window
        if now - self._window_start_5h > 18000:  # 5 hours
            self._window_start_5h = now
            for pool in self._pools.values():
                for quota in pool.keys.values():
                    quota.tokens_used_5h = 0
                    quota.requests_5h = 0
                    quota.cost_5h = 0

        # 7-day window
        if now - self._window_start_7d > 604800:  # 7 days
            self._window_start_7d = now
            for pool in self._pools.values():
                for quota in pool.keys.values():
                    quota.tokens_used_7d = 0

    def get_pool_status(self, provider: str) -> dict[str, Any] | None:
        """Get quota status for all keys in a pool."""
        pool = self._pools.get(provider)
        if not pool:
            return None

        return {
            "provider": provider,
            "total_keys": len(pool.keys),
            "active_keys": sum(1 for k in pool.keys.values() if k.is_active),
            "keys": [
                {
                    "key_hash": q.key_hash[:8],
                    "weight": q.allocation_weight,
                    "tokens_used_5h": q.tokens_used_5h,
                    "cap": q.cap_tokens,
                    "last_used": q.last_used,
                    "is_active": q.is_active,
                }
                for q in pool.keys.values()
            ],
            "window_5h_remaining_s": max(0, 18000 - (time.time() - self._window_start_5h)),
        }

    def remove_key(self, provider: str, api_key_hash: str) -> bool:
        """Remove an API key from quota sharing."""
        pool = self._pools.get(provider)
        if pool and api_key_hash in pool.keys:
            del pool.keys[api_key_hash]
            return True
        return False

    def stats(self) -> dict[str, Any]:
        """Get quota share system stats."""
        return {
            "pools": len(self._pools),
            "total_keys": sum(len(p.keys) for p in self._pools.values()),
            "active_pools": [
                {
                    "provider": p.provider,
                    "keys": len(p.keys),
                }
                for p in self._pools.values()
            ],
        }
