"""Skills exports."""

from wren.skills.skill import Skill, SkillLoader, SkillTrigger


class KeywordTrigger(SkillTrigger):
    """Trigger based on keywords."""

    pass


class TaskTrigger(SkillTrigger):
    """Trigger based on task type."""

    keywords: list[str] = []
    triggers: list[str] = []

    def matches(self, text: str) -> bool:
        """Check if text matches this trigger."""
        text_lower = text.lower()
        return any(trigger.lower() in text_lower for trigger in self.triggers)


__all__ = [
    "Skill",
    "SkillTrigger",
    "SkillLoader",
    "KeywordTrigger",
    "TaskTrigger",
]
