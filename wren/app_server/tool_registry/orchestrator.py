"""Orchestrator for dynamic tool selection and installation.

Ties together the inventory, scraper, and installer into a unified
pipeline:
1. Analyze task requirements for missing capabilities
2. Check local inventory
3. If missing, scrape web for open-source tools
4. Install best-match tools as skills
5. Return updated capability list
"""

import logging
from pathlib import Path
from typing import Any

from wren.app_server.tool_registry.installer import ToolInstaller
from wren.app_server.tool_registry.inventory import (
    CapabilityEntry,
    ToolInventory,
)
from wren.app_server.tool_registry.scraper import (
    ToolDiscoveryResult,
    ToolScraper,
)

_logger = logging.getLogger(__name__)


class ToolOrchestrator:
    """Unified orchestrator for dynamic tool discovery and installation.

    Usage:
        orch = ToolOrchestrator()
        result = await orch.ensure_capabilities(['database', 'postgresql'])
        if result['installed']:
            print(f'Installed: {result["installed"]}')
    """

    def __init__(
        self,
        inventory: ToolInventory | None = None,
        scraper: ToolScraper | None = None,
        installer: ToolInstaller | None = None,
    ):
        self.inventory = inventory or ToolInventory()
        self.scraper = scraper or ToolScraper()
        self.installer = installer or ToolInstaller()

    async def ensure_capabilities(
        self,
        required_capabilities: list[str],
        auto_install: bool = True,
        max_tools: int = 3,
    ) -> dict[str, Any]:
        """Ensure the given capabilities are available.

        Pipeline:
        1. Scan local inventory for matching capabilities
        2. Identify gaps
        3. Scrape web for missing capabilities
        4. Install best matches as skills (if auto_install=True)

        Args:
            required_capabilities: List of capability keywords needed.
            auto_install: If True, automatically install discovered tools.
            max_tools: Maximum number of tools to install per run.

        Returns:
            Dict with keys:
                - 'present': list of already-available cap names
                - 'missing': list of cap names with no match found
                - 'discovered': list of discovered tool results
                - 'installed': list of installed tool paths
                - 'summary': human-readable summary string
        """
        # Phase 1: Check local inventory
        present: list[CapabilityEntry] = []
        missing_keywords: list[str] = []
        for cap in required_capabilities:
            matches = self.inventory.search_by_keyword(cap)
            if matches:
                present.extend(matches)
                _logger.info(f'Capability "{cap}" found locally: {matches[0].name}')
            else:
                missing_keywords.append(cap)
                _logger.info(f'Capability "{cap}" not found locally')

        result: dict[str, Any] = {
            'present': list({e.name for e in present}),
            'missing': missing_keywords,
            'discovered': [],
            'installed': [],
            'errors': [],
        }

        if not missing_keywords:
            result['summary'] = 'All capabilities available locally'
            return result

        if not auto_install:
            result['summary'] = (
                f'Missing capabilities: {", ".join(missing_keywords)}. '
                'Set auto_install=True to install.'
            )
            return result

        # Phase 2: Scrape web for missing capabilities
        all_discovered: list[ToolDiscoveryResult] = []
        for cap in missing_keywords:
            try:
                tools = await self.scraper.search_tool(cap, max_results=3)
                all_discovered.extend(tools)
                _logger.info(f'Discovered {len(tools)} tools for "{cap}"')
            except Exception as e:
                error = f'Search for "{cap}" failed: {e}'
                _logger.warning(error)
                result['errors'].append(error)

        # Deduplicate and sort by score
        seen_names: set[str] = set()
        unique_sorted: list[ToolDiscoveryResult] = []
        for t in sorted(all_discovered, key=lambda x: x.score, reverse=True):
            if t.name.lower() not in seen_names:
                seen_names.add(t.name.lower())
                unique_sorted.append(t)

        discovered = unique_sorted[:max_tools]
        result['discovered'] = [
            {'name': t.name, 'url': t.source_url, 'score': t.score} for t in discovered
        ]

        if not discovered:
            result['summary'] = (
                f'No open-source tools found for: {", ".join(missing_keywords)}. '
                'Consider implementing a custom skill.'
            )
            return result

        # Phase 3: Install best matches
        for tool in discovered[:max_tools]:
            try:
                # Fetch detailed info
                tool = await self.scraper.fetch_tool_details(tool)

                # Generate skill content
                skill_content = self.scraper.generate_skill_from_tool(tool)

                # Write skill file
                skill_path = self.installer.install_skill(
                    name=tool.name,
                    content=skill_content,
                )
                result['installed'].append(str(skill_path))
                _logger.info(f'Installed skill from tool {tool.name} -> {skill_path}')

            except Exception as e:
                error = f'Failed to install {tool.name}: {e}'
                _logger.warning(error)
                result['errors'].append(error)

        present_names = result['present']
        installed_names = [Path(p).stem for p in result['installed']]
        still_missing = [
            c
            for c in missing_keywords
            if not any(c.lower() in n.lower() for n in installed_names)
        ]

        result['summary'] = (
            f'Capabilities available: {len(present_names)} present, '
            f'{len(installed_names)} installed, '
            f'{len(still_missing)} still missing'
        )

        return result

    async def analyze_task_for_tools(
        self,
        task_description: str,
        auto_install: bool = True,
    ) -> dict[str, Any]:
        """Analyze a task description and ensure required tools exist.

        Extracts capability keywords from the task, then runs the
        full ensure_capabilities pipeline.

        Args:
            task_description: Natural language task description.
            auto_install: If True, automatically install missing tools.

        Returns:
            Same structure as ensure_capabilities().
        """
        keywords = self._extract_capability_keywords(task_description)
        if not keywords:
            return {
                'present': [],
                'missing': [],
                'discovered': [],
                'installed': [],
                'summary': 'No capability keywords detected in task',
            }

        return await self.ensure_capabilities(keywords, auto_install=auto_install)

    def get_inventory(self) -> ToolInventory:
        return self.inventory

    def _extract_capability_keywords(self, text: str) -> list[str]:
        """Extract potential capability keywords from task text.

        Uses simple heuristics:
        - Nouns that appear after "use", "with", "need", "install"
        - Technical terms (docker, postgres, redis, kubernetes, etc.)
        - Words following "tool", "capability", "plugin"
        """
        text_lower = text.lower()
        keywords: list[str] = []

        # Direct extraction patterns
        import re

        # Look for known capability patterns
        patterns = [
            r'(?:use|with|need|install|require|missing)\s+([a-zA-Z][a-zA-Z0-9_-]+)',
            r'(?:tool|capability|plugin|integration)\s+(?:for|to|of)\s+([a-zA-Z][a-zA-Z0-9_-]+)',
            r'([a-zA-Z][a-zA-Z0-9_-]+)\s+(?:tool|server|plugin|integration)',
        ]

        for pat in patterns:
            for match in re.finditer(pat, text_lower):
                kw = match.group(1).strip()
                if len(kw) > 1 and kw not in ('the', 'and', 'for', 'this', 'that'):
                    keywords.append(kw)

        # Known tech keyword detection
        known_capabilities = [
            'docker',
            'kubernetes',
            'k8s',
            'postgres',
            'postgresql',
            'mysql',
            'redis',
            'mongodb',
            'sqlite',
            'elasticsearch',
            'aws',
            'gcp',
            'azure',
            'terraform',
            'helm',
            'nginx',
            'apache',
            'kafka',
            'rabbitmq',
            'prometheus',
            'grafana',
            'jenkins',
            'gitlab',
            'github',
            'slack',
            'jira',
            'pagerduty',
            'sentry',
            'datadog',
            'newrelic',
            'stripe',
            'sendgrid',
            'twilio',
            'discord',
            'telegram',
            'notion',
            'confluence',
            'openapi',
            'swagger',
            'graphql',
            'grpc',
            'rest',
            'selenium',
            'playwright',
            'cypress',
            'puppeteer',
            'pandas',
            'numpy',
            'scikit',
            'tensorflow',
            'pytorch',
            'opencv',
            'ffmpeg',
            'imagemagick',
            'latex',
            'pdflatex',
        ]

        for cap in known_capabilities:
            if cap in text_lower and cap not in keywords:
                keywords.append(cap)

        # Deduplicate
        return list(dict.fromkeys(keywords))
