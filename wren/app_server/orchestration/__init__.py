# Lazy imports to avoid pulling in SDK-dependent modules on package init.
# Import the SDK-free modules eagerly; hooks need the external SDK.

from wren.app_server.orchestration.error_recovery import (
    AdaptiveRetryLoop,
    ErrorSignature,
    SolutionRegistry,
)
from wren.app_server.orchestration.goal_detector import GoalDetector
from wren.app_server.orchestration.manager import ManagerAgent
from wren.app_server.orchestration.self_memory_loop import SelfMemoryLoop
from wren.app_server.orchestration.sub_agent_service import (
    SubAgentResult,
    SubAgentService,
)
from wren.app_server.orchestration.working_memory import WorkingMemory


def __getattr__(name: str) -> Any:
    """Lazy-load SDK-dependent modules on first access."""
    if name in ('ReflectionProcessor', 'WorkingMemoryProcessor', 'hooks'):
        from wren.app_server.orchestration.hooks import (  # noqa: PLC0415
            ReflectionProcessor,
            WorkingMemoryProcessor,
        )

        _lazy = {
            'ReflectionProcessor': ReflectionProcessor,
            'WorkingMemoryProcessor': WorkingMemoryProcessor,
        }
        if name in _lazy:
            globals()[name] = _lazy[name]
            return _lazy[name]
        # When 'hooks' is accessed as string, return the module
        from wren.app_server.orchestration import hooks as _hooks_mod  # noqa: PLC0415

        return _hooks_mod
    msg = f'module {__name__!r} has no attribute {name!r}'
    raise AttributeError(msg)


__all__ = [
    'AdaptiveRetryLoop',
    'ErrorSignature',
    'GoalDetector',
    'ManagerAgent',
    'ReflectionProcessor',
    'SelfMemoryLoop',
    'SolutionRegistry',
    'SubAgentResult',
    'SubAgentService',
    'WorkingMemory',
    'WorkingMemoryProcessor',
]
