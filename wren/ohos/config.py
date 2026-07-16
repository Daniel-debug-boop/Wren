"""Global configuration for the Wren Orchestration System (OHOS).

All settings are hardcoded with sensible defaults. No env-var gating —
OHOS is always active.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OHOSConfig:
    """Singleton configuration. Import the module-level CONFIG instance."""

    # ── Auto-mode engine ──────────────────────────────────────────
    auto_mode_enabled: bool = True
    """Always true. OHOS never sleeps."""

    max_concurrent_sub_tasks: int = 5
    """How many sub-tasks can run in parallel."""

    sub_task_timeout_s: int = 600
    """Max seconds a sub-task may run before forced abort."""

    # ── Goal detection ────────────────────────────────────────────
    goal_detection_threshold: float = 2.0
    """Score threshold to auto-activate manager mode (lower = more aggressive)."""

    auto_decompose_on_detect: bool = True
    """Auto-decompose complex goals into sub-tasks without asking."""

    # ── Error recovery ────────────────────────────────────────────
    max_retries_per_error: int = 5
    """How many mutation levels to try before giving up."""

    auto_retry_all_errors: bool = True
    """Wrap every agent action with the adaptive retry loop."""

    error_solutions_path: str = '.wren/error_solutions.json'
    """Where winning strategies are persisted."""

    # ── Tool discovery ────────────────────────────────────────────
    auto_discover_tools: bool = True
    """Scan for missing capabilities and auto-install."""

    discovery_max_per_conversation: int = 10
    """Max auto-installs per conversation to avoid runaway."""

    # ── Reflection ────────────────────────────────────────────────
    auto_reflect_on_complete: bool = True
    """Run self-reflection every time a sub-task completes."""

    auto_reflect_on_error: bool = True
    """Run self-reflection on fatal errors."""

    reflection_max_lessons: int = 50
    """Trim working-memory lessons to this many entries."""

    # ── Circuit breaker ───────────────────────────────────────────
    circuit_breaker_failure_threshold: int = 7
    """Consecutive failures before the breaker trips for an operation type."""

    circuit_breaker_reset_timeout_s: int = 120
    """Seconds before a tripped breaker resets to half-open."""

    # ── Working memory ────────────────────────────────────────────
    working_memory_path: str = '.wren/working_memory.json'
    """JSON file for session-scoped working memory."""

    working_memory_max_entries: int = 200
    """Trim to this many entries on each write."""

    # ── Paths ─────────────────────────────────────────────────────
    project_root: str | None = None
    """Injected at runtime. Do not set manually."""


CONFIG: OHOSConfig = OHOSConfig()
"""The one true config. Import this everywhere."""
