"""Skills exports."""

from wren.skills.skill import Skill, SkillTrigger, SkillLoader


class KeywordTrigger(SkillTrigger):
    """Trigger based on keywords."""

    pass


class TaskTrigger(SkillTrigger):
    """Trigger based on task type."""

    pass


__all__ = [
    "Skill",
    "SkillTrigger",
    "SkillLoader",
    "KeywordTrigger",
    "TaskTrigger",
]
