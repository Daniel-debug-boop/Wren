"""ACP provider detection utilities.

Provides the ``detect_acp_provider_by_command`` function used by
the webhook router to detect ACP providers from conversation commands.
"""

from __future__ import annotations

from wren.settings import detect_acp_provider_by_command

__all__ = ["detect_acp_provider_by_command"]
