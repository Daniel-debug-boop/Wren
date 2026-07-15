"""API client for Wren TUI."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator

import httpx

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Represents an event from the Wren backend."""

    id: int
    source: str  # "agent" | "user" | "environment" | "hook"
    message: str
    timestamp: str
    # Action events
    action: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    # Observation events
    observation: str | None = None
    content: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)
    cause: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        return cls(
            id=data.get('id', 0),
            source=data.get('source', 'agent'),
            message=data.get('message', ''),
            timestamp=data.get('timestamp', ''),
            action=data.get('action'),
            args=data.get('args', {}),
            observation=data.get('observation'),
            content=data.get('content'),
            extras=data.get('extras', {}),
            cause=data.get('cause'),
        )

    @property
    def is_action(self) -> bool:
        return self.action is not None

    @property
    def is_observation(self) -> bool:
        return self.observation is not None

    @property
    def is_message(self) -> bool:
        return self.action == 'message' or self.observation == 'message'

    @property
    def display_text(self) -> str:
        if self.action == 'message':
            return self.args.get('content', self.message)
        if self.observation == 'message':
            return self.content or self.message
        if self.action:
            return f'[action:{self.action}] {self.message}'
        if self.observation:
            return f'[obs:{self.observation}] {self.content or self.message}'
        return self.message


class WrenAPIClient:
    """Async HTTP client for Wren backend API."""

    def __init__(self, base_url: str = 'http://localhost:3000'):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={'Content-Type': 'application/json'},
        )
        self.conversation_id: str | None = None
        self.conversation_url: str | None = None
        self._last_event_id: int = 0

    async def close(self):
        await self.client.aclose()

    async def health_check(self) -> bool:
        """Check if the backend is running."""
        try:
            resp = await self.client.get('/api/v1/health')
            return resp.status_code == 200
        except Exception:
            return False

    async def create_conversation(
        self,
        initial_message: str | None = None,
        repository: str | None = None,
    ) -> str:
        """Create a new conversation and return the conversation ID."""
        body: dict[str, Any] = {}
        if repository:
            body['selected_repository'] = repository
        if initial_message:
            body['initial_message'] = {
                'role': 'user',
                'content': [{'type': 'text', 'text': initial_message}],
            }

        resp = await self.client.post('/api/v1/app-conversations', json=body)
        resp.raise_for_status()
        data = resp.json()
        self.conversation_id = data.get('conversation_id') or data.get('id')
        return self.conversation_id

    async def send_message(self, message: str) -> dict[str, Any]:
        """Send a message to the current conversation."""
        if not self.conversation_id:
            raise ValueError('No conversation active. Create one first.')

        body = {
            'role': 'user',
            'content': [{'type': 'text', 'text': message}],
        }
        resp = await self.client.post(
            f'/api/v1/conversations/{self.conversation_id}/events',
            json=body,
        )
        resp.raise_for_status()
        return resp.json()

    async def get_events(
        self,
        limit: int = 100,
        after_id: int | None = None,
    ) -> list[Event]:
        """Get events from the conversation."""
        if not self.conversation_id:
            return []

        params: dict[str, Any] = {'limit': limit}
        if after_id is not None:
            params['after_id'] = after_id

        resp = await self.client.get(
            f'/api/v1/conversation/{self.conversation_id}/events/search',
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get('items', [])
        events = [Event.from_dict(item) for item in items]
        if events:
            self._last_event_id = max(e.id for e in events)
        return events

    async def get_new_events(self) -> list[Event]:
        """Get only new events since last poll."""
        return await self.get_events(after_id=self._last_event_id)

    async def stream_events(
        self,
        poll_interval: float = 0.5,
    ) -> AsyncGenerator[Event, None]:
        """Continuously poll for new events."""
        while True:
            try:
                events = await self.get_new_events()
                for event in events:
                    yield event
            except Exception as e:
                logger.debug(f'Poll error: {e}')
            await asyncio.sleep(poll_interval)
