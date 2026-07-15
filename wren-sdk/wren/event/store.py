"""Event store for Wren SDK.

Provides persistent event logging for conversation history.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterator

from wren.event.base import Event, EventType
from wren.utils.models import utc_now


class EventLog:
    """In-memory event store with optional persistence.

    Stores events for a conversation and provides iteration/filtering.
    """

    def __init__(self, persist_path: Path | None = None):
        self._events: list[Event] = []
        self._persist_path = persist_path

    def add(self, event: Event) -> None:
        """Add an event to the log."""
        self._events.append(event)
        if self._persist_path:
            self._append_to_file(event)

    def get_events(
        self,
        event_type: EventType | None = None,
        after: datetime | None = None,
        limit: int | None = None,
    ) -> list[Event]:
        """Get events with optional filtering."""
        events = self._events

        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]

        if after is not None:
            events = [e for e in events if e.timestamp > after]

        if limit is not None:
            events = events[:limit]

        return events

    def get_last(self, n: int = 1) -> list[Event]:
        """Get last N events."""
        return self._events[-n:]

    def clear(self) -> None:
        """Clear all events."""
        self._events.clear()

    def __len__(self) -> int:
        return len(self._events)

    def __iter__(self) -> Iterator[Event]:
        return iter(self._events)

    def __getitem__(self, index: int) -> Event:
        return self._events[index]

    def to_prompt(self, limit: int | None = None) -> str:
        """Convert events to prompt string."""
        events = self._events[-limit:] if limit else self._events
        return '\n'.join(e.to_prompt() for e in events)

    def to_json(self) -> str:
        """Serialize all events to JSON."""
        return json.dumps(
            [e.to_dict() for e in self._events],
            indent=2,
        )

    def _append_to_file(self, event: Event) -> None:
        """Append event to persistence file."""
        if self._persist_path is None:
            return

        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._persist_path, 'a') as f:
            f.write(event.to_json() + '\n')
