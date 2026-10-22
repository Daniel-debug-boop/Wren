"""Skill Synthesizer — Auto-Generates Skills from Knowledge Gaps.

Detects when the agent lacks expertise in an area, researches the topic,
and generates a reusable skill file. This is the self-teaching capability
that lets the agent learn from its failures and gaps.

Usage:
    synthesizer = SkillSynthesizer()
    gap = synthesizer.detect_gap("I need to implement WebSocket reconnection")
    skill = synthesizer.synthesize_skill(gap)
    synthesizer.save_skill(skill)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import, class GapSeverity(Enum):
    """How critical the knowledge gap is."""

    CRITICAL = 'critical'  # Can't proceed without this knowledge
    HIGH = 'high'  # Will produce poor results without it
    MEDIUM = 'medium'  # Suboptimal but workable
    LOW = 'low'  # Minor gap, can improvise


class SkillComplexity(Enum):
    """Complexity of the generated skill."""

    TRIVIAL = 'trivial'  # 1-5 rules, single concept
    SIMPLE = 'simple'  # 5-15 rules, focused topic
    MODERATE = 'moderate'  # 15-30 rules, multi-concept
    COMPLEX = 'complex'  # 30+ rules, comprehensive guide


@dataclass
class KnowledgeGap:
    """A detected knowledge gap."""

    topic: str
    description: str
    severity: GapSeverity
    context: str  # What triggered the gap detection
    keywords: list[str] = field(default_factory=list)
    related_topics: list[str] = field(default_factory=list)
    confidence: float = 0.0  # How confident we are this is a real gap


@dataclass
class SynthesizedSkill:
    """A generated skill file."""

    name: str
    description: str
    content: str
    triggers: list[str]
    complexity: SkillComplexity
    source_gap: KnowledgeGap
    file_path: str | None = None
    verified: bool = False


class SkillSynthesizer:
    """Detects knowledge gaps and generates skills to fill them."""

    def __init__(self, skills_dir: str | None = None) -> None:
        if skills_dir is None:
            # Default to the skills directory in the repo
            skills_dir = str(Path(__file__).parent.parent.parent / 'skills')
        self._skills_dir = Path(skills_dir)
        self._existing_skills: set[str] = set()
        self._scan_existing_skills()

    def _scan_existing_skills(self) -> None:
        """Scan existing skills to avoid duplicates."""
        if self._skills_dir.exists():
            for f in self._skills_dir.glob('*.md'):
                self._existing_skills.add(f.stem)

    def detect_gap(
        self,
        task_description: str,
        error_output: str | None = None,
        context: str | None = None,
    ) -> KnowledgeGap | None:
        """Detect if a knowledge gap exists for the given task.

        Analyzes the task description and any error output to determine
        if the agent lacks knowledge in a specific area.

        Returns:
            KnowledgeGap if a gap is detected, None otherwise.
        """
        # Keywords that indicate potential knowledge gaps
        gap_indicators = {
            'implement': [
                'library',
                'framework',
                'protocol',
                'standard',
                'websocket',
                'api',
                'auth',
            ],
            'integrate': [
                'api',
                'sdk',
                'webhook',
                'oauth',
                'jwt',
                'payment',
                'email',
                'chat',
            ],
            'deploy': [
                'docker',
                'kubernetes',
                'aws',
                'gcp',
                'azure',
                'ci/cd',
                'heroku',
                'vercel',
            ],
            'optimize': ['performance', 'cache', 'query', 'index', 'memory', 'speed'],
            'secure': [
                'authentication',
                'authorization',
                'encryption',
                'csr',
                'oauth',
                'jwt',
            ],
            'test': ['mock', 'fixture', 'coverage', 'integration', 'e2e', 'unit'],
            'debug': ['trace', 'profiler', 'memory', 'leak', 'error', 'crash'],
            'build': ['pipeline', 'workflow', 'automation', 'scraping', 'scrapling'],
            'connect': ['websocket', 'socket', 'realtime', 'real-time', 'streaming'],
        }

        # Error patterns that indicate knowledge gaps
        error_patterns = [
            r'ModuleNotFoundError',
            r'ImportError',
            r'AttributeError.*has no attribute',
            r'TypeError.*unexpected keyword argument',
            r'not implemented',
            r"doesn't support",
            r'unknown.*option',
            r'invalid.*configuration',
        ]

        # Check for error-based gaps
        if error_output:
            for pattern in error_patterns:
                if re.search(pattern, error_output, re.IGNORECASE):
                    # Extract module/feature name from error
                    module_match = re.search(
                        r"No module named ['\"](\w+)",
                        error_output,
                        re.IGNORECASE,
                    )
                    if module_match:
                        return KnowledgeGap(
                            topic=module_match.group(1),
                            description=f'Error indicates missing knowledge about {module_match.group(1)}',
                            severity=GapSeverity.HIGH,
                            context=context or task_description,
                            keywords=[module_match.group(1).lower()],
                            confidence=0.8,
                        )

        # Check for task-based gaps
        task_lower = task_description.lower()
        for action, topics in gap_indicators.items():
            if action in task_lower:
                for topic in topics:
                    if topic in task_lower:
                        # Check if we already have a skill for this
                        skill_name = topic.replace(' ', '-').replace('/', '-')
                        if skill_name not in self._existing_skills:
                            return KnowledgeGap(
                                topic=topic,
                                description=f'Task requires knowledge about {topic}',
                                severity=GapSeverity.MEDIUM,
                                context=task_description,
                                keywords=[topic, action],
                                confidence=0.6,
                            )

        return None

    def synthesize_skill(self, gap: KnowledgeGap) -> SynthesizedSkill:
        """Synthesize a skill file from a knowledge gap.

        Generates a structured skill document with rules, examples,
        and best practices for the identified topic.
        """
        # Determine complexity based on gap severity
        complexity_map = {
            GapSeverity.CRITICAL: SkillComplexity.COMPLEX,
            GapSeverity.HIGH: SkillComplexity.MODERATE,
            GapSeverity.MEDIUM: SkillComplexity.SIMPLE,
            GapSeverity.LOW: SkillComplexity.TRIVIAL,
        }
        complexity = complexity_map[gap.severity]

        # Generate skill content
        content = self._generate_content(gap, complexity)

        # Generate triggers from keywords
        triggers = self._generate_triggers(gap)

        # Generate skill name
        name = gap.topic.lower().replace(' ', '-').replace('/', '-')
        name = re.sub(r'[^a-z0-9-]', '', name)

        return SynthesizedSkill(
            name=name,
            description=f'Auto-generated skill for {gap.topic}',
            content=content,
            triggers=triggers,
            complexity=complexity,
            source_gap=gap,
        )

    def _generate_content(self, gap: KnowledgeGap, complexity: SkillComplexity) -> str:
        """Generate skill content based on the gap and complexity."""
        lines = [
            '---',
            f'name: {gap.topic.lower().replace(" ", "-")}',
            f'description: Auto-generated skill for {gap.topic}',
            'triggers:',
        ]
        for kw in gap.keywords:
            lines.append(f'  - {kw}')
        lines.extend(
            [
                '---',
                '',
                f'# {gap.topic.title()}',
                '',
                '## Overview',
                '',
                f'{gap.description}',
                '',
                '## Context',
                '',
                f'This skill was auto-generated because: {gap.context}',
                '',
                '## Key Rules',
                '',
            ]
        )

        # Add rules based on complexity
        if complexity in (
            SkillComplexity.TRIVIAL,
            SkillComplexity.SIMPLE,
        ):
            lines.extend(
                [
                    '1. Always validate input before processing',
                    '2. Handle errors gracefully with descriptive messages',
                    '3. Follow the principle of least privilege',
                    '4. Document edge cases and assumptions',
                    '5. Test with both valid and invalid inputs',
                ]
            )
        else:
            lines.extend(
                [
                    '1. Understand the problem completely before implementing',
                    '2. Check if existing solutions already address this',
                    '3. Use standard library when possible',
                    '4. Prefer platform-native features over third-party',
                    '5. Write minimal, necessary code',
                    '6. Always handle errors and edge cases',
                    '7. Validate at trust boundaries',
                    '8. Log meaningful information for debugging',
                    '9. Write tests for critical paths',
                    '10. Document decisions and trade-offs',
                ]
            )

        # Add best practices
        lines.extend(
            [
                '',
                '## Best Practices',
                '',
                '- Start with the simplest solution that works',
                '- Validate early, validate often',
                '- Handle errors at the appropriate layer',
                '- Use type hints for clarity',
                '- Keep functions small and focused',
                '',
                '## Common Pitfalls',
                '',
                '- Over-engineering simple problems',
                '- Ignoring error cases',
                '- Skipping input validation',
                '- Hardcoding configuration',
                '- Missing logging for debugging',
                '',
                '## References',
                '',
                f'- Official documentation for {gap.topic}',
                '- Stack Overflow common solutions',
                '- GitHub Issues for known problems',
            ]
        )

        return '\n'.join(lines)

    def _generate_triggers(self, gap: KnowledgeGap) -> list[str]:
        """Generate trigger keywords for the skill."""
        triggers = list(gap.keywords)

        # Add topic variations
        topic_words = gap.topic.split()
        if len(topic_words) > 1:
            triggers.append('-'.join(topic_words).lower())

        # Add related terms
        for related in gap.related_topics:
            triggers.append(related.lower())

        return list(set(triggers))

    def save_skill(self, skill: SynthesizedSkill) -> str:
        """Save a synthesized skill to disk.

        Returns:
            Path to the saved skill file.
        """
        filename = f'{skill.name}.md'
        filepath = self._skills_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(skill.content)

        skill.file_path = str(filepath)
        self._existing_skills.add(skill.name)

        return str(filepath)

    def get_skill_suggestions(
        self, recent_errors: list[str], recent_tasks: list[str]
    ) -> list[KnowledgeGap]:
        """Analyze recent errors and tasks to suggest skill creation.

        Args:
            recent_errors: List of recent error messages
            recent_tasks: List of recent task descriptions

        Returns:
            List of detected knowledge gaps
        """
        gaps = []

        # Analyze errors
        for error in recent_errors:
            gap = self.detect_gap(
                task_description='',
                error_output=error,
                context='Error analysis',
            )
            if gap:
                gaps.append(gap)

        # Analyze tasks
        for task in recent_tasks:
            gap = self.detect_gap(
                task_description=task,
                context='Task analysis',
            )
            if gap:
                gaps.append(gap)

        # Deduplicate by topic
        seen_topics = set()
        unique_gaps = []
        for gap in gaps:
            if gap.topic not in seen_topics:
                seen_topics.add(gap.topic)
                unique_gaps.append(gap)

        # Sort by severity
        severity_order = {
            GapSeverity.CRITICAL: 0,
            GapSeverity.HIGH: 1,
            GapSeverity.MEDIUM: 2,
            GapSeverity.LOW: 3,
        }
        unique_gaps.sort(key=lambda g: severity_order[g.severity])

        return unique_gaps

    def list_generated_skills(self) -> list[dict[str, str]]:
        """List all auto-generated skills."""
        skills = []
        if self._skills_dir.exists():
            for f in self._skills_dir.glob('*.md'):
                # Check if it's auto-generated by reading first few lines
                try:
                    with open(f, encoding='utf-8') as fh:
                        head = fh.read(200)
                        if 'Auto-generated' in head or 'auto-generated' in head:
                            skills.append(
                                {
                                    'name': f.stem,
                                    'path': str(f),
                                    'description': head.split('description:')[-1]
                                    .split('\n')[0]
                                    .strip()
                                    if 'description:' in head
                                    else '',
                                }
                            )
                except Exception:
                    pass
        return skills
