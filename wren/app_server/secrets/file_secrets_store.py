from __future__ import annotations

import json
from dataclasses import dataclass

from wren.app_server.file_store.files import FileStore
from wren.app_server.secrets.secrets_models import Secrets
from wren.app_server.secrets.secrets_store import SecretsStore
from wren.app_server.utils.async_utils import call_sync_from_async
from wren.harness.crypto import decrypt, encrypt, is_encrypted


@dataclass
class FileSecretsStore(SecretsStore):
    file_store: FileStore
    path: str = 'secrets.json'

    async def load(self) -> Secrets | None:
        try:
            raw = await call_sync_from_async(self.file_store.read, self.path)
            # Secrets are encrypted at rest. Legacy plaintext files (written
            # before encryption was enabled) are migrated transparently on the
            # next store().
            if is_encrypted(raw):
                raw = decrypt(raw)
            kwargs = json.loads(raw)
            provider_tokens = {
                k: v
                for k, v in (kwargs.get('provider_tokens') or {}).items()
                if v.get('token')
            }
            kwargs['provider_tokens'] = provider_tokens
            secrets = Secrets(**kwargs)
            return secrets
        except FileNotFoundError:
            return None

    async def store(self, secrets: Secrets) -> None:
        json_str = secrets.model_dump_json(context={'expose_secrets': True})
        encrypted = encrypt(json_str)
        await call_sync_from_async(self.file_store.write, self.path, encrypted)

    @classmethod
    async def get_instance(cls, user_id: str | None) -> FileSecretsStore:
        """Get a FileSecretsStore instance using the global config's file_store.

        TODO: This method should be replaced with dependency injection.
        """
        from wren.app_server.config import get_global_config

        file_store = get_global_config().file_store
        return FileSecretsStore(file_store)
