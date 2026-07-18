"""Security exports for Wren."""

from __future__ import annotations

from typing import Any


class SecurityRisk:
    """Security risk assessment."""

    def __init__(self, level: str = "low", description: str = ""):
        self.level = level
        self.description = description


class SecurityAnalyzerBase:
    """Base class for security analyzers."""

    async def analyze(self, action: dict[str, Any]) -> SecurityRisk:
        return SecurityRisk()


class LLMSecurityAnalyzer(SecurityAnalyzerBase):
    """LLM-based security analyzer."""

    def __init__(self, llm: Any = None):
        self.llm = llm


class ConfirmationPolicyBase:
    """Base class for confirmation policies."""

    def requires_confirmation(self, action: dict[str, Any]) -> bool:
        return False


class AlwaysConfirm(ConfirmationPolicyBase):
    """Always require confirmation."""

    def requires_confirmation(self, action: dict[str, Any]) -> bool:
        return True


class NeverConfirm(ConfirmationPolicyBase):
    """Never require confirmation."""

    def requires_confirmation(self, action: dict[str, Any]) -> bool:
        return False


class ConfirmRisky(ConfirmationPolicyBase):
    """Confirm only risky actions."""

    def __init__(self, threshold: str = "medium"):
        self.threshold = threshold

    def requires_confirmation(self, action: dict[str, Any]) -> bool:
        return action.get("risk", "low") != "low"


__all__ = [
    "SecurityRisk",
    "SecurityAnalyzerBase",
    "LLMSecurityAnalyzer",
    "ConfirmationPolicyBase",
    "AlwaysConfirm",
    "NeverConfirm",
    "ConfirmRisky",
]
