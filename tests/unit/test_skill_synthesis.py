"""Tests for Skill Synthesis System.

Tests the self-teaching capability that auto-generates skills
from knowledge gaps detected during task execution.
"""

import tempfile
from pathlib import Path

import pytest

from wren.intent.skill_synthesizer import (
    GapSeverity,
    KnowledgeGap,
    SkillComplexity,
    SkillSynthesizer,
    SynthesizedSkill,
)


class TestKnowledgeGap:
    """Tests for KnowledgeGap data class."""

    def test_create_gap(self) -> None:
        """Test creating a knowledge gap."""
        gap = KnowledgeGap(
            topic='websocket',
            description='Need to implement WebSocket reconnection',
            severity=GapSeverity.HIGH,
            context='Building real-time chat feature',
            keywords=['websocket', 'reconnect'],
        )
        assert gap.topic == 'websocket'
        assert gap.severity == GapSeverity.HIGH
        assert gap.keywords == ['websocket', 'reconnect']

    def test_gap_severity_levels(self) -> None:
        """Test all severity levels."""
        for severity in GapSeverity:
            gap = KnowledgeGap(
                topic='test',
                description='test',
                severity=severity,
                context='test',
            )
            assert gap.severity == severity


class TestSkillSynthesizer:
    """Tests for SkillSynthesizer."""

    @pytest.fixture
    def synthesizer(self, tmp_path: Path) -> SkillSynthesizer:
        """Create a synthesizer with temp skills directory."""
        return SkillSynthesizer(skills_dir=str(tmp_path))

    def test_init(self, synthesizer: SkillSynthesizer) -> None:
        """Test synthesizer initialization."""
        assert synthesizer._skills_dir.exists()

    def test_detect_gap_from_error(self, synthesizer: SkillSynthesizer) -> None:
        """Test detecting gap from error output."""
        gap = synthesizer.detect_gap(
            task_description='',
            error_output="ModuleNotFoundError: No module named 'websocket'",
        )
        assert gap is not None
        assert gap.topic == 'websocket'
        assert gap.severity == GapSeverity.HIGH

    def test_detect_gap_from_task(self, synthesizer: SkillSynthesizer) -> None:
        """Test detecting gap from task description."""
        gap = synthesizer.detect_gap(
            task_description='I need to implement WebSocket reconnection',
        )
        assert gap is not None
        assert 'websocket' in gap.keywords

    def test_detect_gap_no_match(self, synthesizer: SkillSynthesizer) -> None:
        """Test when no gap is detected."""
        gap = synthesizer.detect_gap(
            task_description='Write a simple function',
        )
        assert gap is None

    def test_synthesize_skill(self, synthesizer: SkillSynthesizer) -> None:
        """Test synthesizing a skill from a gap."""
        gap = KnowledgeGap(
            topic='docker',
            description='Need Docker deployment knowledge',
            severity=GapSeverity.HIGH,
            context='Deploying to production',
            keywords=['docker', 'deploy'],
        )
        skill = synthesizer.synthesize_skill(gap)
        assert skill.name == 'docker'
        assert skill.complexity == SkillComplexity.MODERATE
        assert 'docker' in skill.triggers
        assert '# Docker' in skill.content

    def test_save_skill(self, synthesizer: SkillSynthesizer) -> None:
        """Test saving a skill to disk."""
        gap = KnowledgeGap(
            topic='test-skill',
            description='Test skill',
            severity=GapSeverity.LOW,
            context='test',
        )
        skill = synthesizer.synthesize_skill(gap)
        filepath = synthesizer.save_skill(skill)
        assert Path(filepath).exists()
        assert 'test-skill' in synthesizer._existing_skills

    def test_no_duplicate_skills(self, synthesizer: SkillSynthesizer) -> None:
        """Test that existing skills are not recreated."""
        # Create a skill first
        gap = KnowledgeGap(
            topic='existing',
            description='Already exists',
            severity=GapSeverity.LOW,
            context='test',
        )
        skill = synthesizer.synthesize_skill(gap)
        synthesizer.save_skill(skill)

        # Try to detect the same gap
        result = synthesizer.detect_gap(
            task_description='I need to implement existing feature',
        )
        # Should not detect a gap for existing skill
        assert result is None

    def test_get_skill_suggestions(self, synthesizer: SkillSynthesizer) -> None:
        """Test getting skill suggestions from errors/tasks."""
        gaps = synthesizer.get_skill_suggestions(
            recent_errors=[
                "ModuleNotFoundError: No module named 'redis'",
                'ConnectionRefusedError: Redis connection failed',
            ],
            recent_tasks=['Implement caching with Redis'],
        )
        # Should suggest Redis-related skills
        assert len(gaps) > 0
        topics = [g.topic for g in gaps]
        assert any('redis' in t.lower() for t in topics)

    def test_list_generated_skills(self, synthesizer: SkillSynthesizer) -> None:
        """Test listing auto-generated skills."""
        # Create a skill
        gap = KnowledgeGap(
            topic='generated',
            description='Auto-generated',
            severity=GapSeverity.LOW,
            context='test',
        )
        skill = synthesizer.synthesize_skill(gap)
        synthesizer.save_skill(skill)

        # List should include it
        skills = synthesizer.list_generated_skills()
        assert any(s['name'] == 'generated' for s in skills)

    def test_skill_content_trivial(self, synthesizer: SkillSynthesizer) -> None:
        """Test trivial complexity skill content."""
        gap = KnowledgeGap(
            topic='trivial',
            description='Trivial topic',
            severity=GapSeverity.LOW,
            context='test',
        )
        skill = synthesizer.synthesize_skill(gap)
        assert skill.complexity == SkillComplexity.TRIVIAL
        assert '5 rules' in skill.content or 'Always validate' in skill.content

    def test_skill_content_complex(self, synthesizer: SkillSynthesizer) -> None:
        """Test complex complexity skill content."""
        gap = KnowledgeGap(
            topic='complex',
            description='Complex topic',
            severity=GapSeverity.CRITICAL,
            context='test',
        )
        skill = synthesizer.synthesize_skill(gap)
        assert skill.complexity == SkillComplexity.COMPLEX
        assert '10 rules' in skill.content or 'Understand the problem' in skill.content

    def test_generate_triggers(self, synthesizer: SkillSynthesizer) -> None:
        """Test trigger generation from gap keywords."""
        gap = KnowledgeGap(
            topic='my-feature',
            description='Feature',
            severity=GapSeverity.MEDIUM,
            context='test',
            keywords=['feature', 'my-feature', 'special'],
        )
        skill = synthesizer.synthesize_skill(gap)
        assert 'feature' in skill.triggers
        assert 'my-feature' in skill.triggers
        assert 'special' in skill.triggers
