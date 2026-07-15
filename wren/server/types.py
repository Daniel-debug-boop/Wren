# DEPRECATED: This module is deprecated and will be removed in a future release.
# Please use wren.app_server.types instead.
#
# For backward compatibility, this module re-exports all types from wren.app_server.types.

import warnings

warnings.warn(
    'wren.server.types is deprecated. Use wren.app_server.types instead.',
    DeprecationWarning,
    stacklevel=2,
)

from wren.app_server.types import (  # noqa: E402, F401
    AppMode,
    LLMAuthenticationError,
    MissingSettingsError,
    ServerConfigInterface,
    SessionExpiredError,
)

__all__ = [
    'AppMode',
    'ServerConfigInterface',
    'MissingSettingsError',
    'LLMAuthenticationError',
    'SessionExpiredError',
]
