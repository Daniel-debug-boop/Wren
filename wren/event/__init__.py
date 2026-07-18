"""Re-export event types from Wren SDK.

Extends ``__path__`` to include the SDK's ``wren-sdk/wren/event/``
directory so that ``from wren.event.base import ...`` resolves to the
SDK's native event implementation.
"""

from __future__ import annotations

import os as _os

# Extend __path__ to include the SDK's event module directory so submodule
# imports (e.g. ``from wren.event.base import Event``) resolve correctly.
_repo_root = _os.path.dirname(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
)
_sdk_event_dir = _os.path.join(_repo_root, 'wren-sdk', 'wren', 'event')
if _os.path.isdir(_sdk_event_dir) and _sdk_event_dir not in __path__:
    __path__.append(_sdk_event_dir)

# Import from the SDK's event submodule (now resolvable via the extended path).
from wren.event.base import (
    Event as Event,
    ActionEvent as ActionEvent,
    ObservationEvent as ObservationEvent,
    ConversationStateUpdateEvent as ConversationStateUpdateEvent,
)

# EventID is a string alias in the Wren SDK
EventID = str

__all__ = [
    'Event',
    'ActionEvent',
    'ObservationEvent',
    'ConversationStateUpdateEvent',
    'EventID',
]
