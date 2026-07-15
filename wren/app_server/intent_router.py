"""Intent Understanding API routes.

POST /api/v1/intent/analyze — Deep intent analysis of user prompt
POST /api/v1/intent/plan — Generate implementation plan from intent
POST /api/v1/intent/clarify — Generate clarification questions
POST /api/v1/intent/full — Full pipeline: analyze → clarify → plan
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from wren.intent.analyzer import IntentAnalyzer
from wren.intent.planner import PlanGenerator
from wren.intent.clarifier import ClarificationEngine

router = APIRouter(prefix='/api/v1/intent', tags=['intent'])

analyzer = IntentAnalyzer()
planner = PlanGenerator()
clarifier = ClarificationEngine()


# ── Request/Response Models ──────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    prompt: str = Field(description='User prompt to analyze')


class AnalyzeResponse(BaseModel):
    original_prompt: str
    cleaned_prompt: str
    primary_goal: str
    secondary_goals: list[str]
    features: list[str]
    domain: str
    project_type: str
    expertise_level: str
    urgency: str
    complexity: str
    confidence: str
    confidence_score: float
    insights: list[dict[str, Any]]
    ambiguous_parts: list[str]
    needs_clarification: bool
    recommended_stack: list[str]
    recommendedApproach: str


class PlanRequest(BaseModel):
    prompt: str = Field(description='User prompt to generate plan for')


class PlanResponse(BaseModel):
    project_name: str
    project_type: str
    one_line_summary: str
    architecture_decisions: list[dict[str, Any]]
    tech_stack: list[str]
    directory_structure: dict[str, str]
    features: list[dict[str, Any]]
    phases: dict[str, list[dict[str, Any]]]
    success_criteria: list[str]
    quality_gates: list[str]
    total_features: int
    total_steps: int
    estimated_total_hours: float
    risks: list[str]
    mitigations: list[str]


class ClarifyRequest(BaseModel):
    prompt: str = Field(description='User prompt to clarify')


class ClarifyResponse(BaseModel):
    questions: list[dict[str, Any]]
    total_questions: int
    estimated_time_seconds: int
    priority_breakdown: dict[str, int]
    category_breakdown: dict[str, int]


class FullPipelineRequest(BaseModel):
    prompt: str = Field(description='User prompt for full pipeline')
    answers: Optional[dict[str, str]] = Field(
        default=None, description='Optional answers to clarification questions'
    )


class FullPipelineResponse(BaseModel):
    intent: AnalyzeResponse
    clarification: Optional[ClarifyResponse] = None
    plan: Optional[PlanResponse] = None
    ready_to_build: bool
    next_step: str


# ── API Routes ───────────────────────────────────────────────────────────────


@router.post('/analyze', response_model=AnalyzeResponse)
async def analyze_intent(request: AnalyzeRequest) -> AnalyzeResponse:
    """Deep intent analysis of user prompt using psychology frameworks."""
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail='Prompt cannot be empty')

    intent = analyzer.analyze(request.prompt)

    return AnalyzeResponse(
        original_prompt=intent.original_prompt,
        cleaned_prompt=intent.cleaned_prompt,
        primary_goal=intent.primary_goal,
        secondary_goals=intent.secondary_goals,
        features=intent.features,
        domain=intent.context.domain,
        project_type=intent.context.project_type.value,
        expertise_level=intent.context.expertise.value,
        urgency=intent.context.urgency.value,
        complexity=intent.context.complexity.value,
        confidence=intent.confidence.value,
        confidence_score=intent.confidence_score,
        insights=[
            {
                'framework': i.framework,
                'insight': i.insight,
                'confidence': i.confidence,
                'action': i.action,
            }
            for i in intent.insights
        ],
        ambiguous_parts=intent.ambiguous_parts,
        needs_clarification=intent.needs_clarification,
        recommended_stack=intent.recommended_stack,
        recommendedApproach=intent.recommendedApproach,
    )


@router.post('/plan', response_model=PlanResponse)
async def generate_plan(request: PlanRequest) -> PlanResponse:
    """Generate a detailed implementation plan from user prompt."""
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail='Prompt cannot be empty')

    intent = analyzer.analyze(request.prompt)
    plan = planner.generate(intent)

    return PlanResponse(
        project_name=plan.project_name,
        project_type=plan.project_type,
        one_line_summary=plan.one_line_summary,
        architecture_decisions=[
            {
                'decision': d.decision,
                'rationale': d.rationale,
                'alternatives': d.alternatives,
                'tradeoffs': d.tradeoffs,
                'confidence': d.confidence,
            }
            for d in plan.architecture_decisions
        ],
        tech_stack=plan.tech_stack,
        directory_structure=plan.directory_structure,
        features=[
            {
                'name': f.name,
                'description': f.description,
                'priority': f.priority,
                'complexity': f.complexity,
                'estimated_hours': f.estimated_hours,
                'dependencies': f.dependencies,
                'acceptance_criteria': f.acceptance_criteria,
            }
            for f in plan.features
        ],
        phases={
            phase.value: [
                {
                    'step_number': s.step_number,
                    'title': s.title,
                    'description': s.description,
                    'files_to_create': s.files_to_create,
                    'commands': s.commands,
                    'estimated_minutes': s.estimated_minutes,
                    'verification': s.verification,
                }
                for s in steps
            ]
            for phase, steps in plan.phases.items()
        },
        success_criteria=plan.success_criteria,
        quality_gates=plan.quality_gates,
        total_features=plan.total_features,
        total_steps=plan.total_steps,
        estimated_total_hours=plan.estimated_total_hours,
        risks=plan.risks,
        mitigations=plan.mitigations,
    )


@router.post('/clarify', response_model=ClarifyResponse)
async def generate_clarification(request: ClarifyRequest) -> ClarifyResponse:
    """Generate clarification questions for ambiguous prompts."""
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail='Prompt cannot be empty')

    intent = analyzer.analyze(request.prompt)
    session = clarifier.generate_session(intent)

    return ClarifyResponse(
        questions=[
            {
                'question': q.question,
                'priority': q.priority.value,
                'category': q.category.value,
                'options': q.options,
                'follow_up': q.follow_up,
                'rationale': q.rationale,
                'required': q.required,
            }
            for q in session.questions
        ],
        total_questions=session.total_questions,
        estimated_time_seconds=session.estimated_time_seconds,
        priority_breakdown=session.priority_breakdown,
        category_breakdown=session.category_breakdown,
    )


@router.post('/full', response_model=FullPipelineResponse)
async def full_pipeline(request: FullPipelineRequest) -> FullPipelineResponse:
    """Full pipeline: analyze → clarify → plan.

    If answers are provided, skips clarification and generates plan directly.
    """
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail='Prompt cannot be empty')

    # Step 1: Analyze intent
    intent = analyzer.analyze(request.prompt)

    # Step 2: Generate clarification if needed
    clarification = None
    if intent.needs_clarification and not request.answers:
        session = clarifier.generate_session(intent)
        clarification = ClarifyResponse(
            questions=[
                {
                    'question': q.question,
                    'priority': q.priority.value,
                    'category': q.category.value,
                    'options': q.options,
                    'follow_up': q.follow_up,
                    'rationale': q.rationale,
                    'required': q.required,
                }
                for q in session.questions
            ],
            total_questions=session.total_questions,
            estimated_time_seconds=session.estimated_time_seconds,
            priority_breakdown=session.priority_breakdown,
            category_breakdown=session.category_breakdown,
        )

    # Step 3: Generate plan if ready
    plan = None
    ready_to_build = False
    next_step = ''

    if not intent.needs_clarification or request.answers:
        plan_obj = planner.generate(intent)
        plan = PlanResponse(
            project_name=plan_obj.project_name,
            project_type=plan_obj.project_type,
            one_line_summary=plan_obj.one_line_summary,
            architecture_decisions=[
                {
                    'decision': d.decision,
                    'rationale': d.rationale,
                    'alternatives': d.alternatives,
                    'tradeoffs': d.tradeoffs,
                    'confidence': d.confidence,
                }
                for d in plan_obj.architecture_decisions
            ],
            tech_stack=plan_obj.tech_stack,
            directory_structure=plan_obj.directory_structure,
            features=[
                {
                    'name': f.name,
                    'description': f.description,
                    'priority': f.priority,
                    'complexity': f.complexity,
                    'estimated_hours': f.estimated_hours,
                    'dependencies': f.dependencies,
                    'acceptance_criteria': f.acceptance_criteria,
                }
                for f in plan_obj.features
            ],
            phases={
                phase.value: [
                    {
                        'step_number': s.step_number,
                        'title': s.title,
                        'description': s.description,
                        'files_to_create': s.files_to_create,
                        'commands': s.commands,
                        'estimated_minutes': s.estimated_minutes,
                        'verification': s.verification,
                    }
                    for s in steps
                ]
                for phase, steps in plan_obj.phases.items()
            },
            success_criteria=plan_obj.success_criteria,
            quality_gates=plan_obj.quality_gates,
            total_features=plan_obj.total_features,
            total_steps=plan_obj.total_steps,
            estimated_total_hours=plan_obj.estimated_total_hours,
            risks=plan_obj.risks,
            mitigations=plan_obj.mitigations,
        )
        ready_to_build = True
        next_step = 'Ready to build! Approve the plan to start implementation.'
    else:
        next_step = (
            'Please answer the clarification questions above '
            'so I can generate an accurate plan.'
        )

    # Build intent response
    intent_response = AnalyzeResponse(
        original_prompt=intent.original_prompt,
        cleaned_prompt=intent.cleaned_prompt,
        primary_goal=intent.primary_goal,
        secondary_goals=intent.secondary_goals,
        features=intent.features,
        domain=intent.context.domain,
        project_type=intent.context.project_type.value,
        expertise_level=intent.context.expertise.value,
        urgency=intent.context.urgency.value,
        complexity=intent.context.complexity.value,
        confidence=intent.confidence.value,
        confidence_score=intent.confidence_score,
        insights=[
            {
                'framework': i.framework,
                'insight': i.insight,
                'confidence': i.confidence,
                'action': i.action,
            }
            for i in intent.insights
        ],
        ambiguous_parts=intent.ambiguous_parts,
        needs_clarification=intent.needs_clarification,
        recommended_stack=intent.recommended_stack,
        recommendedApproach=intent.recommendedApproach,
    )

    return FullPipelineResponse(
        intent=intent_response,
        clarification=clarification,
        plan=plan,
        ready_to_build=ready_to_build,
        next_step=next_step,
    )
