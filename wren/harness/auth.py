"""MessageBus authentication layer.

Every agent that publishes to the bus must present a valid token.
Tokens are issued by the MetaOrchestrator on spawn and revoked on
reap.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Any

import os as _os

_ISSUER = 'meta_orchestrator'
_TOKEN_TTL_S = 3600  # tokens expire after 1 hour


class AuthError(Exception):
    """Raised on authentication failure."""


class BusAuth:
    """Token-based authentication for message bus publishers.

    Tokens are HMAC-signed. Agent ID embedded in token so
    impersonation is detectable.
    """

    def __init__(self, secret: str | None = None) -> None:
        self._secret = (
            secret
            or _os.environ.get('WREN_HARNESS_AUTH_SECRET')
            or secrets.token_hex(32)
        )
        self._valid_tokens: dict[str, dict[str, Any]] = {}
        self._revoked: set[str] = set()

    # ── Token lifecycle ──────────────────────────────────────────

    def issue_token(self, agent_id: str, agent_type: str) -> str:
        """Issue a signed token for an agent."""
        prefix = secrets.token_hex(4)
        payload = f'{prefix}:{agent_id}:{int(time.time())}'
        sig = hmac.new(
            self._secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]
        token = f'{payload}:{sig}'
        self._valid_tokens[token] = {
            'agent_id': agent_id,
            'agent_type': agent_type,
            'issued_at': time.time(),
        }
        return token

    def revoke_token(self, token: str) -> None:
        self._valid_tokens.pop(token, None)
        self._revoked.add(token)

    def revoke_all_for_agent(self, agent_id: str) -> int:
        count = 0
        for token, info in list(self._valid_tokens.items()):
            if info['agent_id'] == agent_id:
                self.revoke_token(token)
                count += 1
        return count

    # ── Validation ───────────────────────────────────────────────

    def validate(
        self, token: str, expected_agent_id: str | None = None
    ) -> dict[str, Any]:
        """Validate a token. Returns token info or raises AuthError."""
        if token in self._revoked:
            raise AuthError('Token revoked')

        info = self._valid_tokens.get(token)
        if not info:
            raise AuthError('Invalid token')

        # Check expiry
        if time.time() - info['issued_at'] > _TOKEN_TTL_S:
            self.revoke_token(token)
            raise AuthError('Token expired')

        # Check agent ID match
        if expected_agent_id and info['agent_id'] != expected_agent_id:
            raise AuthError(
                f'Token belongs to {info["agent_id"]}, not {expected_agent_id}'
            )

        return info

    def is_authenticated(self, token: str) -> bool:
        try:
            self.validate(token)
            return True
        except AuthError:
            return False

    def stats(self) -> dict[str, Any]:
        return {
            'valid_tokens': len(self._valid_tokens),
            'revoked': len(self._revoked),
        }
