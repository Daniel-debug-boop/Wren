"""Re-export event types from openhands SDK."""

from openhands.sdk.event import (  # noqa: F401
    Event,
    ActionEvent,
    ObservationEvent,
    ConversationStateUpdateEvent,
)

# EventID is a string alias in the openhands SDK
EventID = str
