"""Utility modules for the Wren app server.

Re-exports from wren-sdk utils via namespace path.
"""

import os as _os

# Extend __path__ to include wren-sdk's utils so wren.utils.async_utils etc resolve
_repo_root = _os.path.dirname(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
)
_sdk_utils = _os.path.join(_repo_root, 'wren-sdk', 'wren', 'utils')
if _os.path.isdir(_sdk_utils) and _sdk_utils not in __path__:
    __path__.append(_sdk_utils)

# Re-export utilities for backward compatibility
from wren.utils.models import DiscriminatedUnionMixin, OpenHandsModel, utc_now  # noqa: F401
from wren.utils.redact import (  # noqa: F401
    redact_api_key_literals,
    redact_text_secrets,
    redact_url_params,
)
from wren.utils.paging import page_iterator  # noqa: F401
