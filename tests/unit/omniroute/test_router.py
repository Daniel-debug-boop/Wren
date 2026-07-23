"""Comprehensive unit tests for OmniRouter.

Tests cover:
  - OmniRouter construction and initialization
  - get_api_key method
  - route method (with mocked combo engine)
  - record_call method
  - add_key / remove_key
  - get_full_status
  - Provider properties (catalog, combo_engine, etc.)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── OmniRoute imports (conftest.py handles wren module stub) ────

from wren.omniroute.router import OmniRouter
from wren.omniroute.types import (
    ComboDefinition,
    ComboStep,
    RoutingResult,
    RoutingStrategy,
    ModelTier,
    ProviderInfo,
    ProviderCategory,
)


# ═══════════════════════════════════════════════════════════════════
#  CONSTRUCTION TESTS
# ═══════════════════════════════════════════════════════════════════


class TestOmniRouterConstruction:
    """OmniRouter can be created and accessed."""

    def test_default_construction(self):
        """Router initializes with all sub-components and not initialized."""
        router = OmniRouter()
        assert router.is_initialized is False
        assert router.catalog is not None
        assert router.combo_engine is not None
        assert router.resilience is not None
        assert router.compression_engine is not None
        assert router.cost_tracker is not None
        assert router.quota_share is not None
        assert router.auto_discovery is not None

    def test_initialized_defaults_to_false(self):
        """Router starts uninitialized."""
        router = OmniRouter()
        assert router.is_initialized is False


# ═══════════════════════════════════════════════════════════════════
#  INITIALIZATION TESTS
# ═══════════════════════════════════════════════════════════════════


class TestInitialize:
    """Router initialization with API keys."""

    @pytest.mark.asyncio
    async def test_initialize_with_keys(self):
        """Initializing with keys returns success with provider count."""
        router = OmniRouter()

        # Patch add_api_key to return quickly
        with patch.object(router._discovery, 'add_api_key', return_value={}):
            with patch.object(
                router._discovery, 'discover_and_generate_combos',
                new=AsyncMock(return_value=[]),
            ):
                result = await router.initialize(api_keys={'openai': 'sk-test'})

        assert result['success'] is True
        assert router.is_initialized is True

    @pytest.mark.asyncio
    async def test_initialize_without_keys(self):
        """Initializing without keys still succeeds with zero providers."""
        router = OmniRouter()

        result = await router.initialize()

        assert result['success'] is True
        assert router.is_initialized is True
        assert result['providers_configured'] == 0


# ═══════════════════════════════════════════════════════════════════
#  GET_API_KEY TESTS
# ═══════════════════════════════════════════════════════════════════


class TestGetApiKey:
    """get_api_key method."""

    def test_get_api_key_returns_none_for_unknown(self):
        """Unknown provider returns None."""
        router = OmniRouter()
        # We can set the internal dict directly for testing
        router._available_providers = {'openai': 'sk-openai-123'}
        assert router.get_api_key('unknown-provider') is None

    def test_get_api_key_returns_key_for_known(self):
        """Known provider returns its API key."""
        router = OmniRouter()
        router._available_providers = {
            'openai': 'sk-openai-123',
            'anthropic': 'sk-ant-456',
        }
        assert router.get_api_key('openai') == 'sk-openai-123'
        assert router.get_api_key('anthropic') == 'sk-ant-456'

    def test_get_api_key_empty_providers(self):
        """Empty provider dict returns None."""
        router = OmniRouter()
        router._available_providers = {}
        assert router.get_api_key('anything') is None


# ═══════════════════════════════════════════════════════════════════
#  ROUTE METHOD TESTS
# ═══════════════════════════════════════════════════════════════════


class TestRoute:
    """Router.route() method."""

    @pytest.mark.asyncio
    async def test_route_uninitialized_returns_empty(self):
        """Uninitialized router returns empty routing result."""
        router = OmniRouter()
        result = await router.route()
        assert result.selected_provider == ''
        assert result.selected_model == ''
        assert result.combo_name == 'uninitialized'

    @pytest.mark.asyncio
    async def test_route_initialized_uses_combo_engine(self):
        """Initialized router delegates to combo engine."""
        router = OmniRouter()
        router._initialized = True
        router._available_providers = {'openai': 'sk-test'}

        # Mock combo engine route
        mock_result = RoutingResult(
            selected_provider='openai',
            selected_model='gpt-4o',
            combo_name='auto/coding',
            estimated_cost_usd=0.01,
        )
        router._combo_engine.route = AsyncMock(return_value=mock_result)

        result = await router.route(combo_name='auto/coding', task_type='coding')
        assert result.selected_provider == 'openai'
        assert result.selected_model == 'gpt-4o'

    @pytest.mark.asyncio
    async def test_route_passes_task_type_and_vision(self):
        """Task type and vision requirement are passed to combo engine."""
        router = OmniRouter()
        router._initialized = True
        router._available_providers = {'anthropic': 'sk-test'}

        router._combo_engine.route = AsyncMock(return_value=RoutingResult(
            selected_provider='anthropic',
            selected_model='claude-sonnet-4',
            combo_name='auto/coding',
        ))

        await router.route(combo_name='auto/coding', task_type='reasoning', require_vision=True)

        router._combo_engine.route.assert_awaited_once_with(
            combo_name='auto/coding',
            task_type='reasoning',
            require_vision=True,
        )


# ═══════════════════════════════════════════════════════════════════
#  ADD / REMOVE KEY TESTS
# ═══════════════════════════════════════════════════════════════════


class TestAddRemoveKey:
    """add_key and remove_key methods."""

    @pytest.mark.asyncio
    async def test_add_key_stores_and_returns_result(self):
        """add_key stores the key and returns discovery result."""
        router = OmniRouter()

        with patch.object(router._discovery, 'add_api_key', return_value={'status': 'ok'}):
            with patch.object(
                router._discovery, 'discover_and_generate_combos',
                new=AsyncMock(return_value=[]),
            ):
                result = await router.add_key('openai', 'sk-new-key')

        assert result == {'status': 'ok'}
        assert router._available_providers['openai'] == 'sk-new-key'

    @pytest.mark.asyncio
    async def test_remove_key_existing(self):
        """Removing an existing key succeeds."""
        router = OmniRouter()
        router._available_providers = {'openai': 'sk-test'}

        with patch.object(router._discovery, 'refresh_from_provider_store', new=AsyncMock()):
            result = await router.remove_key('openai')

        assert result is True
        assert 'openai' not in router._available_providers

    @pytest.mark.asyncio
    async def test_remove_key_nonexistent(self):
        """Removing a non-existent key returns False."""
        router = OmniRouter()
        router._available_providers = {'openai': 'sk-test'}

        result = await router.remove_key('anthropic')
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_last_key_clears_combos(self):
        """Removing the last key clears all combos."""
        router = OmniRouter()
        router._available_providers = {'openai': 'sk-test'}
        router._combo_engine.clear_combos = MagicMock()

        with patch.object(router._discovery, 'refresh_from_provider_store', new=AsyncMock()):
            result = await router.remove_key('openai')

        assert result is True
        router._combo_engine.clear_combos.assert_called_once()


# ═══════════════════════════════════════════════════════════════════
#  RECORD_CALL TESTS
# ═══════════════════════════════════════════════════════════════════


class TestRecordCall:
    """record_call delegates to cost tracker and updates health."""

    def test_record_call_success(self):
        """Successful call is tracked in cost tracker and health."""
        router = OmniRouter()
        router._available_providers = {'openai': 'sk-test'}

        with patch.object(router._cost_tracker, 'record_call') as mock_tracker:
            with patch.object(router._combo_engine, 'record_success') as mock_success:
                with patch.object(router._resilience, 'record_provider_success') as mock_health:
                    router.record_call(
                        provider='openai',
                        model='gpt-4o',
                        role='writer',
                        input_tokens=100,
                        output_tokens=50,
                        duration_ms=500.0,
                        success=True,
                    )

        mock_tracker.assert_called_once()
        mock_success.assert_called_once_with('openai', 500.0)
        mock_health.assert_called_once_with('openai')

    def test_record_call_failure(self):
        """Failed call tracks error and updates failure health."""
        router = OmniRouter()

        with patch.object(router._cost_tracker, 'record_call') as mock_tracker:
            with patch.object(router._combo_engine, 'record_failure') as mock_failure:
                with patch.object(router._resilience, 'record_provider_failure') as mock_health:
                    router.record_call(
                        provider='openai',
                        model='gpt-4o',
                        role='writer',
                        input_tokens=100,
                        output_tokens=50,
                        duration_ms=500.0,
                        success=False,
                    )

        mock_tracker.assert_called_once()
        mock_failure.assert_called_once_with('openai')
        mock_health.assert_called_once_with('openai')


# ═══════════════════════════════════════════════════════════════════
#  COMPRESSION TESTS
# ═══════════════════════════════════════════════════════════════════


class TestCompression:
    """Compression methods delegate correctly."""

    def test_compress_delegates(self):
        """compress() delegates to compression engine."""
        router = OmniRouter()
        router._compression.compress = MagicMock(return_value='compressed text')

        result = router.compress('original text', aggressive=True)
        assert result == 'compressed text'
        router._compression.compress.assert_called_once_with('original text', aggressive=True)

    def test_compress_messages_delegates(self):
        """compress_messages() delegates to compression engine."""
        router = OmniRouter()
        messages = [{'role': 'user', 'content': 'hello'}]
        router._compression.compress_messages = MagicMock(return_value=messages)

        result = router.compress_messages(messages)
        assert result == messages
        router._compression.compress_messages.assert_called_once_with(messages)


# ═══════════════════════════════════════════════════════════════════
#  STATUS TESTS
# ═══════════════════════════════════════════════════════════════════


class TestGetFullStatus:
    """get_full_status returns comprehensive status dict."""

    def test_get_full_status_uninitialized(self):
        """Status reflects uninitialized state."""
        router = OmniRouter()
        status = router.get_full_status()

        assert status['initialized'] is False
        assert status['providers']['configured'] == 0

    def test_get_full_status_with_data(self):
        """Status includes providers and combos."""
        router = OmniRouter()
        router._initialized = True
        router._available_providers = {'openai': 'sk-test'}

        status = router.get_full_status()

        assert status['initialized'] is True
        assert 'openai' in status['providers']['list']
        assert 'cost_tracking' in status
        assert 'discovery' in status

    def test_get_provider_summary_delegates(self):
        """get_provider_summary delegates to discovery."""
        router = OmniRouter()
        router._discovery.get_provider_summary = MagicMock(return_value=[{'name': 'openai'}])

        summary = router.get_provider_summary()
        assert summary == [{'name': 'openai'}]


# ═══════════════════════════════════════════════════════════════════
#  EDGE CASES
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Edge cases for OmniRouter."""

    def test_get_api_key_none_when_not_initialized(self):
        """get_api_key works even when not fully initialized."""
        router = OmniRouter()
        assert router.get_api_key('anything') is None

    def test_multiple_providers(self):
        """Multiple providers can be configured."""
        router = OmniRouter()
        router._available_providers = {
            'openai': 'key1',
            'anthropic': 'key2',
            'google': 'key3',
        }
        assert router.get_api_key('openai') == 'key1'
        assert router.get_api_key('anthropic') == 'key2'
        assert router.get_api_key('google') == 'key3'
        assert router.get_api_key('nonexistent') is None

    @pytest.mark.asyncio
    async def test_add_key_after_initialize(self):
        """Adding a key after initialize works and regenerates combos."""
        router = OmniRouter()
        router._initialized = True
        router._available_providers = {'openai': 'sk-old'}

        with patch.object(router._discovery, 'add_api_key', return_value={'status': 'ok'}):
            with patch.object(
                router._discovery, 'discover_and_generate_combos',
                new=AsyncMock(return_value=[]),
            ):
                await router.add_key('anthropic', 'sk-ant-new')

        assert router._available_providers['anthropic'] == 'sk-ant-new'
        assert router._available_providers['openai'] == 'sk-old'
