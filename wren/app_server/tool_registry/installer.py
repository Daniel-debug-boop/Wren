"""Tool and skill installer.

Handles writing new skill files to disk, registering MCP servers,
and validating installed tools.
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

import wren
from wren.app_server.tool_registry.inventory import ToolInventory

_logger = logging.getLogger(__name__)

USER_MICROAGENTS_DIR = Path.home() / '.wren' / 'microagents'
GLOBAL_SKILLS_DIR = Path(wren.__file__).parent.parent / 'skills'


class ToolInstaller:
    """Installs discovered tools as skills and MCP configurations."""

    def __init__(self, inventory: ToolInventory | None = None):
        self.inventory = inventory or ToolInventory()

    def install_skill(
        self,
        name: str,
        content: str,
        target_dir: str = 'user',
    ) -> Path:
        """Write a skill/microagent file to the appropriate directory.

        Args:
            name: Skill name (used as filename stem).
            content: Full markdown content with YAML frontmatter.
            target_dir: 'user' for ~/.wren/microagents/, 'global' for skills/

        Returns:
            Path to the installed skill file.

        Raises:
            OSError: If the file cannot be written.
        """
        if target_dir == 'global':
            dest_dir = GLOBAL_SKILLS_DIR
        else:
            dest_dir = USER_MICROAGENTS_DIR

        dest_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize filename
        safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in name)
        if not safe_name:
            safe_name = 'unnamed_skill'
        file_path = dest_dir / f'{safe_name}.md'

        file_path.write_text(content, encoding='utf-8')
        _logger.info(f'Installed skill: {file_path}')

        # Invalidate inventory cache
        self.inventory.invalidate_cache()

        return file_path

    def install_mcp_server(
        self,
        name: str,
        command: str,
        args: list[str] | None = None,
    ) -> str:
        """Install a MCP stdio server by adding it to a skill file.

        Rather than modifying config files directly, this appends the
        MCP server definition to a new or existing skill file that
        registers it via the standard skill-based MCP mechanism.

        Args:
            name: MCP server name.
            command: CLI command to launch the server.
            args: Arguments for the command.

        Returns:
            Path to the skill file that registers this MCP server.
        """
        args = args or []

        skill_name = f'mcp-{name}'
        content = f'''---
name: {skill_name}
type: repo
version: 1.0.0
agent: CodeActAgent
mcp_tools:
  stdio_servers:
    - name: "{name}"
      command: "{command}"
      args: {json.dumps(args)}
---

# MCP Server: {name}

Auto-installed MCP server providing **{name}** capabilities.
'''
        skill_path = self.install_skill(skill_name, content)
        return str(skill_path)

    def install_python_package(self, package_name: str) -> bool:
        """Install a Python package using pip.

        Args:
            package_name: Name of the PyPI package.

        Returns:
            True if installation succeeded.
        """
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    '-m',
                    'pip',
                    'install',
                    '--quiet',
                    package_name,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                _logger.info(f'Installed Python package: {package_name}')
                return True

            _logger.warning(f'Failed to install {package_name}: {result.stderr}')
            return False
        except subprocess.TimeoutExpired:
            _logger.warning(f'Installation of {package_name} timed out')
            return False
        except Exception as e:
            _logger.warning(f'Installation of {package_name} failed: {e}')
            return False

    def install_npm_package(self, package_name: str) -> bool:
        """Install an npm package globally.

        Args:
            package_name: Name of the npm package.

        Returns:
            True if installation succeeded.
        """
        try:
            result = subprocess.run(
                ['npm', 'install', '--global', '--quiet', package_name],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                _logger.info(f'Installed npm package: {package_name}')
                return True

            _logger.warning(
                f'Failed to install npm package {package_name}: {result.stderr}'
            )
            return False
        except subprocess.TimeoutExpired:
            _logger.warning(f'npm installation of {package_name} timed out')
            return False
        except Exception as e:
            _logger.warning(f'npm installation of {package_name} failed: {e}')
            return False

    def uninstall_skill(self, name: str) -> bool:
        """Remove a skill by name from both user and global dirs.

        Args:
            name: Skill name to remove.

        Returns:
            True if a file was found and removed.
        """
        safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in name)
        found = False

        for search_dir in [USER_MICROAGENTS_DIR, GLOBAL_SKILLS_DIR]:
            candidates = list(search_dir.rglob(f'{safe_name}.md'))
            if search_dir.name == 'skills':
                candidates = [search_dir / f'{safe_name}.md']
            for fp in candidates:
                try:
                    fp.unlink()
                    _logger.info(f'Removed skill: {fp}')
                    found = True
                except OSError as e:
                    _logger.warning(f'Failed to remove {fp}: {e}')

        if found:
            self.inventory.invalidate_cache()

        return found

    def list_installable_mcp_servers(self) -> list[dict[str, Any]]:
        """List well-known MCP servers available for installation,
        sourced from the community registry.
        """
        return [
            {
                'name': 'fetch',
                'description': 'Web page content fetcher for LLMs',
                'command': 'uvx',
                'args': ['mcp-server-fetch'],
                'source': 'https://github.com/modelcontextprotocol/servers',
            },
            {
                'name': 'playwright',
                'description': 'Browser automation with Playwright',
                'command': 'npx',
                'args': ['-y', '@playwright/mcp'],
                'source': 'https://github.com/microsoft/playwright-mcp',
            },
            {
                'name': 'filesystem',
                'description': 'Filesystem access and manipulation',
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-filesystem'],
                'source': 'https://github.com/modelcontextprotocol/servers',
            },
            {
                'name': 'github',
                'description': 'GitHub API integration',
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-github'],
                'source': 'https://github.com/modelcontextprotocol/servers',
            },
            {
                'name': 'slack',
                'description': 'Slack workspace integration',
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-slack'],
                'source': 'https://github.com/modelcontextprotocol/servers',
            },
            {
                'name': 'sqlite',
                'description': 'SQLite database exploration',
                'command': 'uvx',
                'args': ['mcp-server-sqlite'],
                'source': 'https://github.com/modelcontextprotocol/servers',
            },
            {
                'name': 'postgres',
                'description': 'PostgreSQL database exploration',
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-postgres'],
                'source': 'https://github.com/modelcontextprotocol/servers',
            },
            {
                'name': 'docker',
                'description': 'Docker container management',
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-docker'],
                'source': 'https://github.com/modelcontextprotocol/servers',
            },
            {
                'name': 'memory',
                'description': 'Persistent memory/knowledge graph',
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-memory'],
                'source': 'https://github.com/modelcontextprotocol/servers',
            },
        ]
