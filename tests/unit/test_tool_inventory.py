"""Tests for the tool registry inventory — new skills and MCP servers."""

from __future__ import annotations

import pytest

from wren.app_server.tool_registry.inventory import ToolInventory


@pytest.fixture
def inventory():
    return ToolInventory()


class TestScraplingSkill:
    def test_registered(self, inventory):
        entry = inventory.find_by_name('scrapling')
        assert entry is not None
        assert entry.type == 'skill'

    def test_has_triggers(self, inventory):
        entry = inventory.find_by_name('scrapling')
        assert len(entry.triggers) > 0
        assert 'scrape' in entry.triggers
        assert 'cloudflare bypass' in entry.triggers
        assert 'stealth fetch' in entry.triggers

    def test_in_keyword_search(self, inventory):
        results = inventory.search_by_keyword('scrape')
        names = [e.name for e in results]
        assert 'scrapling' in names

    def test_in_cloudflare_search(self, inventory):
        results = inventory.search_by_keyword('cloudflare')
        names = [e.name for e in results]
        assert 'scrapling' in names


class TestEmilSkills:
    def test_emil_design_eng_registered(self, inventory):
        entry = inventory.find_by_name('emil-design-eng')
        assert entry is not None
        assert entry.type == 'skill'

    def test_animation_vocabulary_registered(self, inventory):
        entry = inventory.find_by_name('animation-vocabulary')
        assert entry is not None
        assert entry.type == 'skill'

    def test_review_animations_registered(self, inventory):
        entry = inventory.find_by_name('review-animations')
        assert entry is not None
        assert entry.type == 'skill'

    def test_emil_triggers(self, inventory):
        entry = inventory.find_by_name('emil-design-eng')
        assert 'design quality' in entry.triggers
        assert 'polish' in entry.triggers
        assert 'animation' in entry.triggers

    def test_animation_vocabulary_triggers(self, inventory):
        entry = inventory.find_by_name('animation-vocabulary')
        assert 'animation' in entry.triggers
        assert 'easing' in entry.triggers
        assert 'spring' in entry.triggers

    def test_review_animations_triggers(self, inventory):
        entry = inventory.find_by_name('review-animations')
        assert 'review animation' in entry.triggers
        assert 'animation quality' in entry.triggers


class TestBehaviorSkills:
    @pytest.mark.parametrize(
        'name',
        [
            'skill-triggering',
            'copyright-compliance',
            'file-creation',
            'refusal-handling',
            'tone-formatting',
        ],
    )
    def test_registered(self, inventory, name):
        entry = inventory.find_by_name(name)
        assert entry is not None, f'{name} not registered'
        assert entry.type == 'skill'


class TestPenpotSkill:
    def test_registered(self, inventory):
        entry = inventory.find_by_name('penpot')
        assert entry is not None
        assert entry.type == 'skill'

    def test_has_triggers(self, inventory):
        entry = inventory.find_by_name('penpot')
        assert 'penpot' in entry.triggers
        assert 'design tokens' in entry.triggers


class TestMCPServers:
    def test_scrapling_mcp_registered(self, inventory):
        servers = inventory.get_mcp_server_list()
        names = [s['name'] for s in servers]
        assert 'scrapling' in names

    def test_scrapling_mcp_command(self, inventory):
        servers = inventory.get_mcp_server_list()
        scrapling = [s for s in servers if s['name'] == 'scrapling']
        assert len(scrapling) >= 1
        assert scrapling[0]['command'] == 'scrapling'
        assert 'mcp' in scrapling[0]['args']

    def test_chrome_devtools_mcp_registered(self, inventory):
        servers = inventory.get_mcp_server_list()
        names = [s['name'] for s in servers]
        assert 'chrome-devtools' in names

    def test_fetch_mcp_registered(self, inventory):
        servers = inventory.get_mcp_server_list()
        names = [s['name'] for s in servers]
        assert 'fetch' in names

    def test_filesystem_mcp_registered(self, inventory):
        servers = inventory.get_mcp_server_list()
        names = [s['name'] for s in servers]
        assert 'filesystem' in names


class TestTriggerMap:
    def test_scrapling_in_trigger_map(self, inventory):
        trigger_map = inventory.get_trigger_map()
        assert 'scrape' in trigger_map
        assert 'scrapling' in trigger_map['scrape']

    def test_animation_in_trigger_map(self, inventory):
        trigger_map = inventory.get_trigger_map()
        assert 'animation' in trigger_map
        names = trigger_map['animation']
        assert 'animation-vocabulary' in names
        assert 'emil-design-eng' in names


class TestCapabilitySummary:
    def test_total_count(self, inventory):
        summary = inventory.capability_summary()
        assert summary['total'] >= 40  # At least 40 skills

    def test_has_skill_type(self, inventory):
        summary = inventory.capability_summary()
        assert 'skill' in summary['by_type']
