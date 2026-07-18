"""File-based JSON store for LLM provider configurations.

Stores provider API keys and model configs as an encrypted JSON file in the
persistence directory, keyed by provider name (e.g. 'openai', 'anthropic').

The file is encrypted with AES-256-GCM using a machine-local key derived
from the host's hardware ID (/etc/machine-id). This ensures API keys are
never stored in plaintext on disk.

This store follows the same async pattern as SettingsStore and is used
by the ModelRouter to auto-select models for each agent role.

Storage format (in ~/.wren/llm_providers.json, encrypted):
    Plaintext structure:
    {
        "openai": {
            "provider": "openai",
            "model": "gpt-4o",
            "api_key": "sk-...",
            "base_url": null,
            "updated_at": 1700000000
        },
        ...
    }
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from wren.harness.crypto import decrypt, encrypt, is_encrypted

_logger = logging.getLogger(__name__)


class LLMProviderStore:
    """Persists and retrieves LLM provider configurations.

    Stores provider API keys and model selections in an encrypted JSON file
    under the persistence directory. Thread-safe for single-process use.

    Encryption is transparent: callers save/load plain JSON, the store
    handles encryption at rest automatically.
    """

    _instances: dict[str, 'LLMProviderStore'] = {}
    _DEFAULT_FILENAME = 'llm_providers.json'

    def __init__(self, persistence_dir: str | Path) -> None:
        self._path = Path(persistence_dir) / self._DEFAULT_FILENAME
        self._cache: dict[str, dict[str, Any]] | None = None

    @classmethod
    def get_instance(cls, persistence_dir: str | Path | None = None) -> 'LLMProviderStore':
        """Get or create a store for the given persistence directory.

        Uses the default Wren persistence dir (~/.wren) when none is given.
        """
        if persistence_dir is None:
            persistence_dir = Path.home() / '.wren'
            persistence_dir.mkdir(parents=True, exist_ok=True)

        key = str(persistence_dir)
        if key not in cls._instances:
            cls._instances[key] = cls(persistence_dir)
        return cls._instances[key]

    def _load_raw(self) -> dict[str, dict[str, Any]]:
        """Read the JSON file from disk (bypasses cache).

        Automatically decrypts the file if it was stored encrypted.
        Also handles migration from plaintext to encrypted format.
        """
        if not self._path.exists():
            return {}
        try:
            raw = self._path.read_text('utf-8').strip()
            if not raw:
                return {}

            # Check if the file is encrypted
            if is_encrypted(raw):
                try:
                    raw = decrypt(raw)
                except ValueError as e:
                    _logger.error(
                        'Failed to decrypt %s: %s. '
                        'This likely means the file was created on a different machine.',
                        self._path, e,
                    )
                    return {}
            # Otherwise, it's plaintext JSON (legacy format — will be
            # re-encrypted on next save)

            data = json.loads(raw)
            if not isinstance(data, dict):
                _logger.warning('llm_providers.json is not a dict; resetting')
                return {}
            return data
        except (json.JSONDecodeError, OSError) as e:
            _logger.warning('Failed to load %s: %s', self._path, e)
            return {}

    async def _save_raw(self, data: dict[str, dict[str, Any]]) -> None:
        """Write the JSON file to disk, encrypted, and update cache."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix('.tmp')

        # Serialize to JSON first, then encrypt
        plaintext = json.dumps(data, indent=2, default=str)

        try:
            encrypted = encrypt(plaintext)
            tmp.write_text(encrypted, 'utf-8')
            tmp.replace(self._path)
            _logger.debug(
                'Wrote encrypted provider config (%d bytes ciphertext)',
                len(encrypted),
            )
        except OSError as e:
            _logger.error('Failed to write %s: %s', self._path, e)
            raise
        self._cache = data

    async def load(self) -> dict[str, dict[str, Any]]:
        """Load all provider configs (cached)."""
        if self._cache is not None:
            return self._cache
        self._cache = self._load_raw()
        return self._cache

    async def save_all(self, providers: dict[str, dict[str, Any]]) -> None:
        """Replace all provider configs with the given dict."""
        await self._save_raw(providers)

    async def get(self, provider: str) -> dict[str, Any] | None:
        """Get a single provider config."""
        data = await self.load()
        return data.get(provider)

    async def put(self, provider: str, config: dict[str, Any]) -> None:
        """Save or update a single provider config."""
        data = await self.load()
        data[provider] = config
        await self._save_raw(data)

    async def delete(self, provider: str) -> bool:
        """Remove a provider config. Returns True if it existed."""
        data = await self.load()
        if provider not in data:
            return False
        del data[provider]
        await self._save_raw(data)
        return True

    async def count(self) -> int:
        """Number of configured providers."""
        data = await self.load()
        return len(data)

    async def get_api_keys_map(self) -> dict[str, str]:
        """Return a dict of provider -> api_key for all configured providers.

        This is the format expected by ModelRouter.configure_api_keys().
        """
        data = await self.load()
        return {
            p: cfg['api_key']
            for p, cfg in data.items()
            if cfg.get('api_key')
        }

    async def get_model_map(self) -> dict[str, str]:
        """Return a dict of provider -> model name."""
        data = await self.load()
        return {
            p: cfg['model']
            for p, cfg in data.items()
            if cfg.get('model')
        }
