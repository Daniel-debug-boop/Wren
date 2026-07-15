"""Skill Synthesis API Routes.

Provides endpoints for detecting knowledge gaps and generating skills.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from wren.intent.skill_synthesizer import (
    GapSeverity,
    KnowledgeGap,
    SkillComplexity,
    SkillSynthesizer,
    SynthesizedSkill,
)

router = APIRouter(prefix='/api/v1/skills', tags=['skills'])

# Global synthesizer instance
_synthesizer: SkillSynthesizer | None = None


def get_synthesizer() -> SkillSynthesizer:
    """Get or create the global synthesizer."""
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = SkillSynthesizer()
    return _synthesizer


# ── Request/Response Models ──────────────────────────────────────────────


class DetectGapRequest(BaseModel):
    """Request to detect a knowledge gap."""

    task_description: str = Field(
        ..., description='Description of the task being attempted'
    )
    error_output: str | None = Field(
        None, description='Error output if the task failed'
    )
    context: str | None = Field(None, description='Additional context about the gap')


class GapResponse(BaseModel):
    """Response containing detected gap information."""

    topic: str
    description: str
    severity: str
    context: str
    keywords: list[str]
    confidence: float


class SynthesizeRequest(BaseModel):
    """Request to synthesize a skill from a gap."""

    topic: str = Field(..., description='Topic to create skill for')
    description: str = Field(..., description='Description of the knowledge gap')
    severity: str = Field(
        'medium', description='Gap severity: critical, high, medium, low'
    )
    context: str = Field('', description='Context that triggered the gap')
    keywords: list[str] = Field(default_factory=list, description='Related keywords')


class SynthesizeResponse(BaseModel):
    """Response containing synthesized skill."""

    name: str
    description: str
    triggers: list[str]
    complexity: str
    file_path: str | None
    content_preview: str


class SaveSkillRequest(BaseModel):
    """Request to save a synthesized skill."""

    name: str = Field(..., description='Skill name (kebab-case)')
    description: str = Field(..., description='Skill description')
    content: str = Field(..., description='Full skill content in markdown')
    triggers: list[str] = Field(default_factory=list, description='Trigger keywords')


class SuggestionsRequest(BaseModel):
    """Request for skill suggestions based on recent activity."""

    recent_errors: list[str] = Field(
        default_factory=list, description='Recent error messages'
    )
    recent_tasks: list[str] = Field(
        default_factory=list, description='Recent task descriptions'
    )


class SuggestionResponse(BaseModel):
    """A skill creation suggestion."""

    topic: str
    description: str
    severity: str
    confidence: float
    suggested_name: str


# ── Endpoints ────────────────────────────────────────────────────────────


@router.post('/detect-gap', response_model=GapResponse)
async def detect_gap(request: DetectGapRequest) -> GapResponse:
    """Detect if a knowledge gap exists for the given task/error.

    Analyzes the task description and error output to determine
    if the agent lacks knowledge in a specific area.
    """
    synthesizer = get_synthesizer()
    gap = synthesizer.detect_gap(
        task_description=request.task_description,
        error_output=request.error_output,
        context=request.context,
    )

    if gap is None:
        raise HTTPException(
            status_code=200,
            detail={'message': 'No knowledge gap detected', 'gap': None},
        )

    return GapResponse(
        topic=gap.topic,
        description=gap.description,
        severity=gap.severity.value,
        context=gap.context,
        keywords=gap.keywords,
        confidence=gap.confidence,
    )


@router.post('/synthesize', response_model=SynthesizeResponse)
async def synthesize_skill(request: SynthesizeRequest) -> SynthesizeResponse:
    """Synthesize a skill file from a knowledge gap.

    Generates a structured skill document with rules, examples,
    and best practices for the identified topic.
    """
    synthesizer = get_synthesizer()

    # Create gap object
    gap = KnowledgeGap(
        topic=request.topic,
        description=request.description,
        severity=GapSeverity(request.severity),
        context=request.context,
        keywords=request.keywords,
    )

    # Synthesize skill
    skill = synthesizer.synthesize_skill(gap)

    return SynthesizeResponse(
        name=skill.name,
        description=skill.description,
        triggers=skill.triggers,
        complexity=skill.complexity.value,
        file_path=skill.file_path,
        content_preview=skill.content[:500] + '...'
        if len(skill.content) > 500
        else skill.content,
    )


@router.post('/save', response_model=dict[str, str])
async def save_skill(request: SaveSkillRequest) -> dict[str, str]:
    """Save a synthesized skill to disk.

    Writes the skill file to the skills directory and registers
    it for future use.
    """
    synthesizer = get_synthesizer()

    # Create a minimal gap for the skill
    gap = KnowledgeGap(
        topic=request.name,
        description=request.description,
        severity=GapSeverity.MEDIUM,
        context='Manual save',
        keywords=request.keywords,
    )

    # Create skill object
    skill = SynthesizedSkill(
        name=request.name,
        description=request.description,
        content=request.content,
        triggers=request.triggers,
        complexity=SkillComplexity.SIMPLE,
        source_gap=gap,
    )

    # Save
    filepath = synthesizer.save_skill(skill)

    return {'path': filepath, 'name': request.name}


@router.post('/suggest', response_model=list[SuggestionResponse])
async def suggest_skills(request: SuggestionsRequest) -> list[SuggestionResponse]:
    """Get skill creation suggestions based on recent activity.

    Analyzes recent errors and tasks to recommend skills that
    would improve the agent's capabilities.
    """
    synthesizer = get_synthesizer()
    gaps = synthesizer.get_skill_suggestions(
        recent_errors=request.recent_errors,
        recent_tasks=request.recent_tasks,
    )

    return [
        SuggestionResponse(
            topic=gap.topic,
            description=gap.description,
            severity=gap.severity.value,
            confidence=gap.confidence,
            suggested_name=gap.topic.lower().replace(' ', '-').replace('/', '-'),
        )
        for gap in gaps
    ]


@router.get('/generated', response_model=list[dict[str, str]])
async def list_generated_skills() -> list[dict[str, str]]:
    """List all auto-generated skills.

    Returns a list of skills that were created by the synthesis
    system, not manually written.
    """
    synthesizer = get_synthesizer()
    return synthesizer.list_generated_skills()
