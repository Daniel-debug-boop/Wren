# DEPRECATED: This module is deprecated and will be removed in a future release.
# Please use wren.app_server.app instead.
#
# For backward compatibility, this module re-exports the app from wren.app_server.app.
# Note: This module does NOT include middleware setup. Use wren.server.listen or
# wren.app_server.app directly for the fully configured application.

import warnings

warnings.warn(
    'wren.server.app is deprecated. Use wren.app_server.app instead.',
    DeprecationWarning,
    stacklevel=2,
)

from wren.app_server.app import (  # noqa: E402, F401
    app,
    authentication_error_handler,
    combine_lifespans,
    mcp_app,
)

__all__ = ['app', 'mcp_app', 'combine_lifespans', 'authentication_error_handler']
