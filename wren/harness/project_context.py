"""Project context loader — reads WREN.md / CLAUDE.md from the sandbox workspace.

Injects project-level conventions, architecture decisions, and coding standards
into the planner agent so every conversation starts with the right project context.

Inspired by Claude Code's CLAUDE.md pattern, but extended with Wren-specific
sections for agent role preferences.

Supported files (checked in order):
  - WREN.md          (primary — Wren-native)
  - CLAUDE.md        (Claude Code compatibility)
  - .wren/config.md  (scoped config directory)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

_logger = logging.getLogger(__name__)

_CONTEXT_FILES = [
    'WREN.md',
    'CLAUDE.md',
    '.wren/config.md',
]


@dataclass
class ProjectContext:
    """Loaded project context from a workspace config file."""

    raw_content: str = ''
    source_file: str = ''
    found: bool = False

    # Extracted sections
    summary: str = ''
    coding_standards: str = ''
    architecture_notes: str = ''
    agent_preferences: dict[str, str] = field(default_factory=dict)

    @property
    def formatted(self) -> str:
        """Format the context as a prompt block for injection into an agent."""
        if not self.found or not self.raw_content:
            return ''
        sections = ['<project_context>']
        sections.append(self.raw_content)
        sections.append('</project_context>')
        return '\n'.join(sections)

    @property
    def short_summary(self) -> str:
        """First 300 chars of content or summary."""
        if self.summary:
            return self.summary[:300]
        if self.raw_content:
            # Take first non-empty lines
            lines = [l.strip() for l in self.raw_content.split('\n') if l.strip()]
            first_block = '\n'.join(lines[:5])
            return first_block[:300]
        return ''

    def to_dict(self) -> dict[str, Any]:
        return {
            'source_file': self.source_file,
            'found': self.found,
            'summary': self.short_summary,
            'coding_standards': self.coding_standards[:200] if self.coding_standards else '',
            'architecture_notes': self.architecture_notes[:200] if self.architecture_notes else '',
            'agent_preferences': self.agent_preferences,
        }


class ProjectContextLoader:
    """Reads project context files from the sandbox workspace.

    Uses the ExecutionSandbox to run shell commands (cat) to read files
    from the workspace directory, so it works in both local and remote
    sandbox environments.
    """

    def __init__(self, sandbox: Any) -> None:
        self._sandbox = sandbox
        self._cache: ProjectContext | None = None

    async def load(self, force: bool = False) -> ProjectContext:
        """Load project context from the workspace.

        Results are cached after first load. Set force=True to re-read.

        Returns a ProjectContext (always, even if no file is found).
        """
        if self._cache is not None and not force:
            return self._cache

        context = ProjectContext()

        for filename in _CONTEXT_FILES:
            content = await self._try_read_file(filename)
            if content:
                context.raw_content = content
                context.source_file = filename
                context.found = True
                self._parse_sections(context, content)
                _logger.info(
                    'ProjectContext: loaded from %s (%d chars)',
                    filename,
                    len(content),
                )
                break

        self._cache = context
        return context

    async def _try_read_file(self, filename: str) -> str | None:
        """Try to read a file from the sandbox workspace.

        Uses the sandbox shell to cat the file. Returns None if the
        file doesn't exist or can't be read.
        """
        if not self._sandbox:
            _logger.debug('ProjectContext: no sandbox available, skipping %s', filename)
            return None

        try:
            # Use workdir='.' to run from the sandbox's default working directory
            result = await self._sandbox.shell(f'cat {filename}', timeout_s=5.0)

            if result.success and result.stdout.strip():
                return result.stdout.strip()
            return None
        except Exception as e:
            _logger.debug('ProjectContext: could not read %s: %s', filename, e)
            return None

    @staticmethod
    def _parse_sections(context: ProjectContext, content: str) -> None:
        """Extract structured sections from the raw markdown content.

        Recognises common section headers and extracts agent preference blocks.
        """
        lines = content.split('\n')
        current_section = 'general'
        section_text: dict[str, list[str]] = {
            'general': [],
            'coding_standards': [],
            'architecture': [],
            'agent_prefs': [],
        }

        section_keywords = {
            'coding standards': 'coding_standards',
            'code style': 'coding_standards',
            'style guide': 'coding_standards',
            'architecture': 'architecture',
            'design': 'architecture',
            'technical decisions': 'architecture',
            'agent preferences': 'agent_prefs',
            'agent roles': 'agent_prefs',
            'model preferences': 'agent_prefs',
        }

        for line in lines:
            stripped = line.strip().lower()
            # Check for section headers (## Heading or ### Heading)
            heading_match = re.match(r'^#{1,3}\s+(.+)$', stripped)
            if heading_match:
                heading_text = heading_match.group(1).strip()
                matched_key = None
                for keyword, key in section_keywords.items():
                    if keyword in heading_text:
                        matched_key = key
                        break
                current_section = matched_key or 'general'
                continue

            section_text[current_section].append(line)

        context.coding_standards = '\n'.join(
            section_text.get('coding_standards', [])
        ).strip()
        context.architecture_notes = '\n'.join(
            section_text.get('architecture', [])
        ).strip()

        # Parse agent preferences from the agent_prefs section
        prefs_text = '\n'.join(section_text.get('agent_prefs', []))
        for line in prefs_text.split('\n'):
            match = re.match(r'^[-*]\s+(\w+)\s*[=:]\s*(.+)$', line.strip())
            if match:
                role = match.group(1).strip().lower()
                model_pref = match.group(2).strip()
                context.agent_preferences[role] = model_pref
