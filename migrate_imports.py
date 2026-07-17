"""Migration script: openhands -> wren imports.

This script handles the mechanical import replacement for the wren/ codebase.
Run from repo root: python migrate_imports.py
"""

import re
import sys
from pathlib import Path

# Mapping of old imports to new imports
# SDK imports: openhands.sdk.* -> wren.*
SDK_MAPPINGS = {
    'from openhands.sdk import': 'from wren import',
    'from openhands.sdk.agent': 'from wren.agent',
    'from openhands.sdk.context': 'from wren.context',
    'from openhands.sdk.conversation': 'from wren.conversation',
    'from openhands.sdk.event': 'from wren.event',
    'from openhands.sdk.hooks': 'from wren.hooks',
    'from openhands.sdk.llm': 'from wren.llm',
    'from openhands.sdk.mcp': 'from wren.mcp',
    'from openhands.sdk.plugin': 'from wren.plugin',
    'from openhands.sdk.profiles': 'from wren.profiles',
    'from openhands.sdk.secret': 'from wren.secret',
    'from openhands.sdk.security': 'from wren.security',
    'from openhands.sdk.settings': 'from wren.settings',
    'from openhands.sdk.skills': 'from wren.skills',
    'from openhands.sdk.subagent': 'from wren.subagent',
    'from openhands.sdk.tool': 'from wren.tool',
    'from openhands.sdk.utils': 'from wren.utils',
    'from openhands.sdk.workspace': 'from wren.workspace',
    # Specific module mappings
    'from openhands.sdk.utils.models import': 'from wren.utils.models import',
    'from openhands.sdk.utils.redact import': 'from wren.utils.redact import',
    'from openhands.sdk.utils.paging import': 'from wren.utils.paging import',
    'from openhands.sdk.utils.truncate import': 'from wren.utils.truncate import',
    'from openhands.sdk.utils.datetime import': 'from wren.utils.datetime import',
    'from openhands.sdk.utils.github import': 'from wren.utils.github import',
    'from openhands.sdk.utils.json import': 'from wren.utils.json import',
    'from openhands.sdk.utils.path import': 'from wren.utils.path import',
    'from openhands.sdk.utils.async_utils import': 'from wren.utils.async_utils import',
    'from openhands.sdk.utils.command import': 'from wren.utils.command import',
    'from openhands.sdk.utils.cipher import': 'from wren.utils.cipher import',
    'from openhands.sdk.utils.deprecation import': 'from wren.utils.deprecation import',
    'from openhands.sdk.utils.visualize import': 'from wren.utils.visualize import',
    'from openhands.sdk.llm.llm import': 'from wren.llm.client import',
    'from openhands.sdk.llm.message import': 'from wren.llm.message import',
    'from openhands.sdk.llm.streaming import': 'from wren.llm.streaming import',
    'from openhands.sdk.llm.fallback_strategy import': 'from wren.llm.fallback_strategy import',
    'from openhands.sdk.llm.llm_registry import': 'from wren.llm.registry import',
    'from openhands.sdk.llm.llm_profile_store import': 'from wren.llm.profile_store import',
    'from openhands.sdk.llm.auth': 'from wren.llm.auth',
    'from openhands.sdk.llm.exceptions': 'from wren.llm.exceptions',
    'from openhands.sdk.llm.mixins': 'from wren.llm.mixins',
    'from openhands.sdk.llm.options': 'from wren.llm.options',
    'from openhands.sdk.llm.router': 'from wren.llm.router',
    'from openhands.sdk.llm.utils': 'from wren.llm.utils',
    'from openhands.sdk.tool.tool import': 'from wren.tool.base import',
    'from openhands.sdk.tool.spec import': 'from wren.tool.base import',
    'from openhands.sdk.tool.schema import': 'from wren.tool.base import',
    'from openhands.sdk.tool.registry import': 'from wren.tool.registry import',
    'from openhands.sdk.tool.client_tool import': 'from wren.tool.client_tool import',
    'from openhands.sdk.tool.builtins': 'from wren.tool.builtins',
    'from openhands.sdk.conversation.conversation import': 'from wren.conversation.conversation import',
    'from openhands.sdk.conversation.base import': 'from wren.conversation.base import',
    'from openhands.sdk.conversation.state import': 'from wren.conversation.state import',
    'from openhands.sdk.conversation.stats import': 'from wren.conversation.stats import',
    'from openhands.sdk.conversation.event_store import': 'from wren.event.store import',
    'from openhands.sdk.conversation.types import': 'from wren.conversation.types import',
    'from openhands.sdk.conversation.exceptions import': 'from wren.conversation.exceptions import',
    'from openhands.sdk.conversation.request import': 'from wren.conversation.request import',
    'from openhands.sdk.conversation.response_utils import': 'from wren.conversation.response_utils import',
    'from openhands.sdk.conversation.secret_registry import': 'from wren.conversation.secret_registry import',
    'from openhands.sdk.conversation.stuck_detector import': 'from wren.conversation.stuck_detector import',
    'from openhands.sdk.conversation.title_utils import': 'from wren.conversation.title_utils import',
    'from openhands.sdk.conversation.cancellation import': 'from wren.conversation.cancellation import',
    'from openhands.sdk.conversation.fifo_lock import': 'from wren.conversation.fifo_lock import',
    'from openhands.sdk.conversation.resource_lock_manager import': 'from wren.conversation.resource_lock_manager import',
    'from openhands.sdk.conversation.persistence_const import': 'from wren.conversation.persistence_const import',
    'from openhands.sdk.conversation.goal': 'from wren.conversation.goal',
    'from openhands.sdk.conversation.impl': 'from wren.conversation.impl',
    'from openhands.sdk.conversation.visualizer': 'from wren.conversation.visualizer',
    'from openhands.sdk.context.agent_context import': 'from wren.context.context import',
    'from openhands.sdk.context.condenser': 'from wren.context.condenser',
    'from openhands.sdk.context.prompts': 'from wren.context.prompts',
    'from openhands.sdk.context.view': 'from wren.context.view',
    'from openhands.sdk.agent.agent import': 'from wren.agent.agent import',
    'from openhands.sdk.agent.base import': 'from wren.agent.base import',
    'from openhands.sdk.agent.acp_agent import': 'from wren.agent.acp_agent import',
    'from openhands.sdk.agent.critic_mixin import': 'from wren.agent.critic_mixin import',
    'from openhands.sdk.agent.parallel_executor import': 'from wren.agent.parallel_executor import',
    'from openhands.sdk.agent.response_dispatch import': 'from wren.agent.response_dispatch import',
    'from openhands.sdk.workspace.base import': 'from wren.workspace.base import',
    'from openhands.sdk.workspace.workspace import': 'from wren.workspace.workspace import',
    'from openhands.sdk.workspace.local import': 'from wren.workspace.local import',
    'from openhands.sdk.workspace.repo import': 'from wren.workspace.repo import',
    'from openhands.sdk.workspace.models import': 'from wren.workspace.models import',
    'from openhands.sdk.workspace.remote': 'from wren.workspace.remote',
    'from openhands.sdk.hooks.config import': 'from wren.hooks.config import',
    'from openhands.sdk.hooks.conversation_hooks import': 'from wren.hooks.conversation_hooks import',
    'from openhands.sdk.hooks.executor import': 'from wren.hooks.executor import',
    'from openhands.sdk.hooks.manager import': 'from wren.hooks.manager import',
    'from openhands.sdk.hooks.types import': 'from wren.hooks.types import',
    'from openhands.sdk.settings.model import': 'from wren.settings.model import',
    'from openhands.sdk.settings.metadata import': 'from wren.settings.metadata import',
    'from openhands.sdk.settings.acp_providers import': 'from wren.settings.acp_providers import',
    'from openhands.sdk.settings.api_models import': 'from wren.settings.api_models import',
    'from openhands.sdk.mcp.client import': 'from wren.mcp.client import',
    'from openhands.sdk.mcp.tool import': 'from wren.mcp.tool import',
    'from openhands.sdk.mcp.definition import': 'from wren.mcp.definition import',
    'from openhands.sdk.mcp.exceptions import': 'from wren.mcp.exceptions import',
    'from openhands.sdk.mcp.utils import': 'from wren.mcp.utils import',
    'from openhands.sdk.skills.skill import': 'from wren.skills.skill import',
    'from openhands.sdk.skills.trigger import': 'from wren.skills.trigger import',
    'from openhands.sdk.skills.execute import': 'from wren.skills.execute import',
    'from openhands.sdk.skills.fetch import': 'from wren.skills.fetch import',
    'from openhands.sdk.skills.installed import': 'from wren.skills.installed import',
    'from openhands.sdk.skills.types import': 'from wren.skills.types import',
    'from openhands.sdk.skills.utils import': 'from wren.skills.utils import',
    'from openhands.sdk.skills.exceptions import': 'from wren.skills.exceptions import',
    'from openhands.sdk.subagent.load import': 'from wren.subagent.load import',
    'from openhands.sdk.subagent.registry import': 'from wren.subagent.registry import',
    'from openhands.sdk.subagent.schema import': 'from wren.subagent.schema import',
    'from openhands.sdk.plugin.discovery import': 'from wren.plugin.discovery import',
    'from openhands.sdk.plugin.fetch import': 'from wren.plugin.fetch import',
    'from openhands.sdk.plugin.installed import': 'from wren.plugin.installed import',
    'from openhands.sdk.plugin.loader import': 'from wren.plugin.loader import',
    'from openhands.sdk.plugin.plugin import': 'from wren.plugin.plugin import',
    'from openhands.sdk.plugin.source import': 'from wren.plugin.source import',
    'from openhands.sdk.plugin.types import': 'from wren.plugin.types import',
    'from openhands.sdk.profiles.agent_profile import': 'from wren.profiles.agent_profile import',
    'from openhands.sdk.profiles.agent_profile_store import': 'from wren.profiles.agent_profile_store import',
    'from openhands.sdk.profiles.profile_refs import': 'from wren.profiles.profile_refs import',
    'from openhands.sdk.profiles.resolver import': 'from wren.profiles.resolver import',
    'from openhands.sdk.profiles.seed import': 'from wren.profiles.seed import',
    'from openhands.sdk.secret.secrets import': 'from wren.secret.secrets import',
    'from openhands.sdk.security.analyzer import': 'from wren.security.analyzer import',
    'from openhands.sdk.security.confirmation_policy import': 'from wren.security.confirmation_policy import',
    'from openhands.sdk.security.ensemble import': 'from wren.security.ensemble import',
    'from openhands.sdk.security.llm_analyzer import': 'from wren.security.llm_analyzer import',
    'from openhands.sdk.security.risk import': 'from wren.security.risk import',
    'from openhands.sdk.security.shell_parser import': 'from wren.security.shell_parser import',
    'from openhands.sdk.security.defense_in_depth': 'from wren.security.defense_in_depth',
    'from openhands.sdk.security.grayswan': 'from wren.security.grayswan',
    'from openhands.sdk.git': 'from wren.git',
    'from openhands.sdk.io': 'from wren.io',
    'from openhands.sdk.logger': 'from wren.logger',
    'from openhands.sdk.marketplace': 'from wren.marketplace',
    'from openhands.sdk.observability': 'from wren.observability',
    'from openhands.sdk.testing': 'from wren.testing',
}

# Agent server imports: wren.agent_server.* -> wren.agent_server.*
# These need stubs since we're not building wren-server yet
AGENT_SERVER_MAPPINGS = {
    'from wren.agent_server.env_parser import': 'from wren.agent_server.env_parser import',
    'from wren.agent_server.models import': 'from wren.agent_server.models import',
    'from wren.agent_server.utils import': 'from wren.agent_server.utils import',
}

# Tools imports: openhands.tools.* -> wren.tools.*
TOOLS_MAPPINGS = {
    'from openhands.tools.preset.default import': 'from wren.tools.preset.default import',
    'from openhands.tools.preset.planning import': 'from wren.tools.preset.planning import',
    'from openhands import tools': 'from wren import tools',
}


def migrate_file(filepath: Path, dry_run: bool = False) -> list[str]:
    """Migrate imports in a single file."""
    content = filepath.read_text(encoding='utf-8')
    original = content
    changes = []

    # Apply SDK mappings
    for old, new in SDK_MAPPINGS.items():
        if old in content:
            content = content.replace(old, new)
            changes.append(f'  {old} -> {new}')

    # Apply agent_server mappings
    for old, new in AGENT_SERVER_MAPPINGS.items():
        if old in content:
            content = content.replace(old, new)
            changes.append(f'  {old} -> {new}')

    # Apply tools mappings
    for old, new in TOOLS_MAPPINGS.items():
        if old in content:
            content = content.replace(old, new)
            changes.append(f'  {old} -> {new}')

    if content != original:
        if not dry_run:
            filepath.write_text(content, encoding='utf-8')
        return changes

    return []


def main():
    dry_run = '--dry-run' in sys.argv
    repo_root = Path('/home/daniel/Downloads/OpenHands-main')
    wren_dir = repo_root / 'wren'

    if dry_run:
        print('DRY RUN - no files will be modified\n')

    total_changes = 0
    files_changed = 0

    for py_file in sorted(wren_dir.rglob('*.py')):
        changes = migrate_file(py_file, dry_run=dry_run)
        if changes:
            files_changed += 1
            total_changes += len(changes)
            rel = py_file.relative_to(repo_root)
            print(f'\n{rel}:')
            for change in changes:
                print(change)

    print(f'\n{"=" * 60}')
    print(f'Files changed: {files_changed}')
    print(f'Import replacements: {total_changes}')

    if dry_run:
        print('\nRun without --dry-run to apply changes')


if __name__ == '__main__':
    main()
