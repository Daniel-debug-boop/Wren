"""Resilience Manager — 3 independent layers of protection.

Layer 1: Circuit Breaker (whole provider)
  Stops hammering a provider that's failing upstream; auto-probes to recover.

Layer 2: Connection Cooldown (one account/key)
  Skips a rate-limited key while other keys keep serving.

Layer 3: Model Lockout (provider + model)
  Quarantines just one quota-limited model, not the whole connection.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

_logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerState:
    """State for a circuit breaker."""
    failures: int = 0
    last_failure_time: float = 0.0
    state: str = "closed"  # closed, open, half-open
    open_until: float = 0.0
    recovery_probe_interval_s: float = 30.0


@dataclass
class CooldownState:
    """State for a cooldown entry."""
    cooldown_until: float = 0.0
    reason: str = ""
    consecutive_rate_limits: int = 0


@dataclass
class LockoutState:
    """State for a model lockout."""
    locked_until: float = 0.0
    reason: str = ""
    is_quota_limit: bool = False


class ResilienceManager:
    """3-layer resilience: circuit breaker, cooldown, model lockout.

    Auto-protects against provider failures, rate limits, and
    quota exhaustion. Self-healing with recovery probes.
    """

    def __init__(self) -> None:
        # Layer 1: Circuit breakers (provider-level)
        self._circuit_breakers: dict[str, CircuitBreakerState] = {}

        # Layer 2: Connection cooldowns (per API key)
        self._cooldowns: dict[str, CooldownState] = {}

        # Layer 3: Model lockouts (provider + model)
        self._lockouts: dict[str, LockoutState] = {}

        # Configuration
        self._circuit_breaker_threshold = 5  # failures before open
        self._cooldown_duration_s = 60.0  # default cooldown
        self._lockout_duration_s = 120.0  # default lockout
        self._recovery_probe_interval_s = 30.0

    # ═══════════════════════════════════════════════════════════════
    #  LAYER 1 — CIRCUIT BREAKER (whole provider)
    # ═══════════════════════════════════════════════════════════════

    def record_provider_failure(self, provider: str) -> None:
        """Record a failure for a provider's circuit breaker.

        After threshold failures, the circuit opens and stops
        requests for recovery_probe_interval_s.
        """
        cb = self._circuit_breakers.setdefault(provider, CircuitBreakerState())
        cb.failures += 1
        cb.last_failure_time = time.time()

        if cb.failures >= self._circuit_breaker_threshold and cb.state == "closed":
            cb.state = "open"
            cb.open_until = time.time() + self._recovery_probe_interval_s
            _logger.warning(
                "Circuit breaker OPEN for provider %s "
                "(failures=%d, recovery_in=%.0fs)",
                provider, cb.failures, self._recovery_probe_interval_s,
            )

    def record_provider_success(self, provider: str) -> None:
        """Record a success — resets the circuit breaker."""
        cb = self._circuit_breakers.get(provider)
        if cb:
            cb.failures = 0
            if cb.state == "half-open":
                cb.state = "closed"
                _logger.info("Circuit breaker CLOSED for provider %s", provider)

    def is_provider_available(self, provider: str) -> bool:
        """Check if a provider is available (circuit not open).

        Auto-transitions from open → half-open when recovery
        probe interval expires.
        """
        cb = self._circuit_breakers.get(provider)
        if not cb:
            return True

        if cb.state == "closed":
            return True

        if cb.state == "open":
            # Check if recovery interval has passed
            if time.time() >= cb.open_until:
                cb.state = "half-open"
                _logger.info(
                    "Circuit breaker HALF-OPEN for provider %s — probing",
                    provider,
                )
                return True
            return False

        # half-open: allow one request through (the probe)
        return True

    # ═══════════════════════════════════════════════════════════════
    #  LAYER 2 — CONNECTION COOLDOWN (per API key)
    # ═══════════════════════════════════════════════════════════════

    def rate_limit_hit(self, api_key_hash: str, reason: str = "") -> None:
        """Put an API key into cooldown after rate limiting."""
        cd = self._cooldowns.setdefault(api_key_hash, CooldownState())
        cd.cooldown_until = time.time() + self._cooldown_duration_s
        cd.reason = reason
        cd.consecutive_rate_limits += 1

        # Exponential backoff for repeated rate limits
        if cd.consecutive_rate_limits > 1:
            backoff = self._cooldown_duration_s * (2 ** (cd.consecutive_rate_limits - 1))
            cd.cooldown_until = time.time() + min(backoff, 600.0)  # max 10min

        _logger.info(
            "Connection cooldown for api_key=%s (%.0fs): %s",
            api_key_hash[:8],
            cd.cooldown_until - time.time(),
            reason,
        )

    def is_key_available(self, api_key_hash: str) -> bool:
        """Check if an API key is available (not in cooldown)."""
        cd = self._cooldowns.get(api_key_hash)
        if not cd:
            return True
        if time.time() >= cd.cooldown_until:
            # Cooldown expired
            del self._cooldowns[api_key_hash]
            return True
        return False

    # ═══════════════════════════════════════════════════════════════
    #  LAYER 3 — MODEL LOCKOUT (provider + model)
    # ═══════════════════════════════════════════════════════════════

    def lockout_model(self, provider: str, model: str, reason: str = "") -> None:
        """Lock out a specific model on a provider.

        Useful when a model's quota is exhausted but other models
        from the same provider still work.
        """
        key = f"{provider}:{model}"
        lo = self._lockouts.setdefault(key, LockoutState())
        lo.locked_until = time.time() + self._lockout_duration_s
        lo.reason = reason
        lo.is_quota_limit = "quota" in reason.lower()

        _logger.info(
            "Model lockout for %s/%s (%.0fs): %s",
            provider, model,
            self._lockout_duration_s, reason,
        )

    def is_model_available(self, provider: str, model: str) -> bool:
        """Check if a provider+model is available (not locked out)."""
        key = f"{provider}:{model}"
        lo = self._lockouts.get(key)
        if not lo:
            return True
        if time.time() >= lo.locked_until:
            del self._lockouts[key]
            return True
        return False

    # ═══════════════════════════════════════════════════════════════
    #  COMPOSITE CHECKS
    # ═══════════════════════════════════════════════════════════════

    def is_available(self, provider: str, model: str,
                     api_key_hash: str = "") -> tuple[bool, str]:
        """Composite check: is this provider+model+key available?

        Returns (available, reason_if_unavailable).
        """
        # Layer 1: Circuit breaker
        if not self.is_provider_available(provider):
            return False, f"Circuit breaker open for {provider}"

        # Layer 3: Model lockout
        if not self.is_model_available(provider, model):
            return False, f"Model {model} locked out on {provider}"

        # Layer 2: Key cooldown
        if api_key_hash and not self.is_key_available(api_key_hash):
            return False, f"API key in cooldown for {provider}"

        return True, ""

    def get_unavailable_providers(self) -> list[dict[str, Any]]:
        """Get list of all unavailable providers with reasons."""
        unavailable = []

        for provider, cb in self._circuit_breakers.items():
            if cb.state != "closed":
                unavailable.append({
                    "provider": provider,
                    "layer": "circuit_breaker",
                    "state": cb.state,
                    "failures": cb.failures,
                    "recovery_in_s": max(0, cb.open_until - time.time()),
                })

        return unavailable

    def get_active_lockouts(self) -> list[dict[str, Any]]:
        """Get all active model lockouts."""
        active = []
        now = time.time()
        for key, lo in self._lockouts.items():
            if now < lo.locked_until:
                provider, model = key.split(":", 1)
                active.append({
                    "provider": provider,
                    "model": model,
                    "reason": lo.reason,
                    "expires_in_s": lo.locked_until - now,
                })
        return active

    def get_active_cooldowns(self) -> list[dict[str, Any]]:
        """Get all active API key cooldowns."""
        active = []
        now = time.time()
        for key_hash, cd in self._cooldowns.items():
            if now < cd.cooldown_until:
                active.append({
                    "key_hash": key_hash[:8],
                    "reason": cd.reason,
                    "expires_in_s": cd.cooldown_until - now,
                })
        return active

    def stats(self) -> dict[str, Any]:
        """Get resilience system stats."""
        return {
            "circuit_breakers": {
                "total": len(self._circuit_breakers),
                "open": sum(
                    1 for cb in self._circuit_breakers.values()
                    if cb.state == "open"
                ),
                "half_open": sum(
                    1 for cb in self._circuit_breakers.values()
                    if cb.state == "half-open"
                ),
            },
            "active_cooldowns": len(self.get_active_cooldowns()),
            "active_lockouts": len(self.get_active_lockouts()),
        }
