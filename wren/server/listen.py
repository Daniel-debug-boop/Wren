# DEPRECATED: This module is deprecated and will be removed in a future release.
# Please use wren.app_server.app instead.
#
# For backward compatibility, this module re-exports the app from wren.app_server.app.

import warnings

warnings.warn(
    'wren.server.listen is deprecated. Use wren.app_server.app instead.',
    DeprecationWarning,
    stacklevel=2,
)

from wren.app_server.app import app  # noqa: E402, F401

__all__ = ['app']
