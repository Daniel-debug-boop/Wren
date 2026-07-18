from __future__ import annotations

from types import MappingProxyType

from pydantic import SecretStr

from wren.app_server.file_store.memory import InMemoryFileStore
from wren.app_server.integrations.provider import ProviderToken, ProviderType
from wren.app_server.secrets.file_secrets_store import FileSecretsStore
from wren.app_server.secrets.secrets_models import Secrets


class TestFileSecretsStoreEncryption:
    def _make_store(self) -> FileSecretsStore:
        return FileSecretsStore(file_store=InMemoryFileStore())

    async def test_secrets_encrypted_at_rest(self):
        """Stored secrets must not be readable as plaintext on disk."""
        store = self._make_store()
        secrets = Secrets(
            provider_tokens=MappingProxyType(
                {
                    ProviderType.GITHUB: ProviderToken(
                        token=SecretStr('github-token-123'), user_id='user1'
                    )
                }
            )
        )
        await store.store(secrets)

        raw = store.file_store.read('secrets.json')
        # The raw bytes must never contain the plaintext token.
        assert 'github-token-123' not in raw
        assert raw != secrets.model_dump_json(context={'expose_secrets': True})

    async def test_roundtrip(self):
        store = self._make_store()
        secrets = Secrets(
            provider_tokens=MappingProxyType(
                {
                    ProviderType.GITHUB: ProviderToken(
                        token=SecretStr('github-token-123'), user_id='user1'
                    )
                }
            )
        )
        await store.store(secrets)
        loaded = await store.load()

        assert loaded is not None
        assert (
            loaded.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
            == 'github-token-123'
        )

    async def test_legacy_plaintext_migration(self):
        """A pre-existing plaintext secrets.json should still load."""
        store = self._make_store()
        plaintext = Secrets(
            provider_tokens=MappingProxyType(
                {
                    ProviderType.GITHUB: ProviderToken(
                        token=SecretStr('legacy-plain-456'), user_id='user1'
                    )
                }
            )
        ).model_dump_json(context={'expose_secrets': True})
        store.file_store.write('secrets.json', plaintext)
        loaded = await store.load()
        assert loaded is not None
        assert (
            loaded.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
            == 'legacy-plain-456'
        )
