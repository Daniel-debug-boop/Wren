"""Skill/procedure library.

Indexes available skills, procedures, and known solution patterns.
Provides lookup by name, tag, or vector similarity.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

from wren.harness.knowledge.vector_store import VectorStore

_logger = logging.getLogger(__name__)


@dataclass
class SkillEntry:
    name: str
    description: str
    content: str  # full skill markdown/code
    tags: list[str] = field(default_factory=list)
    usage_count: int = 0
    source_path: str = ''


class SkillLibrary:
    """Indexes skills from disk and provides retrieval.

    Scans skill files from standard locations and makes them
    searchable via vector store.
    """

    SKILL_PATHS = [
        '/home/daniel/.agents/skills',
        '/home/daniel/.config/opencode/skills',
        '/home/daniel/.claude/skills',
    ]

    def __init__(self, vector_store: VectorStore | None = None) -> None:
        self._vs = vector_store or VectorStore()
        self._skills: dict[str, SkillEntry] = {}
        self._loaded = False

    # ── Loading ──────────────────────────────────────────────────

    def load_all(self, force: bool = False) -> int:
        if self._loaded and not force:
            return len(self._skills)
        count = 0
        for path in self.SKILL_PATHS:
            if not os.path.isdir(path):
                continue
            for root, _dirs, files in os.walk(path):
                for fn in files:
                    if fn.endswith('.md'):
                        fp = os.path.join(root, fn)
                        count += self._load_skill(fp)
        self._loaded = True
        _logger.info('SkillLibrary: loaded %d skills', count)
        return count

    def _load_skill(self, filepath: str) -> int:
        try:
            with open(filepath) as f:
                content = f.read()
            name = os.path.splitext(os.path.basename(filepath))[0]
            desc = ''
            tags: list[str] = []
            # Extract frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    front = parts[1]
                    desc = self._extract_field(front, 'description')
                    # Extract first line as fallback description
                    if not desc:
                        for line in parts[2].strip().split('\n'):
                            if line.strip():
                                desc = line.strip()[:200]
                                break
            else:
                desc = content.strip().split('\n')[0][:200]

            entry = SkillEntry(
                name=name,
                description=desc or name,
                content=content,
                tags=tags or [name],
                source_path=filepath,
            )
            self._skills[name] = entry
            self._vs.insert(
                content=f'{name}: {desc}',
                source='skill_library',
                tags=[name] + tags,
                metadata={'path': filepath, 'name': name},
            )
            return 1
        except Exception as exc:
            _logger.warning('SkillLibrary: failed to load %s: %s', filepath, exc)
            return 0

    @staticmethod
    def _extract_field(frontmatter: str, field_name: str) -> str:
        for line in frontmatter.split('\n'):
            if line.strip().startswith(f'{field_name}:'):
                val = line.split(':', 1)[1].strip().strip('"\'')
                return val
        return ''

    # ── Lookup ───────────────────────────────────────────────────

    def get(self, name: str) -> SkillEntry | None:
        return self._skills.get(name)

    def search(self, query: str, top_k: int = 3) -> list[tuple[SkillEntry, float]]:
        results = self._vs.search(query, top_k=top_k, min_score=0.0, tags=[])
        mapped: list[tuple[SkillEntry, float]] = []
        for entry, score in results:
            name = entry.metadata.get('name', '')
            skill = self._skills.get(name)
            if skill:
                mapped.append((skill, score))
                skill.usage_count += 1
        return mapped

    def all(self) -> list[SkillEntry]:
        return list(self._skills.values())

    def record_usage(self, name: str) -> None:
        skill = self._skills.get(name)
        if skill:
            skill.usage_count += 1
