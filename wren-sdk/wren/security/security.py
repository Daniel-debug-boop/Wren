"""Security analysis for Wren SDK.

Provides risk assessment for tool operations.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from wren.tool.base import ToolDef, Action, ToolSafety
from wren.utils.models import WrenModel

logger = logging.getLogger("wren.security")


class SecurityRisk(str, Enum):
    """Security risk levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityAssessment(WrenModel):
    """Assessment of a tool action's security risk."""

    risk: SecurityRisk
    reasons: list[str]
    requires_confirmation: bool = False
    blocked: bool = False


class SecurityAnalyzer:
    """Analyzes security risk of tool operations."""

    def assess(self, tool_def: ToolDef, action: Action) -> SecurityAssessment:
        """Assess the security risk of an action.

        Args:
            tool_def: The tool definition.
            action: The action to assess.

        Returns:
            SecurityAssessment with risk level and reasons.
        """
        reasons = []
        risk = SecurityRisk.LOW

        # Check tool safety level
        if tool_def.safety == ToolSafety.DANGEROUS:
            risk = SecurityRisk.HIGH
            reasons.append("Tool marked as dangerous")
        elif tool_def.safety == ToolSafety.SAFE:
            risk = SecurityRisk.LOW

        # Check for destructive patterns
        command = action.arguments.get("command", "")
        if command:
            if self._is_destructive_command(command):
                risk = SecurityRisk.HIGH
                reasons.append(f"Destructive command: {command}")

        # Check file paths
        path = action.arguments.get("path", "")
        if path:
            if self._is_sensitive_path(path):
                risk = max(risk, SecurityRisk.MEDIUM)
                reasons.append(f"Sensitive path: {path}")

        # Check for data exfiltration
        if self._is_data_exfiltration(action):
            risk = SecurityRisk.CRITICAL
            reasons.append("Potential data exfiltration")

        requires_confirmation = risk in (SecurityRisk.HIGH, SecurityRisk.CRITICAL)

        return SecurityAssessment(
            risk=risk,
            reasons=reasons,
            requires_confirmation=requires_confirmation,
        )

    def _is_destructive_command(self, command: str) -> bool:
        """Check if a command is destructive."""
        destructive_patterns = [
            "rm ",
            "rm -rf",
            "rmdir",
            "unlink",
            "mkfs",
            "dd if=",
            "format",
            "> /dev/",
            "chmod 777",
            "chown",
        ]
        return any(pattern in command for pattern in destructive_patterns)

    def _is_sensitive_path(self, path: str) -> bool:
        """Check if a path is sensitive."""
        sensitive_patterns = [
            "/etc/",
            "/proc/",
            "/sys/",
            ".env",
            "credentials",
            "secrets",
            ".ssh/",
            ".gnupg/",
        ]
        return any(pattern in path.lower() for pattern in sensitive_patterns)

    def _is_data_exfiltration(self, action: Action) -> bool:
        """Check for potential data exfiltration."""
        # Check for curl/wget to external URLs
        command = action.arguments.get("command", "")
        if "curl" in command or "wget" in command:
            url = action.arguments.get("url", "")
            if url and not url.startswith("http://localhost"):
                return True

        # Check for base64 encoding of files
        if "base64" in command and ("cat " in command or "read" in action.arguments):
            return True

        return False
