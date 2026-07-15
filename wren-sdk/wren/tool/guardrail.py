"""Guardrails for Wren SDK.

Safety constraints that prevent dangerous tool operations.
"""

from __future__ import annotations

import re
import logging
from abc import ABC, abstractmethod
from typing import Any

from wren.tool.base import Action, ToolDef

logger = logging.getLogger("wren.tool.guardrails")


class GuardrailResult:
    """Result of a guardrail check."""

    def __init__(self, allowed: bool, reason: str | None = None):
        self.allowed = allowed
        self.reason = reason

    @classmethod
    def allow(cls) -> GuardrailResult:
        return cls(allowed=True)

    @classmethod
    def deny(cls, reason: str) -> GuardrailResult:
        return cls(allowed=False, reason=reason)


class Guardrail(ABC):
    """Base guardrail class.

    Subclass this to create safety constraints for tool operations.
    """

    @abstractmethod
    def check(self, tool_def: ToolDef, action: Action) -> GuardrailResult:
        """Check if an action is allowed.

        Args:
            tool_def: The tool definition.
            action: The action to check.

        Returns:
            GuardrailResult with allowed=True or allowed=False with reason.
        """
        ...


class CommandBlocklist(Guardrail):
    """Block dangerous shell commands."""

    BLOCKED_PATTERNS = [
        r"rm\s+-rf\s+/",
        r"rm\s+-rf\s+~",
        r"mkfs\.",
        r"dd\s+if=",
        r":\(\){ :\|:& };:",  # fork bomb
        r"chmod\s+-R\s+777\s+/",
        r"chown\s+-R",
        r">\s+/dev/sd",
    ]

    def check(self, tool_def: ToolDef, action: Action) -> GuardrailResult:
        if tool_def.name != "bash":
            return GuardrailResult.allow()

        command = action.arguments.get("command", "")
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, command):
                return GuardrailResult.deny(
                    f"Blocked dangerous command: matches pattern '{pattern}'"
                )

        return GuardrailResult.allow()


class PathBlocklist(Guardrail):
    """Block access to sensitive file paths."""

    BLOCKED_PATHS = [
        r"/etc/",
        r"/proc/",
        r"/sys/",
        r"/dev/",
        r"\.env$",
        r"\.env\.",
        r"credentials",
        r"secrets",
        r"\.ssh/",
        r"\.gnupg/",
    ]

    def check(self, tool_def: ToolDef, action: Action) -> GuardrailResult:
        if tool_def.name not in ("read_file", "write_file", "edit_file", "list_directory"):
            return GuardrailResult.allow()

        path = action.arguments.get("path", "")
        for pattern in self.BLOCKED_PATHS:
            if re.search(pattern, path, re.IGNORECASE):
                return GuardrailResult.deny(f"Blocked access to sensitive path: {path}")

        return GuardrailResult.allow()


class GitGuardrail(Guardrail):
    """Block dangerous git operations."""

    BLOCKED_COMMANDS = [
        r"git\s+push\s+--force",
        r"git\s+reset\s+--hard",
        r"git\s+clean\s+-fd",
        r"git\s+branch\s+-D",
        r"git\s+checkout\s+--\s+\.",
    ]

    def check(self, tool_def: ToolDef, action: Action) -> GuardrailResult:
        if tool_def.name != "bash":
            return GuardrailResult.allow()

        command = action.arguments.get("command", "")
        for pattern in self.BLOCKED_COMMANDS:
            if re.search(pattern, command):
                return GuardrailResult.deny(f"Blocked dangerous git operation: {pattern}")

        return GuardrailResult.allow()


class NetworkGuardrail(Guardrail):
    """Block access to internal/private IPs."""

    PRIVATE_IP_PATTERNS = [
        r"127\.\d+\.\d+\.\d+",
        r"10\.\d+\.\d+\.\d+",
        r"172\.(1[6-9]|2\d|3[01])\.\d+\.\d+",
        r"192\.168\.\d+\.\d+",
        r"localhost",
        r"0\.0\.0\.0",
    ]

    def check(self, tool_def: ToolDef, action: Action) -> GuardrailResult:
        if tool_def.name not in ("fetch", "scrape", "bash"):
            return GuardrailResult.allow()

        url = action.arguments.get("url", "")
        command = action.arguments.get("command", "")
        target = url or command

        for pattern in self.PRIVATE_IP_PATTERNS:
            if re.search(pattern, target):
                return GuardrailResult.deny(f"Blocked access to private/internal address: {target}")

        return GuardrailResult.allow()


class GuardrailEnforcer:
    """Enforces multiple guardrails on tool operations."""

    def __init__(self):
        self._guardrails: list[Guardrail] = []

    def add(self, guardrail: Guardrail) -> None:
        """Add a guardrail."""
        self._guardrails.append(guardrail)

    def remove(self, guardrail: Guardrail) -> None:
        """Remove a guardrail."""
        self._guardrails.remove(guardrail)

    def check(self, tool_def: ToolDef, action: Action) -> GuardrailResult:
        """Check all guardrails for an action.

        Returns:
            GuardrailResult with allowed=True if all guardrails pass,
            or allowed=False with the first denial reason.
        """
        for guardrail in self._guardrails:
            result = guardrail.check(tool_def, action)
            if not result.allowed:
                logger.warning(f"Guardrail blocked {tool_def.name}: {result.reason}")
                return result

        return GuardrailResult.allow()

    @classmethod
    def default(cls) -> GuardrailEnforcer:
        """Create a guardrail enforcer with default guardrails."""
        enforcer = cls()
        enforcer.add(CommandBlocklist())
        enforcer.add(PathBlocklist())
        enforcer.add(GitGuardrail())
        enforcer.add(NetworkGuardrail())
        return enforcer
