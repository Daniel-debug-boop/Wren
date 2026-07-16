"""Web scraper for discovering open-source tools online.

Uses the Scrapling MCP tool (available as an external MCP server) to
search for open-source tools, fetch documentation, and extract
installation instructions. Falls back to direct HTTP fetching when
the Scrapling MCP is not available.
"""

import json
import logging
from typing import Any

import httpx

_logger = logging.getLogger(__name__)

# Registry of known open-source tool sources
TOOL_SOURCES = {
    'github': 'https://github.com/{owner}/{repo}',
    'npm': 'https://www.npmjs.com/package/{package}',
    'pypi': 'https://pypi.org/project/{package}',
    'crates': 'https://crates.io/crates/{package}',
}


class ToolDiscoveryResult:
    """Result of discovering a tool from the web."""

    def __init__(
        self,
        name: str,
        source_url: str,
        tool_type: str,
        description: str,
        installation: str | None = None,
        mcp_config: dict[str, Any] | None = None,
        skill_content: str | None = None,
        score: float = 0.0,
    ):
        self.name = name
        self.source_url = source_url
        self.tool_type = tool_type  # 'mcp_server', 'cli', 'library'
        self.description = description
        self.installation = installation
        self.mcp_config = mcp_config
        self.skill_content = skill_content
        self.score = score

    def __repr__(self) -> str:
        return (
            f'<ToolDiscoveryResult {self.name} type={self.tool_type} '
            f'score={self.score:.2f}>'
        )


class ToolScraper:
    """Scrapes the web for open-source tools matching a capability need."""

    def __init__(self):
        self._discovery_cache: dict[str, list[ToolDiscoveryResult]] = {}

    async def search_tool(
        self,
        capability: str,
        max_results: int = 5,
    ) -> list[ToolDiscoveryResult]:
        """Search for an open-source tool that provides the given capability.

        Uses web search and structured scraping to find tools.
        """
        cache_key = capability.lower().strip()
        if cache_key in self._discovery_cache:
            return self._discovery_cache[cache_key][:max_results]

        results: list[ToolDiscoveryResult] = []

        # Try multiple strategies in parallel
        try:
            results.extend(await self._search_github_mcp_servers(capability))
        except Exception as e:
            _logger.debug(f'GitHub MCP search failed: {e}')

        try:
            results.extend(await self._search_web_for_tool(capability))
        except Exception as e:
            _logger.debug(f'Web search failed: {e}')

        try:
            results.extend(await self._search_smithery_registry(capability))
        except Exception as e:
            _logger.debug(f'Smithery search failed: {e}')

        # Deduplicate and score
        seen: set[str] = set()
        unique: list[ToolDiscoveryResult] = []
        for r in results:
            if r.name.lower() not in seen:
                seen.add(r.name.lower())
                unique.append(r)

        unique.sort(key=lambda r: r.score, reverse=True)

        self._discovery_cache[cache_key] = unique
        return unique[:max_results]

    async def fetch_tool_details(
        self, tool: ToolDiscoveryResult
    ) -> ToolDiscoveryResult:
        """Fetch detailed information about a discovered tool."""
        if tool.skill_content:
            return tool

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(tool.source_url, follow_redirects=True)
                if resp.status_code == 200:
                    text = resp.text
                    tool.description = (
                        self._extract_description(text) or tool.description
                    )
                    tool.installation = self._extract_installation(text)
        except Exception as e:
            _logger.debug(f'Failed to fetch details for {tool.name}: {e}')

        return tool

    async def _search_github_mcp_servers(
        self, capability: str
    ) -> list[ToolDiscoveryResult]:
        """Search GitHub for MCP servers matching the capability."""
        query = f'{capability} mcp server'
        url = (
            'https://api.github.com/search/repositories'
            f'?q={query}&sort=stars&order=desc&per_page=5'
        )

        results: list[ToolDiscoveryResult] = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    url,
                    headers={'Accept': 'application/vnd.github.v3+json'},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get('items', []):
                        name = item.get('full_name', '')
                        desc = item.get('description') or ''
                        stars = item.get('stargazers_count', 0)
                        repo_url = item.get('html_url', '')
                        topics = item.get('topics', [])

                        mcp_config = self._infer_mcp_config(name, repo_url, topics)

                        results.append(
                            ToolDiscoveryResult(
                                name=name.split('/')[-1] if '/' in name else name,
                                source_url=repo_url,
                                tool_type='mcp_server',
                                description=desc,
                                score=min(1.0, stars / 1000) * 0.9
                                + (0.1 if 'mcp' in desc.lower() else 0),
                                mcp_config=mcp_config,
                            )
                        )
        except Exception as e:
            _logger.debug(f'GitHub API search failed: {e}')

        return results

    async def _search_web_for_tool(self, capability: str) -> list[ToolDiscoveryResult]:
        """Search the web using Scrapling-style fetch for tool docs."""
        search_urls = [
            f'https://github.com/topics/{capability}-mcp',
            'https://github.com/topics/mcp-server',
            f'https://pypi.org/search/?q={capability}+mcp',
        ]

        results: list[ToolDiscoveryResult] = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for url in search_urls:
                try:
                    resp = await client.get(url, follow_redirects=True)
                    if resp.status_code == 200:
                        extracted = self._extract_tool_links(resp.text, url)
                        results.extend(extracted)
                except Exception:
                    continue

        return results

    async def _search_smithery_registry(
        self, capability: str
    ) -> list[ToolDiscoveryResult]:
        """Search Smithery.ai registry for MCP servers."""
        url = f'https://registry.smithery.ai/servers?search={capability}'

        results: list[ToolDiscoveryResult] = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, follow_redirects=True)
                if resp.status_code == 200:
                    text = resp.text
                    import re

                    server_names = re.findall(r'/servers/([a-zA-Z0-9_-]+)', text)
                    for name in set(server_names[:5]):
                        results.append(
                            ToolDiscoveryResult(
                                name=name,
                                source_url=f'https://smithery.ai/server/{name}',
                                tool_type='mcp_server',
                                description=f'MCP server: {name}',
                                mcp_config={
                                    'name': name,
                                    'command': 'npx',
                                    'args': [
                                        '-y',
                                        '@smithery/cli@latest',
                                        'run',
                                        name,
                                    ],
                                },
                                score=0.7,
                            )
                        )
        except Exception as e:
            _logger.debug(f'Smithery search failed: {e}')

        return results

    def _infer_mcp_config(
        self,
        repo_full_name: str,
        repo_url: str,
        topics: list[str],
    ) -> dict[str, Any] | None:
        """Try to infer MCP stdio config from repo metadata."""
        repo_name = (
            repo_full_name.split('/')[-1] if '/' in repo_full_name else repo_full_name
        )

        if any(t in topics for t in ['python', 'mcp']):
            return {
                'name': repo_name,
                'command': 'uvx',
                'args': ['--from', 'git+{repo_url}', repo_name],
            }

        if any(t in topics for t in ['typescript', 'javascript', 'node']):
            return {
                'name': repo_name,
                'command': 'npx',
                'args': ['-y', repo_name],
            }

        if any(t in topics for t in ['go', 'golang']):
            return {
                'name': repo_name,
                'command': 'go',
                'args': ['run', f'{repo_url}'],
            }

        return None

    def _extract_description(self, html: str) -> str | None:
        """Extract meta description from HTML."""
        import re

        match = re.search(
            r'<meta\s+name="description"\s+content="([^"]+)"',
            html,
            re.IGNORECASE,
        )
        if match:
            return match.group(1)[:300]
        match = re.search(
            r'<meta\s+property="og:description"\s+content="([^"]+)"',
            html,
            re.IGNORECASE,
        )
        if match:
            return match.group(1)[:300]
        return None

    def _extract_installation(self, html: str) -> str | None:
        """Extract installation instructions from HTML."""
        import re

        # Look for pip install
        pip_match = re.search(r'pip install ([a-zA-Z0-9_.-]+)', html)
        if pip_match:
            return f'pip install {pip_match.group(1)}'

        # Look for npm install
        npm_match = re.search(r'npm install ([a-zA-Z0-9_.@/-]+)', html)
        if npm_match:
            return f'npm install {npm_match.group(1)}'

        # Look for brew install
        brew_match = re.search(r'brew install ([a-zA-Z0-9_.-]+)', html)
        if brew_match:
            return f'brew install {brew_match.group(1)}'

        # Look for cargo install
        cargo_match = re.search(r'cargo install ([a-zA-Z0-9_.-]+)', html)
        if cargo_match:
            return f'cargo install {cargo_match.group(1)}'

        return None

    def _extract_tool_links(
        self, html: str, source_url: str
    ) -> list[ToolDiscoveryResult]:
        """Extract tool links from a search results page."""
        import re

        results: list[ToolDiscoveryResult] = []

        if 'github.com/topics' in source_url:
            repo_pattern = r'href="/repos/([^"]+)"'
            for match in re.finditer(repo_pattern, html):
                path = match.group(1)
                parts = path.strip('/').split('/')
                if len(parts) >= 2:
                    owner, repo = parts[0], parts[1]
                    results.append(
                        ToolDiscoveryResult(
                            name=repo,
                            source_url=f'https://github.com/{owner}/{repo}',
                            tool_type='mcp_server',
                            description=f'GitHub repo: {owner}/{repo}',
                            score=0.5,
                        )
                    )

        return results

    def generate_skill_from_tool(
        self, tool: ToolDiscoveryResult, triggers: list[str] | None = None
    ) -> str:
        """Generate a complete microagent skill file from a discovered tool."""
        if triggers is None:
            trigs = [tool.name.lower(), tool.name.split('-')[0].lower()]
        else:
            trigs = triggers

        mcp_yaml = ''
        if tool.mcp_config:
            mcp_yaml = (
                f'mcp_tools:\n'
                f'  stdio_servers:\n'
                f'    - name: "{tool.mcp_config["name"]}"\n'
                f'      command: "{tool.mcp_config["command"]}"\n'
                f'      args: {json.dumps(tool.mcp_config.get("args", []))}\n'
            )

        installation = ''
        if tool.installation:
            installation = f'\n## Installation\n\n```bash\n{tool.installation}\n```\n'

        content = f"""---
name: {tool.name}
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
{chr(10).join(f'  - {t}' for t in trigs)}
{mcp_yaml}---

# {tool.name}

{tool.description}

**Source:** {tool.source_url}
**Auto-discovered:** true
{installation}

## Usage

This tool was dynamically discovered by the Tool Registry to provide
**{tool.name}** capabilities.

## When to use

- When the task mentions: {', '.join(trigs)}
- When existing tools lack {tool.name} functionality
"""
        return content
