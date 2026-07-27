"""Authentication service for Wren backend.

Simple token-based auth with bcrypt password hashing.
Default credentials: admin / admin
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Any

from .storage import Storage


def _hash_password(password: str) -> str:
    """Simple SHA-256 hash for password (avoids bcrypt dependency issues)."""
    return hashlib.sha256(password.encode()).hexdigest()


def _verify_password(password: str, hashed: str) -> bool:
    return _hash_password(password) == hashed


class AuthService:
    """Authentication and token management."""

    def __init__(self, storage: Storage | None = None):
        self.storage = storage or Storage.get_instance()
        self._secret_key = self._get_or_create_key()

    def _get_or_create_key(self) -> str:
        """Get or create the JWT signing key."""
        config = self.storage.read("auth", {})
        if "secret_key" not in config:
            config["secret_key"] = hashlib.sha256(
                str(time.time()).encode()
            ).hexdigest()
            # Set default admin user
            config["users"] = [
                {
                    "id": "user_001",
                    "username": "admin",
                    "password_hash": _hash_password("admin"),
                    "email": "admin@wren.ai",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            ]
            self.storage.write("auth", config)
        return config["secret_key"]

    def _get_config(self) -> dict[str, Any]:
        return self.storage.read("auth", {})

    def _save_config(self, config: dict[str, Any]) -> None:
        self.storage.write("auth", config)

    def _make_token(self, user_id: str, username: str) -> str:
        """Create a simple signed token."""
        payload = {
            "user_id": user_id,
            "username": username,
            "iat": int(time.time()),
            "exp": int(time.time()) + 86400 * 7,  # 7 days
        }
        payload_str = json.dumps(payload, separators=(",", ":"))
        sig = hmac.new(
            self._secret_key.encode(), payload_str.encode(), hashlib.sha256
        ).hexdigest()
        return f"{payload_str}.{sig}"

    def _verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify a token and return its payload."""
        try:
            parts = token.split(".")
            if len(parts) != 2:
                return None
            payload_str, sig = parts
            expected_sig = hmac.new(
                self._secret_key.encode(), payload_str.encode(), hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(sig, expected_sig):
                return None
            payload = json.loads(payload_str)
            if payload.get("exp", 0) < time.time():
                return None
            return payload
        except (json.JSONDecodeError, ValueError, IndexError):
            return None

    def login(self, username: str, password: str) -> dict[str, Any] | None:
        """Authenticate a user and return a token + user info."""
        config = self._get_config()
        for user in config.get("users", []):
            if user["username"] == username and _verify_password(
                password, user["password_hash"]
            ):
                token = self._make_token(user["id"], user["username"])
                return {
                    "token": token,
                    "user": {
                        "id": user["id"],
                        "username": user["username"],
                        "email": user.get("email", ""),
                        "created_at": user.get("created_at", ""),
                    },
                }
        return None

    def get_user_from_token(self, token: str) -> dict[str, Any] | None:
        """Get user info from a valid token."""
        payload = self._verify_token(token)
        if not payload:
            return None
        config = self._get_config()
        for user in config.get("users", []):
            if user["id"] == payload["user_id"]:
                return {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user.get("email", ""),
                    "created_at": user.get("created_at", ""),
                }
        return None

    def register(
        self, username: str, password: str, email: str | None = None
    ) -> dict[str, Any] | None:
        """Register a new user."""
        config = self._get_config()
        for user in config.get("users", []):
            if user["username"] == username:
                return None  # Username taken

        new_user = {
            "id": f"user_{hashlib.md5(username.encode()).hexdigest()[:8]}",
            "username": username,
            "password_hash": _hash_password(password),
            "email": email or "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        config["users"].append(new_user)
        self._save_config(config)
        token = self._make_token(new_user["id"], new_user["username"])
        return {
            "token": token,
            "user": {
                "id": new_user["id"],
                "username": new_user["username"],
                "email": new_user["email"],
                "created_at": new_user["created_at"],
            },
        }
