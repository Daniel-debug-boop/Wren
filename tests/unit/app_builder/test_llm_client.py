"""Comprehensive unit tests for LLMClient.

Tests cover:
  - Construction with various parameters
  - Direct API call flow (mocked urllib)
  - OmniRoute integration
  - Error handling
  - from_env classmethod
  - Cost tracking record_call
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from wren.app_builder.llm_client import LLMClient, get_omnirouter


# ═══════════════════════════════════════════════════════════════════
#  CONSTRUCTION TESTS
# ═══════════════════════════════════════════════════════════════════


class TestLLMClientConstruction:
    """LLMClient construction and default values."""

    def test_default_construction(self):
        """Client can be created with just an API key."""
        client = LLMClient(api_key='sk-test-123')
        assert client.api_key == 'sk-test-123'
        assert client.model == 'gpt-4o'
        assert client.base_url == 'https://api.openai.com/v1'
        assert client.max_tokens == 16384
        assert client.temperature == 0.3
        assert client._omnirouter is None
        assert client._combo_name == 'auto/coding'

    def test_construction_with_all_params(self):
        """Client accepts all optional parameters."""
        router = MagicMock()
        client = LLMClient(
            api_key='sk-test',
            model='claude-sonnet-4',
            base_url='https://api.anthropic.com/v1',
            max_tokens=8192,
            temperature=0.7,
            timeout_read=60.0,
            omnirouter=router,
            combo_name='auto/cheap',
        )
        assert client.api_key == 'sk-test'
        assert client.model == 'claude-sonnet-4'
        assert client.base_url == 'https://api.anthropic.com/v1'
        assert client.max_tokens == 8192
        assert client.temperature == 0.7
        assert client._timeout == 60.0
        assert client._omnirouter is router
        assert client._combo_name == 'auto/cheap'

    def test_base_url_trailing_slash_removed(self):
        """Trailing slash in base_url is stripped."""
        client = LLMClient(api_key='sk-test', base_url='https://openrouter.ai/api/v1/')
        assert client.base_url == 'https://openrouter.ai/api/v1'

    def test_empty_base_url_defaults_to_openai(self):
        """Empty base_url defaults to OpenAI."""
        client = LLMClient(api_key='sk-test', base_url='')
        assert client.base_url == 'https://api.openai.com/v1'

    def test_close_is_noop(self):
        """close() does nothing since urllib has no persistent client."""
        client = LLMClient(api_key='sk-test')
        result = client.close()
        assert result is None

    def test_from_env_with_env_vars(self, monkeypatch):
        """from_env reads environment variables."""
        monkeypatch.setenv('OPENAI_API_KEY', 'sk-env-key')
        monkeypatch.setenv('LLM_MODEL', 'gpt-4o-mini')
        monkeypatch.setenv('LLM_BASE_URL', 'https://api.deepseek.com/v1')

        client = LLMClient.from_env()
        assert client.api_key == 'sk-env-key'
        assert client.model == 'gpt-4o-mini'
        assert client.base_url == 'https://api.deepseek.com/v1'

    def test_from_env_defaults(self, monkeypatch):
        """from_env uses defaults when env vars are not set."""
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)
        monkeypatch.delenv('LLM_MODEL', raising=False)
        monkeypatch.delenv('LLM_BASE_URL', raising=False)

        client = LLMClient.from_env()
        assert client.api_key == ''
        assert client.model == 'gpt-4o'
        assert client.base_url is None  # from_env doesn't set default base_url


# ═══════════════════════════════════════════════════════════════════
#  SEND — DIRECT MODE TESTS
# ═══════════════════════════════════════════════════════════════════


class TestLLMClientSendDirect:
    """LLMClient.send() in direct mode (no OmniRoute)."""

    @pytest.mark.asyncio
    async def test_send_success(self):
        """Successful API call returns response content."""
        mock_response = {
            'choices': [{'message': {'content': 'Hello from LLM!'}}]
        }
        response_json = json.dumps(mock_response).encode('utf-8')

        with patch('wren.app_builder.llm_client.urlopen') as mock_urlopen:
            mock_ctx = MagicMock()
            mock_ctx.read.return_value = response_json
            mock_urlopen.return_value.__enter__.return_value = mock_ctx

            client = LLMClient(api_key='sk-test')
            result = await client.send('You are helpful.', 'Say hello')

            assert result == 'Hello from LLM!'

            # Verify the API URL and headers
            call_args = mock_urlopen.call_args
            req = call_args[0][0]
            assert '/chat/completions' in str(req.url)
            assert 'Bearer sk-test' in str(req.headers)
            assert 'application/json' in str(req.headers)

    @pytest.mark.asyncio
    async def test_send_empty_content(self):
        """API returning empty content returns empty string."""
        mock_response = {
            'choices': [{'message': {'content': ''}}]
        }
        response_json = json.dumps(mock_response).encode('utf-8')

        with patch('wren.app_builder.llm_client.urlopen') as mock_urlopen:
            mock_ctx = MagicMock()
            mock_ctx.read.return_value = response_json
            mock_urlopen.return_value.__enter__.return_value = mock_ctx

            client = LLMClient(api_key='sk-test')
            result = await client.send('You are helpful.', 'Say nothing')
            assert result == ''

    @pytest.mark.asyncio
    async def test_send_missing_choices_key(self):
        """API response missing 'choices' returns empty string."""
        response_json = json.dumps({'id': '123'}).encode('utf-8')

        with patch('wren.app_builder.llm_client.urlopen') as mock_urlopen:
            mock_ctx = MagicMock()
            mock_ctx.read.return_value = response_json
            mock_urlopen.return_value.__enter__.return_value = mock_ctx

            client = LLMClient(api_key='sk-test')
            result = await client.send('You are helpful.', 'Test')
            assert result == ''


# ═══════════════════════════════════════════════════════════════════
#  SEND — ERROR HANDLING TESTS
# ═══════════════════════════════════════════════════════════════════


class TestLLMClientErrors:
    """LLMClient error handling."""

    @pytest.mark.asyncio
    async def test_missing_api_key_raises_error(self):
        """Calling send() without API key raises RuntimeError."""
        client = LLMClient(api_key='')
        with pytest.raises(RuntimeError, match='No API key available'):
            await client.send('system', 'user')

    @pytest.mark.asyncio
    async def test_http_error(self):
        """HTTP 4xx/5xx raises RuntimeError with details."""
        from urllib.error import HTTPError

        # Mock HTTPError raised by urlopen
        error_patcher = patch(
            'wren.app_builder.llm_client.urlopen',
            side_effect=HTTPError(
                url='http://test.com/chat/completions',
                code=401,
                msg='Unauthorized',
                hdrs={},
                fp=type('FakeFile', (), {'read': lambda s: b'{"error":"invalid key"}'})(),
            ),
        )

        with error_patcher:
            client = LLMClient(api_key='sk-bad')
            with pytest.raises(RuntimeError, match='LLM API error 401'):
                await client.send('system', 'user')

    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Connection failure raises RuntimeError."""
        from urllib.error import URLError

        with patch('wren.app_builder.llm_client.urlopen', side_effect=URLError('Connection refused')):
            client = LLMClient(api_key='sk-test')
            with pytest.raises(RuntimeError, match='LLM API connection failed'):
                await client.send('system', 'user')

    @pytest.mark.asyncio
    async def test_invalid_json_response(self):
        """Non-JSON response raises RuntimeError."""
        with patch('wren.app_builder.llm_client.urlopen') as mock_urlopen:
            mock_ctx = MagicMock()
            mock_ctx.read.return_value = b'not-json-at-all'
            mock_urlopen.return_value.__enter__.return_value = mock_ctx

            client = LLMClient(api_key='sk-test')
            with pytest.raises(RuntimeError, match='invalid JSON'):
                await client.send('system', 'user')


# ═══════════════════════════════════════════════════════════════════
#  SEND — OMNIROUTE MODE TESTS
# ═══════════════════════════════════════════════════════════════════


class TestLLMClientOmniRoute:
    """LLMClient.send() with OmniRoute integration."""

    @pytest.mark.asyncio
    async def test_omniroute_routes_request(self):
        """When OmniRoute is available, it selects the provider."""
        mock_response = json.dumps(
            {'choices': [{'message': {'content': 'Hello from OmniRoute!'}}]}
        ).encode('utf-8')

        # Create a realistic OmniRouter mock
        router = AsyncMock()
        router.is_initialized = True
        router.route.return_value = MagicMock(
            selected_provider='openai',
            selected_model='gpt-4o',
            fallback_chain=[],
        )
        router.get_api_key.return_value = 'sk-omniroute-key'
        router.catalog.get_provider.return_value = MagicMock(
            base_url='https://api.openai.com/v1'
        )

        with patch('wren.app_builder.llm_client.urlopen') as mock_urlopen:
            mock_ctx = MagicMock()
            mock_ctx.read.return_value = mock_response
            mock_urlopen.return_value.__enter__.return_value = mock_ctx

            client = LLMClient(api_key='sk-fallback', omnirouter=router)
            result = await client.send('system', 'user')

            assert result == 'Hello from OmniRoute!'

            # Verify OmniRoute was consulted
            router.route.assert_awaited_once()
            router.get_api_key.assert_called_once_with('openai')

            # Verify client tracked provider
            assert client._last_provider == 'openai'
            assert client._last_model == 'gpt-4o'

    @pytest.mark.asyncio
    async def test_omniroute_not_initialized_falls_back_to_direct(self):
        """When OmniRoute is not initialized, direct config is used."""
        mock_response = json.dumps(
            {'choices': [{'message': {'content': 'Direct fallback'}}]}
        ).encode('utf-8')

        router = MagicMock()
        router.is_initialized = False  # Not initialized

        with patch('wren.app_builder.llm_client.urlopen') as mock_urlopen:
            mock_ctx = MagicMock()
            mock_ctx.read.return_value = mock_response
            mock_urlopen.return_value.__enter__.return_value = mock_ctx

            client = LLMClient(api_key='sk-direct', model='gpt-3.5-turbo', omnirouter=router)
            result = await client.send('system', 'user')

            assert result == 'Direct fallback'
            # OmniRoute.route should NOT have been called
            router.route.assert_not_called()

    @pytest.mark.asyncio
    async def test_omniroute_records_call_in_finally(self):
        """OmniRoute.record_call is invoked in the finally block."""
        mock_response = json.dumps(
            {'choices': [{'message': {'content': 'OK'}}]}
        ).encode('utf-8')

        router = AsyncMock()
        router.is_initialized = True
        router.route.return_value = MagicMock(
            selected_provider='openai',
            selected_model='gpt-4o',
            fallback_chain=[],
        )
        router.get_api_key.return_value = 'sk-ok'
        router.catalog.get_provider.return_value = MagicMock(
            base_url='https://api.openai.com/v1'
        )

        with patch('wren.app_builder.llm_client.urlopen') as mock_urlopen:
            mock_ctx = MagicMock()
            mock_ctx.read.return_value = mock_response
            mock_urlopen.return_value.__enter__.return_value = mock_ctx

            client = LLMClient(api_key='sk-test', omnirouter=router)
            await client.send('system', 'user')

            # Verify record_call was called
            router.record_call.assert_called_once()
            call_kwargs = router.record_call.call_args.kwargs
            assert call_kwargs['provider'] == 'openai'
            assert call_kwargs['model'] == 'gpt-4o'
            assert call_kwargs['role'] == 'writer'
            assert call_kwargs['success'] is True
            assert call_kwargs['duration_ms'] > 0

    @pytest.mark.asyncio
    async def test_omniroute_records_failed_call(self):
        """OmniRoute.record_call is invoked even when API call fails."""
        router = AsyncMock()
        router.is_initialized = True
        router.route.return_value = MagicMock(
            selected_provider='openai',
            selected_model='gpt-4o',
            fallback_chain=[],
        )
        router.get_api_key.return_value = 'sk-test'
        router.catalog.get_provider.return_value = MagicMock(
            base_url='https://api.openai.com/v1'
        )

        from urllib.error import URLError

        with patch('wren.app_builder.llm_client.urlopen', side_effect=URLError('Timeout')):
            client = LLMClient(api_key='sk-test', omnirouter=router)
            with pytest.raises(RuntimeError):
                await client.send('system', 'user')

            # Verify record_call was still called
            router.record_call.assert_called_once()
            call_kwargs = router.record_call.call_args.kwargs
            assert call_kwargs['provider'] == 'openai'
            assert call_kwargs['model'] == 'gpt-4o'
            assert call_kwargs['success'] is False

    @pytest.mark.asyncio
    async def test_omniroute_no_routed_provider(self):
        """When OmniRoute doesn't select a provider, direct config is used."""
        mock_response = json.dumps(
            {'choices': [{'message': {'content': 'No routed provider'}}]}
        ).encode('utf-8')

        router = AsyncMock()
        router.is_initialized = True
        router.route.return_value = MagicMock(
            selected_provider='',  # Empty = no selection
            selected_model=None,
            fallback_chain=[],
        )
        router.get_api_key.return_value = None  # No key found

        with patch('wren.app_builder.llm_client.urlopen') as mock_urlopen:
            mock_ctx = MagicMock()
            mock_ctx.read.return_value = mock_response
            mock_urlopen.return_value.__enter__.return_value = mock_ctx

            client = LLMClient(api_key='sk-direct', model='gpt-3.5-turbo', omnirouter=router)
            result = await client.send('system', 'user')

            assert result == 'No routed provider'
            assert client._last_provider == ''  # Not tracked


# ═══════════════════════════════════════════════════════════════════
#  GET_OMNIROUTER FUNCTION
# ═══════════════════════════════════════════════════════════════════


class TestGetOmniRouter:
    """get_omnirouter() lazy import function."""

    def test_returns_none_when_not_available(self):
        """get_omnirouter returns None when fastapi/pydantic not available."""
        # In test context, the full fastapi stack isn't available
        # so get_omnirouter gracefully returns None
        result = get_omnirouter()
        assert result is None


# ═══════════════════════════════════════════════════════════════════
#  TRACKING / STATE TESTS
# ═══════════════════════════════════════════════════════════════════


class TestLLMClientTracking:
    """LLMClient internal state tracking."""

    @pytest.mark.asyncio
    async def test_last_provider_and_model_updated(self):
        """_last_provider and _last_model are updated after OmniRoute send."""
        mock_response = json.dumps(
            {'choices': [{'message': {'content': 'OK'}}]}
        ).encode('utf-8')

        router = AsyncMock()
        router.is_initialized = True
        router.route.return_value = MagicMock(
            selected_provider='anthropic',
            selected_model='claude-sonnet-4',
            fallback_chain=[],
        )
        router.get_api_key.return_value = 'sk-ant-key'
        router.catalog.get_provider.return_value = MagicMock(
            base_url='https://api.anthropic.com/v1'
        )

        with patch('wren.app_builder.llm_client.urlopen') as mock_urlopen:
            mock_ctx = MagicMock()
            mock_ctx.read.return_value = mock_response
            mock_urlopen.return_value.__enter__.return_value = mock_ctx

            client = LLMClient(api_key='sk-test', omnirouter=router)
            assert client._last_provider == ''
            assert client._last_model == ''

            await client.send('system', 'user')

            assert client._last_provider == 'anthropic'
            assert client._last_model == 'claude-sonnet-4'

    def test_default_combo_name(self):
        """Default combo_name is auto/coding."""
        client = LLMClient(api_key='sk-test')
        assert client._combo_name == 'auto/coding'

    def test_custom_combo_name(self):
        """Custom combo_name is accepted."""
        client = LLMClient(api_key='sk-test', combo_name='auto/vision')
        assert client._combo_name == 'auto/vision'
