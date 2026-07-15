"""OpenHands Orchestration System (OHOS) — the autonomous engine.

OHOS is always active. It cannot be disabled. Every conversation
gets the full auto-mode pipeline: goal detection, error recovery,
tool discovery, reflection, and circuit breakers.

SDK entry point:
    from wren.ohos import Orchestrator

    orch = Orchestrator(project_root='/workspace')
    await orch.pre_start(user_message)
    await orch.on_event(event)
    await orch.post_completion(summary)

Lower-level access:
    from wren.ohos import (
        CONFIG,                 # global config
        BREAKER,                # circuit breaker registry
        auto_operation,         # run with auto-recovery
        auto_retry,             # decorate with auto-recovery
        DAGScheduler,           # DAG task scheduler
        run_pre_action_pipeline,
        run_post_event_pipeline,
        run_post_completion_pipeline,
    )
"""

from wren.ohos.auto_wrapper import auto_operation, auto_retry
from wren.ohos.circuit_breaker import BREAKER, CircuitBreakerRegistry
from wren.ohos.config import CONFIG, OHOSConfig
from wren.ohos.orchestrator import Orchestrator
from wren.ohos.pipeline import (
    PostEventContext,
    PreActionContext,
    run_post_completion_pipeline,
    run_post_event_pipeline,
    run_pre_action_pipeline,
)
from wren.ohos.scheduler import DAGScheduler, ScheduledTask

__all__ = [
    'BREAKER',
    'CONFIG',
    'CircuitBreakerRegistry',
    'DAGScheduler',
    'OHOSConfig',
    'Orchestrator',
    'PostEventContext',
    'PreActionContext',
    'ScheduledTask',
    'auto_operation',
    'auto_retry',
    'run_post_completion_pipeline',
    'run_post_event_pipeline',
    'run_pre_action_pipeline',
]
