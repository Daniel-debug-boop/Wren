# DEPRECATED: This module is deprecated and will be removed in a future release.
# Please use wren.app_server.middleware instead.
#
# For backward compatibility, this module re-exports from wren.app_server.middleware.

import warnings

warnings.warn(
    'wren.server.middleware is deprecated. Use wren.app_server.middleware instead.',
    DeprecationWarning,
    stacklevel=2,
)

from wren.app_server.middleware import (  # noqa: E402, F401
    CacheControlMiddleware,
    InMemoryRateLimiter,
    LocalhostCORSMiddleware,
    RateLimitMiddleware,
)

__all__ = [
    'LocalhostCORSMiddleware',
    'CacheControlMiddleware',
    'InMemoryRateLimiter',
    'RateLimitMiddleware',
]
