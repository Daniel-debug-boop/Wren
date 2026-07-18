"""Hook system for Wren SDK.

Event-driven hooks that execute before/after tool operations.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from wren.event.base import Event
from wren.tool.base import Action, Observation

logger = logging.getLogger("wren.hooks")


class HookPoint(str, Enum):
    """When hooks execute."""

    BEFORE_TOOL = "before_tool"
    AFTER_TOOL = "after_tool"
    BEFORE_LLM = "before_llm"
    AFTER_LLM = "after_llm"
    ON_ERROR = "on_error"
    ON_MESSAGE = "on_message"


class HookResult:
    """Result of a hook execution."""

    def __init__(
        self,
        continue_: bool = True,
        modified_action: Action | None = None,
        modified_observation: Observation | None = None,
        reason: str | None = None,
    ):
        self.continue_ = continue_
        self.modified_action = modified_action
        self.modified_observation = modified_observation
        self.reason = reason

    @classmethod
    def proceed(cls) -> HookResult:
        """Continue execution."""
        return cls(continue_=True)

    @classmethod
    def block(cls, reason: str) -> HookResult:
        """Block execution."""
        return cls(continue_=False, reason=reason)

    @classmethod
    def modify_action(cls, action: Action) -> HookResult:
        """Modify the action before execution."""
        return cls(continue_=True, modified_action=action)

    @classmethod
    def modify_observation(cls, observation: Observation) -> HookResult:
        """Modify the observation after execution."""
        return cls(continue_=True, modified_observation=observation)


class Hook(ABC):
    """Base hook class."""

    @abstractmethod
    def get_point(self) -> HookPoint:
        """Get the hook point."""
        ...

    @abstractmethod
    async def execute(
        self,
        event: Event,
        action: Action | None = None,
        observation: Observation | None = None,
    ) -> HookResult:
        """Execute the hook."""
        ...


class HookManager:
    """Manages and executes hooks."""

    def __init__(self):
        self._hooks: dict[HookPoint, list[Hook]] = {}

    def register(self, hook: Hook) -> None:
        """Register a hook."""
        point = hook.get_point()
        if point not in self._hooks:
            self._hooks[point] = []
        self._hooks[point].append(hook)

    def unregister(self, hook: Hook) -> None:
        """Unregister a hook."""
        point = hook.get_point()
        if point in self._hooks:
            self._hooks[point].remove(hook)

    async def execute_hooks(
        self,
        point: HookPoint,
        event: Event,
        action: Action | None = None,
        observation: Observation | None = None,
    ) -> tuple[bool, Action | None, Observation | None]:
        """Execute all hooks at a given point.

        Returns:
            Tuple of (should_continue, modified_action, modified_observation).
        """
        hooks = self._hooks.get(point, [])

        current_action = action
        current_observation = observation

        for hook in hooks:
            try:
                result = await hook.execute(event, current_action, current_observation)

                if not result.continue_:
                    logger.info(f"Hook blocked execution: {result.reason}")
                    return False, None, None

                if result.modified_action:
                    current_action = result.modified_action

                if result.modified_observation:
                    current_observation = result.modified_observation

            except Exception as e:
                logger.error(f"Hook {hook.__class__.__name__} failed: {e}")

        return True, current_action, current_observation
