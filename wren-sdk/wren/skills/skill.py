"""Skill system for Wren SDK.

Skills are specialized prompts/workflows that enhance agent capabilities.
They can be auto-loaded based on triggers.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from wren.utils.models import WrenModel


class SkillTrigger(WrenModel):
    """Trigger for auto-activating a skill."""

    keywords: list[str]
    patterns: list[str] = []

    def matches(self, text: str) -> bool:
        """Check if text matches this trigger."""
        text_lower = text.lower()

        # Check keywords
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                return True

        # Check regex patterns
        for pattern in self.patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False


class Skill(WrenModel):
    """A skill that enhances agent capabilities."""

    name: str
    description: str
    content: str
    triggers: list[SkillTrigger] | None = None
    metadata: dict[str, Any] | None = None

    @property
    def has_triggers(self) -> bool:
        """Check if skill has auto-triggers."""
        return self.triggers is not None and len(self.triggers) > 0

    def matches(self, text: str) -> bool:
        """Check if text should activate this skill."""
        if not self.has_triggers:
            return True  # No triggers = always loaded

        return any(trigger.matches(text) for trigger in self.triggers)

    def to_prompt_section(self) -> str:
        """Convert skill to prompt section."""
        return f"""## Skill: {self.name}
{self.description}

{self.content}"""


class SkillLoader:
    """Loads skills from directories."""

    def __init__(self, *skill_dirs: str | Path):
        self._skill_dirs = [Path(d) for d in skill_dirs]

    def load_all(self) -> list[Skill]:
        """Load all skills from configured directories."""
        skills = []
        for skill_dir in self._skill_dirs:
            if skill_dir.exists():
                skills.extend(self._load_from_dir(skill_dir))
        return skills

    def load_matching(self, text: str) -> list[Skill]:
        """Load skills that match the given text."""
        all_skills = self.load_all()
        return [skill for skill in all_skills if skill.matches(text)]

    def _load_from_dir(self, directory: Path) -> list[Skill]:
        """Load skills from a directory."""
        skills = []

        for file_path in directory.glob("*.md"):
            skill = self._load_skill_file(file_path)
            if skill:
                skills.append(skill)

        return skills

    def _load_skill_file(self, file_path: Path) -> Skill | None:
        """Load a single skill from a markdown file."""
        try:
            content = file_path.read_text(encoding="utf-8")

            # Parse frontmatter
            triggers = None
            if content.startswith("---"):
                end_idx = content.find("---", 3)
                if end_idx != -1:
                    frontmatter = content[3:end_idx].strip()
                    content = content[end_idx + 3 :].strip()
                    triggers = self._parse_frontmatter(frontmatter)

            # Extract name and description
            name = file_path.stem
            description = ""

            # Try to extract from first heading
            lines = content.split("\n")
            for line in lines:
                if line.startswith("# "):
                    name = line[2:].strip()
                    break
                elif line.strip():
                    description = line.strip()
                    break

            return Skill(
                name=name,
                description=description or f"Skill: {name}",
                content=content,
                triggers=triggers,
            )

        except Exception as e:
            return None

    def _parse_frontmatter(self, frontmatter: str) -> SkillTrigger | None:
        """Parse YAML-like frontmatter for triggers."""
        keywords = []
        patterns = []

        for line in frontmatter.split("\n"):
            line = line.strip()
            if line.startswith("triggers:"):
                continue
            elif line.startswith("- "):
                trigger = line[2:].strip()
                if trigger.startswith("/") and trigger.endswith("/"):
                    patterns.append(trigger[1:-1])
                else:
                    keywords.append(trigger)

        if keywords or patterns:
            return SkillTrigger(keywords=keywords, patterns=patterns)

        return None
