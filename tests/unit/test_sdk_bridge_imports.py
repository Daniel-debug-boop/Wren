"""Import tests for the ``wren.sdk`` compatibility bridge.

The vendored SDK copy predates the ``wren.sdk`` layout that the app server
and its tests import from. The bridge modules under ``wren/sdk/`` re-export
every symbol from its canonical location. These tests pin that contract:

* every ``wren.sdk.*`` symbol the test suite imports is importable, and
* the bridge symbol is the *same object* as the canonical one (so class
  identity, ``isinstance`` checks and enum members keep working).
"""

from __future__ import annotations

import importlib

import pytest


def _resolve(module_path: str, attr: str):
    module = importlib.import_module(module_path)
    return getattr(module, attr)


# (bridge module, bridge attr, canonical module, canonical attr)
BRIDGE_SYMBOLS = [
    # ── wren.sdk top level ────────────────────────────────────────────
    ('wren.sdk', 'Agent', 'wren.agent', 'Agent'),
    ('wren.sdk', 'AgentConfig', 'wren.agent', 'AgentConfig'),
    ('wren.sdk', 'AgentContext', 'wren.context', 'AgentContext'),
    ('wren.sdk', 'Event', 'wren.event', 'Event'),
    ('wren.sdk', 'EventType', 'wren.event', 'EventType'),
    ('wren.sdk', 'MessageEvent', 'wren.event', 'MessageEvent'),
    ('wren.sdk', 'Message', 'wren.llm', 'Message'),
    ('wren.sdk', 'MessageRole', 'wren.llm', 'MessageRole'),
    ('wren.sdk', 'TextContent', 'wren.llm', 'TextContent'),
    ('wren.sdk', 'ConversationStats', 'wren.conversation', 'ConversationStats'),
    # ── wren.sdk.llm ──────────────────────────────────────────────────
    ('wren.sdk.llm', 'LLM', 'wren.llm', 'LLM'),
    ('wren.sdk.llm', 'Metrics', 'wren.llm', 'Metrics'),
    ('wren.sdk.llm', 'MetricsSnapshot', 'wren.llm', 'MetricsSnapshot'),
    ('wren.sdk.llm', 'TokenUsage', 'wren.llm', 'TokenUsage'),
    # ── wren.sdk.settings ─────────────────────────────────────────────
    ('wren.sdk.settings', 'OpenHandsAgentSettings', 'wren.settings', 'OpenHandsAgentSettings'),
    ('wren.sdk.settings', 'ACPAgentSettings', 'wren.settings', 'ACPAgentSettings'),
    ('wren.sdk.settings', 'ConversationSettings', 'wren.settings', 'ConversationSettings'),
    # ── wren.sdk.settings.model ───────────────────────────────────────
    ('wren.sdk.settings.model', 'AGENT_SETTINGS_SCHEMA_VERSION', 'wren.settings.model', 'AGENT_SETTINGS_SCHEMA_VERSION'),
    ('wren.sdk.settings.model', 'CondenserSettings', 'wren.settings.model', 'CondenserSettings'),
    ('wren.sdk.settings.model', 'VerificationSettings', 'wren.settings.model', 'VerificationSettings'),
    # ── wren.sdk.skills ───────────────────────────────────────────────
    ('wren.sdk.skills', 'Skill', 'wren.skills', 'Skill'),
    ('wren.sdk.skills', 'KeywordTrigger', 'wren.skills', 'KeywordTrigger'),
    ('wren.sdk.skills', 'TaskTrigger', 'wren.skills', 'TaskTrigger'),
    # ── wren.sdk.security ─────────────────────────────────────────────
    ('wren.sdk.security', 'LLMSecurityAnalyzer', 'wren.security', 'LLMSecurityAnalyzer'),
    ('wren.sdk.security', 'NeverConfirm', 'wren.security', 'NeverConfirm'),
    ('wren.sdk.security', 'ConfirmRisky', 'wren.security', 'ConfirmRisky'),
    ('wren.sdk.security', 'AlwaysConfirm', 'wren.security', 'AlwaysConfirm'),
    # ── wren.sdk.event ────────────────────────────────────────────────
    ('wren.sdk.event', 'PauseEvent', 'wren.event', 'PauseEvent'),
    ('wren.sdk.event', 'TokenEvent', 'wren.event', 'TokenEvent'),
    ('wren.sdk.event', 'ConversationStateUpdateEvent', 'wren.event', 'ConversationStateUpdateEvent'),
    # ── wren.sdk.secret ───────────────────────────────────────────────
    ('wren.sdk.secret', 'LookupSecret', 'wren.secret', 'LookupSecret'),
    ('wren.sdk.secret', 'StaticSecret', 'wren.secret', 'StaticSecret'),
    # ── wren.sdk.workspace ────────────────────────────────────────────
    ('wren.sdk.workspace.remote.async_remote_workspace', 'AsyncRemoteWorkspace', 'wren.workspace.remote', 'AsyncRemoteWorkspace'),
    ('wren.sdk.workspace.remote', 'RemoteWorkspace', 'wren.workspace.remote', 'RemoteWorkspace'),
    ('wren.sdk.workspace', 'LocalWorkspace', 'wren.workspace.workspace', 'LocalWorkspace'),
    # ── wren.sdk.context.condenser ────────────────────────────────────
    ('wren.sdk.context.condenser', 'LLMSummarizingCondenser', 'wren.context.condenser', 'LLMSummarizingCondenser'),
    # ── wren.sdk.subagent.schema ──────────────────────────────────────
    ('wren.sdk.subagent.schema', 'AgentDefinition', 'wren.subagent.schema', 'AgentDefinition'),
    # ── wren.sdk.agent ────────────────────────────────────────────────
    ('wren.sdk.agent.acp_agent', 'ACPAgent', 'wren.agent.acp_agent', 'ACPAgent'),
    ('wren.sdk.agent.agent', 'Agent', 'wren.agent.agent', 'Agent'),
    ('wren.sdk.agent', 'AgentConfig', 'wren.agent', 'AgentConfig'),
    # ── wren.sdk.conversation ─────────────────────────────────────────
    ('wren.sdk.conversation', 'ConversationExecutionStatus', 'wren.conversation', 'ConversationExecutionStatus'),
    # ── wren.sdk.utils.redact ─────────────────────────────────────────
    ('wren.sdk.utils.redact', 'redact_api_key_literals', 'wren.utils.redact', 'redact_api_key_literals'),
    ('wren.sdk.utils.redact', 'redact_text_secrets', 'wren.utils.redact', 'redact_text_secrets'),
    ('wren.sdk.utils.redact', 'redact_url_params', 'wren.utils.redact', 'redact_url_params'),
    ('wren.sdk.utils.redact', 'sanitize_config', 'wren.utils.redact', 'sanitize_config'),
]


@pytest.mark.parametrize(
    ('bridge_module', 'bridge_attr', 'canonical_module', 'canonical_attr'),
    BRIDGE_SYMBOLS,
    ids=[f'{m}.{a}' for m, a, _, _ in BRIDGE_SYMBOLS],
)
def test_bridge_symbol_importable_and_identical(
    bridge_module, bridge_attr, canonical_module, canonical_attr
):
    """The bridge symbol exists and is the same object as the canonical one."""
    bridge_obj = _resolve(bridge_module, bridge_attr)
    canonical_obj = _resolve(canonical_module, canonical_attr)
    assert bridge_obj is canonical_obj


def test_bridge_subpackages_accessible_after_import():
    """All bridge subpackages resolve as attributes of ``wren.sdk``."""
    import wren.sdk

    for sub in (
        'agent',
        'conversation',
        'event',
        'llm',
        'secret',
        'security',
        'settings',
        'skills',
        'subagent',
        'utils',
        'workspace',
        'context',
    ):
        assert getattr(wren.sdk, sub) is not None


def test_settings_models_instantiate_through_bridge():
    """Bridge settings models behave like the canonical ones."""
    from wren.sdk.settings import ACPAgentSettings, ConversationSettings, OpenHandsAgentSettings
    from wren.sdk.settings.model import AGENT_SETTINGS_SCHEMA_VERSION, CondenserSettings

    assert OpenHandsAgentSettings().agent_kind == 'wren'
    assert ACPAgentSettings().agent_kind == 'acp'
    assert ConversationSettings().max_iterations == 50
    assert AGENT_SETTINGS_SCHEMA_VERSION >= 1
    assert CondenserSettings().enabled is True


def test_secret_sources_work_through_bridge():
    """Secret sources can be constructed through the bridge."""
    from wren.sdk.secret import LookupSecret, StaticSecret

    assert StaticSecret('abc').value == 'abc'
    assert LookupSecret('MY_KEY').key == 'MY_KEY'


def test_redact_helpers_work_through_bridge():
    """Redaction helpers behave through the bridge."""
    from wren.sdk.utils.redact import redact_text_secrets

    out = redact_text_secrets("api_key='secret123'")
    assert 'secret123' not in out
    assert '<redacted>' in out


def test_event_subclasses_are_events_through_bridge():
    """App-server event subclasses are also wren.sdk.Event instances."""
    from wren.sdk import Event
    from wren.sdk.event import ConversationStateUpdateEvent, PauseEvent, TokenEvent

    assert issubclass(ConversationStateUpdateEvent, Event)
    assert issubclass(PauseEvent, Event)
    assert issubclass(TokenEvent, Event)
