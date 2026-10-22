"""Clarification Engine — Asks Smart Questions When Intent is Unclear.

Uses progressive disclosure and psychology to ask the right questions
in the right order, minimizing user friction while maximizing understanding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import, from wren.intent.analyzer import ExtractedIntent, IntentConfidence
from wren.intent.psychology import (
    ProjectType,
)


class QuestionPriority(Enum):
    """Priority of clarification questions."""

    CRITICAL = 'critical'  # Must answer to proceed
    HIGH = 'high'  # Should answer for good results
    MEDIUM = 'medium'  # Nice to have
    LOW = 'low'  #, class QuestionCategory(Enum):
    """Category of clarification question."""

    PURPOSE = 'purpose'
    FEATURES = 'features'
    TECH = 'tech'
    DESIGN = 'design'
    AUDIENCE = 'audience'
    CONSTRAINTS = 'constraints'


@dataclass
class ClarificationQuestion:
    """A single clarification question."""

    question: str
    priority: QuestionPriority
    category: QuestionCategory
    options: list[str] = field(default_factory=list)  # Multiple choice options
    follow_up: str = ''  # What to ask based on answer
    rationale: str = ''  # Why we're asking
    required: bool = True


@dataclass
class ClarificationSession:
    """A complete clarification session."""

    questions: list[ClarificationQuestion]
    total_questions: int
    estimated_time_seconds: int
    priority_breakdown: dict[str, int]  # priority -> count
    category_breakdown: dict[str, int]  # category -> count


@dataclass
class ClarificationAnswer:
    """User's answer to a clarification question."""

    question: str
    answer: str
    category: QuestionCategory
    timestamp: float = 0.0


class ClarificationEngine:
    """Generates and manages clarification questions."""

    def __init__(self) -> None:
        self._question_templates: dict[
            QuestionCategory, list[ClarificationQuestion]
        ] = {
            QuestionCategory.PURPOSE: [
                ClarificationQuestion(
                    question='What is the primary purpose of this project?',
                    priority=QuestionPriority.CRITICAL,
                    category=QuestionCategory.PURPOSE,
                    options=[
                        'Portfolio/Personal website',
                        'SaaS product',
                        'E-commerce store',
                        'Internal tool/Dashboard',
                        'Blog/CMS',
                        'Social platform',
                        'Other',
                    ],
                    follow_up='Tell me more about what makes this {purpose} unique.',
                    rationale='Understanding the purpose helps me choose the right architecture and features.',
                ),
                ClarificationQuestion(
                    question='Who is the target audience?',
                    priority=QuestionPriority.HIGH,
                    category=QuestionCategory.AUDIENCE,
                    options=[
                        'Developers',
                        'Business users',
                        'Consumers/General public',
                        'Enterprise clients',
                        'Internal team',
                    ],
                    follow_up='What do these {audience} value most?',
                    rationale='Different audiences have different expectations for design and functionality.',
                ),
            ],
            QuestionCategory.FEATURES: [
                ClarificationQuestion(
                    question='What are the core features you need?',
                    priority=QuestionPriority.CRITICAL,
                    category=QuestionCategory.FEATURES,
                    options=[
                        'Authentication (login/signup)',
                        'Dashboard/Analytics',
                        'Payment processing',
                        'Real-time updates',
                        'Admin panel',
                        'Search/Filtering',
                        'File uploads',
                        'Email notifications',
                    ],
                    follow_up='Tell me more about the {feature} requirements.',
                    rationale='Core features determine the architecture and implementation order.',
                ),
                ClarificationQuestion(
                    question='What features can wait for v2?',
                    priority=QuestionPriority.MEDIUM,
                    category=QuestionCategory.FEATURES,
                    options=['None, I need everything', 'Let me specify'],
                    follow_up="Great, we'll focus on the essentials first.",
                    rationale='Scope management prevents feature creep and ensures timely delivery.',
                ),
            ],
            QuestionCategory.TECH: [
                ClarificationQuestion(
                    question='Do you have a preferred tech stack?',
                    priority=QuestionPriority.HIGH,
                    category=QuestionCategory.TECH,
                    options=[
                        'React + Python (FastAPI)',
                        'React + Node.js (Express)',
                        'Vue + Python (FastAPI)',
                        'Vue + Node.js (Express)',
                        'No preference, recommend one',
                    ],
                    follow_up="I'll use {tech_stack} for this project.",
                    rationale='Tech preferences affect the entire implementation approach.',
                ),
                ClarificationQuestion(
                    question='What database do you prefer?',
                    priority=QuestionPriority.MEDIUM,
                    category=QuestionCategory.TECH,
                    options=[
                        'PostgreSQL (recommended)',
                        'MySQL',
                        'MongoDB',
                        'SQLite (for prototyping)',
                        'No preference',
                    ],
                    follow_up='{database} it is.',
                    rationale='Database choice affects data modeling and queries.',
                ),
            ],
            QuestionCategory.DESIGN: [
                ClarificationQuestion(
                    question='What design style do you prefer?',
                    priority=QuestionPriority.MEDIUM,
                    category=QuestionCategory.DESIGN,
                    options=[
                        'Clean and minimal',
                        'Bold and modern',
                        'Professional/Corporate',
                        'Playful/Creative',
                        'No preference, use best practices',
                    ],
                    follow_up="I'll aim for a {style} design.",
                    rationale='Design style affects the visual direction and component choices.',
                ),
                ClarificationQuestion(
                    question='Do you have any design references?',
                    priority=QuestionPriority.LOW,
                    category=QuestionCategory.DESIGN,
                    options=["Yes, I'll share links", 'No, use your judgment'],
                    follow_up="I'll use those as inspiration.",
                    rationale='Design references help me understand your visual expectations.',
                ),
            ],
            QuestionCategory.CONSTRAINTS: [
                ClarificationQuestion(
                    question='What is your timeline?',
                    priority=QuestionPriority.HIGH,
                    category=QuestionCategory.CONSTRAINTS,
                    options=[
                        'ASAP (prototype)',
                        'This week (MVP)',
                        'This month (production)',
                        'No rush (enterprise)',
                    ],
                    follow_up="I'll optimize for {timeline} delivery.",
                    rationale='Timeline affects the scope and quality tradeoffs.',
                ),
                ClarificationQuestion(
                    question='Any constraints I should know about?',
                    priority=QuestionPriority.MEDIUM,
                    category=QuestionCategory.CONSTRAINTS,
                    options=[
                        'Budget limitations',
                        'Must use specific services',
                        'Compliance requirements',
                        'Performance requirements',
                        'None',
                    ],
                    follow_up="I'll keep {constraint} in mind.",
                    rationale='Constraints affect architecture and technology choices.',
                ),
            ],
        }

    def generate_session(self, intent: ExtractedIntent) -> ClarificationSession:
        """Generate a clarification session based on extracted intent."""
        questions = []

        # Determine which categories need clarification
        categories_needed = self._determine_categories(intent)

        # Generate questions for each category
        for category in categories_needed:
            category_questions = self._question_templates.get(category, [])

            # Filter and prioritize based on intent
            for question in category_questions:
                if self._should_ask(question, intent):
                    questions.append(question)

        # Sort by priority
        priority_order = {
            QuestionPriority.CRITICAL: 0,
            QuestionPriority.HIGH: 1,
            QuestionPriority.MEDIUM: 2,
            QuestionPriority.LOW: 3,
        }
        questions.sort(key=lambda q: priority_order[q.priority])

        # Limit to reasonable number
        max_questions = self._get_max_questions(intent)
        questions = questions[:max_questions]

        # Calculate breakdowns
        priority_breakdown = {}
        category_breakdown = {}
        for q in questions:
            priority_breakdown[q.priority.value] = (
                priority_breakdown.get(q.priority.value, 0) + 1
            )
            category_breakdown[q.category.value] = (
                category_breakdown.get(q.category.value, 0) + 1
            )

        return ClarificationSession(
            questions=questions,
            total_questions=len(questions),
            estimated_time_seconds=len(questions) * 15,  # ~15 seconds per question
            priority_breakdown=priority_breakdown,
            category_breakdown=category_breakdown,
        )

    def _determine_categories(self, intent: ExtractedIntent) -> list[QuestionCategory]:
        """Determine which categories need clarification."""
        categories = []

        # Always check purpose if unclear
        if intent.context.domain == 'general':
            categories.append(QuestionCategory.PURPOSE)

        # Check features if none detected
        if not intent.features:
            categories.append(QuestionCategory.FEATURES)

        # Check tech if no preferences
        if not intent.context.tech_preferences:
            categories.append(QuestionCategory.TECH)

        # Check design for production/enterprise
        if intent.context.project_type in [
            ProjectType.PRODUCTION,
            ProjectType.ENTERPRISE,
        ]:
            categories.append(QuestionCategory.DESIGN)

        # Check constraints if missing
        categories.append(QuestionCategory.CONSTRAINTS)

        return categories

    def _should_ask(
        self, question: ClarificationQuestion, intent: ExtractedIntent
    ) -> bool:
        """Determine if a specific question should be asked."""
        # Skip if confidence is very high
        if intent.confidence == IntentConfidence.VERY_HIGH:
            return question.priority in [
                QuestionPriority.CRITICAL,
                QuestionPriority.HIGH,
            ]

        # Skip if we already have the info
        if question.category == QuestionCategory.TECH:
            if intent.context.tech_preferences:
                return False

        if question.category == QuestionCategory.FEATURES:
            if intent.features:
                return False

        if question.category == QuestionCategory.PURPOSE:
            if intent.context.domain != 'general':
                return False

        return True

    def _get_max_questions(self, intent: ExtractedIntent) -> int:
        """Get maximum number of questions based on context."""
        # Quick prototype: fewer questions
        if intent.context.project_type == ProjectType.PROTOTYPE:
            return 3

        # MVP: moderate questions
        if intent.context.project_type == ProjectType.MVP:
            return 5

        # Production/Enterprise: more questions
        if intent.context.project_type in [
            ProjectType.PRODUCTION,
            ProjectType.ENTERPRISE,
        ]:
            return 7

        return 5

    def process_answer(
        self, question: ClarificationQuestion, answer: str
    ) -> str | None:
        """Process an answer and return follow-up if needed."""
        if question.follow_up:
            return question.follow_up.replace(
                '{' + question.category.value + '}', answer
            )
        return None

    def generate_quick_summary(
        self, intent: ExtractedIntent, answers: list[ClarificationAnswer]
    ) -> str:
        """Generate a quick summary from answers."""
        summary_parts = []

        for answer in answers:
            if answer.category == QuestionCategory.PURPOSE:
                summary_parts.append(f'Purpose: {answer.answer}')
            elif answer.category == QuestionCategory.FEATURES:
                summary_parts.append(f'Features: {answer.answer}')
            elif answer.category == QuestionCategory.TECH:
                summary_parts.append(f'Tech: {answer.answer}')
            elif answer.category == QuestionCategory.DESIGN:
                summary_parts.append(f'Design: {answer.answer}')
            elif answer.category == QuestionCategory.CONSTRAINTS:
                summary_parts.append(f'Constraints: {answer.answer}')

        return ' | '.join(summary_parts) if summary_parts else 'No additional info'
