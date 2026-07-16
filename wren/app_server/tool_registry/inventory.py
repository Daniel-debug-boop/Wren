"""Local tool and capability inventory scanner.

Scans the local filesystem for installed skills, microagents, and
MCP tool registrations. Provides a unified view of what capabilities
are available.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

import wren

_logger = logging.getLogger(__name__)

GLOBAL_SKILLS_DIR = Path(wren.__file__).parent.parent / 'skills'
USER_MICROAGENTS_DIR = Path.home() / '.wren' / 'microagents'
PROJECT_MICROAGENTS_DIR = Path.cwd() / '.wren' / 'microagents'


class CapabilityEntry:
    """A single capability or tool in the inventory."""

    def __init__(
        self,
        name: str,
        capability_type: str,
        source: str,
        triggers: list[str] | None = None,
        description: str | None = None,
        file_path: str | None = None,
        mcp_servers: list[dict[str, Any]] | None = None,
    ):
        self.name = name
        self.type = capability_type  # 'skill', 'microagent', 'mcp_tool', 'builtin'
        self.source = source
        self.triggers = triggers or []
        self.description = description or ''
        self.file_path = file_path
        self.mcp_servers = mcp_servers or []

    def __repr__(self) -> str:
        return f'<CapabilityEntry {self.name} type={self.type} source={self.source}>'


class ToolInventory:
    """Scans local sources for installed tools, skills, and capabilities."""

    def __init__(self):
        self._cache: list[CapabilityEntry] | None = None

    def scan_all(self) -> list[CapabilityEntry]:
        """Scan all local sources and return unified capability list."""
        if self._cache is not None:
            return self._cache

        entries: list[CapabilityEntry] = []

        # 1. Global skills from skills/
        for skill_file in sorted(GLOBAL_SKILLS_DIR.rglob('*.md')):
            if skill_file.name == 'README.md':
                continue
            entry = self._parse_skill_file(skill_file, source='global')
            if entry:
                entries.append(entry)

        # 2. User microagents
        for micro_dir in [USER_MICROAGENTS_DIR, PROJECT_MICROAGENTS_DIR]:
            if micro_dir.exists():
                for mf in sorted(micro_dir.rglob('*.md')):
                    entry = self._parse_skill_file(mf, source='user')
                    if entry:
                        entries.append(entry)

        # 3. Built-in MCP tools (from default-tools.md)
        default_tools = GLOBAL_SKILLS_DIR / 'default-tools.md'
        if default_tools.exists():
            entry = self._parse_skill_file(default_tools, source='builtin')
            if entry:
                entries.append(entry)

        self._cache = entries
        return entries

    def invalidate_cache(self):
        self._cache = None

    def find_by_name(self, name: str) -> CapabilityEntry | None:
        for e in self.scan_all():
            if e.name == name:
                return e
        return None

    def search_by_keyword(self, keyword: str) -> list[CapabilityEntry]:
        """Find capabilities matching a keyword in name, triggers, or description."""
        kw = keyword.lower()
        results: list[CapabilityEntry] = []
        for e in self.scan_all():
            if kw in e.name.lower():
                results.append(e)
                continue
            for t in e.triggers:
                if kw in t.lower():
                    results.append(e)
                    break
            if kw in e.description.lower():
                results.append(e)
        return results

    def get_mcp_server_list(self) -> list[dict[str, Any]]:
        """Return all registered MCP stdio servers from skills."""
        servers: list[dict[str, Any]] = []
        for e in self.scan_all():
            servers.extend(e.mcp_servers)
        return servers

    def get_trigger_map(self) -> dict[str, list[str]]:
        """Build a mapping: trigger keyword -> capability names."""
        mapping: dict[str, list[str]] = {}
        for e in self.scan_all():
            for t in e.triggers:
                mapping.setdefault(t, []).append(e.name)
        return mapping

    def capability_summary(self) -> dict[str, Any]:
        """Return a structured summary of all capabilities."""
        entries = self.scan_all()
        return {
            'total': len(entries),
            'by_type': {
                t: len([e for e in entries if e.type == t])
                for t in {e.type for e in entries}
            },
            'by_source': {
                s: len([e for e in entries if e.source == s])
                for s in {e.source for e in entries}
            },
            'trigger_count': sum(len(e.triggers) for e in entries),
            'mcp_servers': self.get_mcp_server_list(),
            'capabilities': [
                {'name': e.name, 'type': e.type, 'triggers': e.triggers}
                for e in entries
            ],
        }

    def missing_capabilities(self, required_keywords: list[str]) -> list[str]:
        """Return keywords from the input list that have NO matching capability."""
        entries = self.scan_all()
        all_triggers: set[str] = set()
        all_names: set[str] = set()
        for e in entries:
            all_names.add(e.name.lower())
            for t in e.triggers:
                all_triggers.add(t.lower())

        missing: list[str] = []
        for kw in required_keywords:
            k = kw.lower()
            found = k in all_names or any(k in t for t in all_triggers)
            if not found:
                missing.append(kw)
        return missing

    def _parse_skill_file(self, file_path: Path, source: str) -> CapabilityEntry | None:
        """Parse a single skill markdown file into a CapabilityEntry."""
        try:
            text = file_path.read_text(encoding='utf-8')
        except Exception:
            _logger.debug(f'Cannot read {file_path}')
            return None

        if not text.startswith('---'):
            return None

        end = text.find('---', 3)
        if end == -1:
            return None

        try:
            fm = yaml.safe_load(text[3:end])
        except yaml.YAMLError:
            return None

        if not isinstance(fm, dict):
            return None

        name = fm.get('name') or file_path.stem
        triggers = fm.get('triggers') or []
        description = text[end + 3 :].strip()[:200] if end + 3 < len(text) else ''

        mcp_servers: list[dict[str, Any]] = []
        mcp_config = fm.get('mcp_tools', {})
        if isinstance(mcp_config, dict):
            stdio = mcp_config.get('stdio_servers', [])
            if isinstance(stdio, list):
                for srv in stdio:
                    if isinstance(srv, dict):
                        mcp_servers.append(srv)

        capability_type = 'skill'
        if source == 'user':
            capability_type = 'microagent'
        if mcp_servers:
            capability_type = 'mcp_tool'
        if name == 'default-tools':
            capability_type = 'builtin'

        return CapabilityEntry(
            name=name,
            capability_type=capability_type,
            source=source,
            triggers=triggers,
            description=description,
            file_path=str(file_path),
            mcp_servers=mcp_servers,
        )
