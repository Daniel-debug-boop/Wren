"""File-based JSON storage for Wren backend.

Persists app data to `~/.wren/` as JSON files.
Thread-safe with file locking for concurrent access.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


class Storage:
    """Thread-safe file-based JSON storage."""

    _locks: dict[str, threading.Lock] = {}
    _instance: "Storage | None" = None
    _init_lock = threading.Lock()

    def __init__(self, base_dir: str | None = None) -> None:
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path.home() / ".wren"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_instance(cls) -> "Storage":
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _lock(self, name: str) -> threading.Lock:
        if name not in self._locks:
            self._locks[name] = threading.Lock()
        return self._locks[name]

    def _path(self, name: str) -> Path:
        return self.base_dir / f"{name}.json"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def read(self, name: str, default: Any = None) -> Any:
        """Read a JSON file, returning default if not found."""
        path = self._path(name)
        with self._lock(name):
            if not path.exists():
                return default if default is not None else {}
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                return default if default is not None else {}

    def write(self, name: str, data: Any) -> None:
        """Write data to a JSON file atomically."""
        path = self._path(name)
        with self._lock(name):
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2, default=str))
            tmp.replace(path)

    def list_collection(self, name: str, key: str = "id") -> list[dict[str, Any]]:
        """Read a collection (list of dicts) from storage."""
        data = self.read(name, [])
        if isinstance(data, list):
            return data
        return list(data.values()) if isinstance(data, dict) else []

    def add_to_collection(self, name: str, item: dict[str, Any], key: str = "id") -> dict[str, Any]:
        """Add an item to a collection, generating an id if missing."""
        if key not in item or not item[key]:
            item[key] = uuid4().hex[:12]
        data = self.read(name, [])
        if not isinstance(data, list):
            data = list(data.values()) if isinstance(data, dict) else []
        data.append(item)
        self.write(name, data)
        return item

    def update_in_collection(self, name: str, item_id: str, updates: dict[str, Any], key: str = "id") -> dict[str, Any] | None:
        """Update an item in a collection by id."""
        data = self.read(name, [])
        if not isinstance(data, list):
            return None
        for i, item in enumerate(data):
            if item.get(key) == item_id:
                data[i] = {**item, **updates}
                self.write(name, data)
                return data[i]
        return None

    def remove_from_collection(self, name: str, item_id: str, key: str = "id") -> bool:
        """Remove an item from a collection by id."""
        data = self.read(name, [])
        if not isinstance(data, list):
            return False
        filtered = [item for item in data if item.get(key) != item_id]
        if len(filtered) == len(data):
            return False
        self.write(name, filtered)
        return True

    def get_by_id(self, name: str, item_id: str, key: str = "id") -> dict[str, Any] | None:
        """Get a single item from a collection by id."""
        data = self.read(name, [])
        if not isinstance(data, list):
            return None
        for item in data:
            if item.get(key) == item_id:
                return item
        return None

    def get_settings(self) -> dict[str, Any]:
        """Get application settings with defaults."""
        defaults = {
            "llm_config": {
                "model": "openai/gpt-4o-mini",
                "base_url": "https://openrouter.ai/api/v1",
                "max_tokens": 4096,
                "temperature": 0.7,
            },
            "language": "en",
            "sandbox_type": "local",
        }
        settings = self.read("settings", {})
        return {**defaults, **settings}

    def save_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        """Save application settings."""
        current = self.get_settings()
        merged = {**current, **settings}
        self.write("settings", merged)
        return merged

    def get_secrets(self) -> dict[str, str]:
        """Get stored secrets (API keys etc)."""
        return self.read("secrets", {})

    def set_secret(self, name: str, value: str) -> None:
        """Store a secret."""
        secrets = self.get_secrets()
        secrets[name] = value
        self.write("secrets", secrets)

    def delete_secret(self, name: str) -> bool:
        """Delete a secret by name."""
        secrets = self.get_secrets()
        if name in secrets:
            del secrets[name]
            self.write("secrets", secrets)
            return True
        return False

    def get_api_keys(self) -> list[dict[str, Any]]:
        """Get API keys list."""
        return self.list_collection("api_keys", "id")

    def create_api_key(self, name: str) -> dict[str, Any]:
        """Create a new API key."""
        key = f"wr_{uuid4().hex[:24]}"
        item = {
            "id": uuid4().hex[:12],
            "name": name,
            "key_preview": key[:12] + "...",
            "key": key,
            "created_at": self._now(),
        }
        return self.add_to_collection("api_keys", item)

    def delete_api_key(self, key_id: str) -> bool:
        """Delete an API key by id."""
        return self.remove_from_collection("api_keys", key_id)

    def get_conversations(self) -> list[dict[str, Any]]:
        """Get all conversations."""
        return self.list_collection("conversations", "conversation_id")

    def get_conversation(self, conv_id: str) -> dict[str, Any] | None:
        """Get a single conversation."""
        return self.get_by_id("conversations", conv_id, "conversation_id")

    def create_conversation(self, title: str | None = None) -> dict[str, Any]:
        """Create a new conversation."""
        now = self._now()
        conv = {
            "conversation_id": uuid4().hex[:12],
            "title": title or "New Conversation",
            "created_at": now,
            "updated_at": now,
            "status": "stopped",
        }
        return self.add_to_collection("conversations", conv, "conversation_id")

    def delete_conversation(self, conv_id: str) -> bool:
        """Delete a conversation."""
        # Also delete messages
        msg_path = self.base_dir / f"messages_{conv_id}.json"
        if msg_path.exists():
            msg_path.unlink()
        return self.remove_from_collection("conversations", conv_id, "conversation_id")

    def get_messages(self, conv_id: str) -> list[dict[str, Any]]:
        """Get messages for a conversation."""
        return self.list_collection(f"messages_{conv_id}", "id")

    def add_message(self, conv_id: str, role: str, content: str) -> dict[str, Any]:
        """Add a message to a conversation."""
        msg = {
            "id": uuid4().hex[:12],
            "role": role,
            "content": content,
            "timestamp": self._now(),
        }
        result = self.add_to_collection(f"messages_{conv_id}", msg)
        # Update conversation's updated_at
        self.update_in_collection("conversations", conv_id, {"updated_at": self._now()}, "conversation_id")
        return result

    def get_profiles(self) -> dict[str, Any]:
        """Get LLM profiles."""
        data = self.read("profiles", {"profiles": [], "active_profile": None})
        if not data:
            data = {"profiles": [], "active_profile": None}
        return data

    def create_profile(self, name: str, config: dict[str, Any]) -> dict[str, Any]:
        """Create a new LLM profile."""
        profiles_data = self.get_profiles()
        profile = {
            "name": name,
            "model": config.get("model", "openai/gpt-4o-mini"),
            "base_url": config.get("base_url"),
            "api_key_set": bool(config.get("api_key")),
        }
        profiles_data["profiles"].append(profile)
        if not profiles_data["active_profile"]:
            profiles_data["active_profile"] = name
        self.write("profiles", profiles_data)
        return profile

    def delete_profile(self, name: str) -> bool:
        """Delete an LLM profile."""
        profiles_data = self.get_profiles()
        profiles_data["profiles"] = [p for p in profiles_data["profiles"] if p.get("name") != name]
        if profiles_data.get("active_profile") == name:
            profiles_data["active_profile"] = (
                profiles_data["profiles"][0]["name"] if profiles_data["profiles"] else None
            )
        self.write("profiles", profiles_data)
        return True

    def activate_profile(self, name: str) -> bool:
        """Activate an LLM profile."""
        profiles_data = self.get_profiles()
        if not any(p.get("name") == name for p in profiles_data["profiles"]):
            return False
        profiles_data["active_profile"] = name
        self.write("profiles", profiles_data)
        return True

    def get_skills(self) -> list[dict[str, Any]]:
        """Get skills list."""
        return self.list_collection("skills", "name")

    def toggle_skill(self, name: str, enabled: bool) -> dict[str, Any] | None:
        """Toggle a skill's enabled state."""
        return self.update_in_collection("skills", name, {"enabled": enabled}, "name")
