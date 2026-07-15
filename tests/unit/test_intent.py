"""Tests for the Intent Understanding system."""

from __future__ import annotations

import pytest

from wren.intent.psychology import (
    PsychologyFramework,
    UserContext,
    ExpertiseLevel,
    ProjectType,
    UrgencyLevel,
    ComplexityPreference,
)
from wren.intent.analyzer import IntentAnalyzer, ExtractedIntent, IntentConfidence
from wren.intent.planner import PlanGenerator, ImplementationPlan, PlanPhase
from wren.intent.clarifier import (
    ClarificationEngine,
    ClarificationSession,
    QuestionPriority,
)


# ── Psychology Framework Tests ────────────────────────────────────────────────


class TestPsychologyFramework:
    @pytest.fixture
    def framework(self):
        return PsychologyFramework()

    def test_detect_fintech_domain(self, framework):
        context = framework.analyze('make me a payment processing app with stripe')
        assert context.domain == 'fintech'

    def test_detect_healthcare_domain(self, framework):
        context = framework.analyze('build a patient portal for our clinic')
        assert context.domain == 'healthcare'

    def test_detect_ecommerce_domain(self, framework):
        context = framework.analyze('create an online store with cart and checkout')
        assert context.domain == 'ecommerce'

    def test_detect_portfolio_domain(self, framework):
        context = framework.analyze('build a portfolio website to showcase my work')
        assert context.domain == 'portfolio'

    def test_detect_beginner_expertise(self, framework):
        context = framework.analyze('help me learn how to make a simple website')
        assert context.expertise == ExpertiseLevel.BEGINNER

    def test_detect_advanced_expertise(self, framework):
        context = framework.analyze(
            'build a scalable microservice architecture with kubernetes'
        )
        assert context.expertise == ExpertiseLevel.ADVANCED

    def test_detect_prototype_type(self, framework):
        context = framework.analyze('quick prototype to validate my idea')
        assert context.project_type == ProjectType.PROTOTYPE

    def test_detect_production_type(self, framework):
        context = framework.analyze('production ready app for real users')
        assert context.project_type == ProjectType.PRODUCTION

    def test_detect_urgent_urgency(self, framework):
        context = framework.analyze('need this asap, very urgent')
        assert context.urgency == UrgencyLevel.IMMEDIATE

    def test_detect_simple_complexity(self, framework):
        context = framework.analyze('just a simple minimal website')
        assert context.complexity == ComplexityPreference.SIMPLE

    def test_detect_enterprise_complexity(self, framework):
        context = framework.analyze('enterprise grade scalable system')
        assert context.complexity == ComplexityPreference.ENTERPRISE

    def test_extract_features(self, framework):
        context = framework.analyze(
            'app with login, dashboard, payments, and real-time chat'
        )
        assert 'authentication' in context.features
        assert 'dashboard' in context.features
        assert 'payments' in context.features
        assert 'real-time' in context.features

    def test_infer_implicit_needs_production(self, framework):
        context = framework.analyze('production ready ecommerce store')
        assert 'error_handling' in context.implicit_needs
        assert 'security' in context.implicit_needs

    def test_infer_implicit_needs_fintech(self, framework):
        context = framework.analyze('fintech payment app')
        assert 'audit_logging' in context.implicit_needs
        assert 'data_encryption' in context.implicit_needs

    def test_get_insights(self, framework):
        context = framework.analyze('make me a professional saas dashboard')
        insights = framework.get_insights(context)
        assert len(insights) == 4
        frameworks = [i.framework for i in insights]
        assert 'maslow' in frameworks
        assert 'jtbd' in frameworks
        assert 'cognitive_load' in frameworks
        assert 'expertise_alignment' in frameworks


# ── Intent Analyzer Tests ─────────────────────────────────────────────────────


class TestIntentAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return IntentAnalyzer()

    def test_analyze_vague_prompt(self, analyzer):
        intent = analyzer.analyze('make me a website')
        assert intent.primary_goal
        assert intent.confidence in [
            IntentConfidence.LOW,
            IntentConfidence.MEDIUM,
        ]
        assert intent.needs_clarification is True

    def test_analyze_detailed_prompt(self, analyzer):
        intent = analyzer.analyze(
            'build a react + fastapi saas dashboard with authentication, '
            'payments via stripe, and real-time analytics for enterprise users'
        )
        assert intent.confidence in [
            IntentConfidence.HIGH,
            IntentConfidence.VERY_HIGH,
        ]
        assert 'authentication' in intent.features
        assert 'payments' in intent.features
        assert 'dashboard' in intent.features
        assert 'react' in intent.context.tech_preferences

    def test_clean_prompt(self, analyzer):
        intent = analyzer.analyze('please help me make a simple website')
        assert 'please' not in intent.cleaned_prompt
        assert 'help' not in intent.cleaned_prompt
        assert 'website' in intent.cleaned_prompt

    def test_extract_primary_goal(self, analyzer):
        intent = analyzer.analyze('create a portfolio website for designers')
        assert 'portfolio' in intent.primary_goal.lower()

    def test_extract_features(self, analyzer):
        intent = analyzer.analyze(
            'app with auth, search, file upload, and email notifications'
        )
        assert 'authentication' in intent.features
        assert 'search' in intent.features
        assert 'file-upload' in intent.features
        assert 'email' in intent.features

    def test_recommended_stack(self, analyzer):
        intent = analyzer.analyze('build a react app with postgres')
        assert 'React' in intent.recommended_stack
        assert 'PostgreSQL' in intent.recommended_stack

    def test_recommended_approach_prototype(self, analyzer):
        intent = analyzer.analyze('quick prototype to test an idea')
        assert 'prototyp' in intent.recommendedApproach.lower()

    def test_recommended_approach_production(self, analyzer):
        intent = analyzer.analyze('production ready app with tests')
        assert 'production' in intent.recommendedApproach.lower()

    def test_psychological_insights_present(self, analyzer):
        intent = analyzer.analyze('make me a professional dashboard')
        assert len(intent.insights) > 0
        assert all(hasattr(i, 'framework') for i in intent.insights)

    def test_ambiguity_detection(self, analyzer):
        intent = analyzer.analyze('make me a website etc')
        assert len(intent.ambiguous_parts) > 0

    def test_clarification_needed_for_vague(self, analyzer):
        intent = analyzer.analyze('make something cool')
        assert intent.needs_clarification is True

    def test_clarification_not_needed_for_detailed(self, analyzer):
        intent = analyzer.analyze(
            'build a react + fastapi saas with auth, payments, dashboard '
            'for enterprise users, production ready with tests'
        )
        assert intent.needs_clarification is False


# ── Plan Generator Tests ──────────────────────────────────────────────────────


class TestPlanGenerator:
    @pytest.fixture
    def generator(self):
        return PlanGenerator()

    @pytest.fixture
    def analyzer(self):
        return IntentAnalyzer()

    def test_generate_plan(self, generator, analyzer):
        intent = analyzer.analyze('build a saas dashboard with auth and payments')
        plan = generator.generate(intent)
        assert plan.project_name
        assert plan.tech_stack
        assert len(plan.features) > 0
        assert len(plan.architecture_decisions) > 0

    def test_plan_has_phases(self, generator, analyzer):
        intent = analyzer.analyze('production ready app')
        plan = generator.generate(intent)
        assert PlanPhase.FOUNDATION in plan.phases
        assert PlanPhase.CORE_FEATURES in plan.phases
        assert PlanPhase.TESTING in plan.phases
        assert PlanPhase.DEPLOYMENT in plan.phases

    def test_plan_has_success_criteria(self, generator, analyzer):
        intent = analyzer.analyze('build an app')
        plan = generator.generate(intent)
        assert len(plan.success_criteria) > 0
        assert len(plan.quality_gates) > 0

    def test_plan_has_estimates(self, generator, analyzer):
        intent = analyzer.analyze('app with auth and dashboard')
        plan = generator.generate(intent)
        assert plan.estimated_total_hours > 0
        assert plan.total_features > 0
        assert plan.total_steps > 0

    def test_plan_has_directory_structure(self, generator, analyzer):
        intent = analyzer.analyze('build a web app')
        plan = generator.generate(intent)
        assert 'frontend/' in plan.directory_structure
        assert 'backend/' in plan.directory_structure

    def test_plan_enterprise_has_more_gates(self, generator, analyzer):
        intent = analyzer.analyze('enterprise grade system with tests')
        plan = generator.generate(intent)
        assert len(plan.quality_gates) >= 5

    def test_plan_has_risks(self, generator, analyzer):
        intent = analyzer.analyze('app with payments and real-time')
        plan = generator.generate(intent)
        assert len(plan.risks) > 0
        assert len(plan.mitigations) > 0


# ── Clarification Engine Tests ────────────────────────────────────────────────


class TestClarificationEngine:
    @pytest.fixture
    def engine(self):
        return ClarificationEngine()

    @pytest.fixture
    def analyzer(self):
        return IntentAnalyzer()

    def test_generate_session(self, engine, analyzer):
        intent = analyzer.analyze('make me a website')
        session = engine.generate_session(intent)
        assert session.total_questions > 0
        assert len(session.questions) > 0

    def test_session_has_priority_breakdown(self, engine, analyzer):
        intent = analyzer.analyze('make something')
        session = engine.generate_session(intent)
        assert len(session.priority_breakdown) > 0

    def test_session_has_category_breakdown(self, engine, analyzer):
        intent = analyzer.analyze('make something')
        session = engine.generate_session(intent)
        assert len(session.category_breakdown) > 0

    def test_questions_sorted_by_priority(self, engine, analyzer):
        intent = analyzer.analyze('make something')
        session = engine.generate_session(intent)
        priorities = [q.priority for q in session.questions]
        # Should be sorted: CRITICAL first, then HIGH, MEDIUM, LOW
        for i in range(len(priorities) - 1):
            assert priorities[i].value <= priorities[i + 1].value

    def test_limit_questions_for_prototype(self, engine, analyzer):
        intent = analyzer.analyze('quick prototype')
        session = engine.generate_session(intent)
        assert session.total_questions <= 3

    def test_more_questions_for_enterprise(self, engine, analyzer):
        intent = analyzer.analyze('enterprise grade system')
        session = engine.generate_session(intent)
        assert session.total_questions <= 7

    def test_process_answer(self, engine):
        from wren.intent.clarifier import ClarificationQuestion, QuestionCategory

        question = ClarificationQuestion(
            question='What is the purpose?',
            priority=QuestionPriority.HIGH,
            category=QuestionCategory.PURPOSE,
            follow_up='Great, building a {purpose} app.',
        )
        follow_up = engine.process_answer(question, 'SaaS')
        assert follow_up == 'Great, building a SaaS app.'

    def test_quick_summary(self, engine, analyzer):
        from wren.intent.clarifier import ClarificationAnswer, QuestionCategory

        intent = analyzer.analyze('make something')
        answers = [
            ClarificationAnswer(
                question='Purpose?',
                answer='SaaS',
                category=QuestionCategory.PURPOSE,
            ),
            ClarificationAnswer(
                question='Features?',
                answer='auth, dashboard',
                category=QuestionCategory.FEATURES,
            ),
        ]
        summary = engine.generate_quick_summary(intent, answers)
        assert 'SaaS' in summary
        assert 'auth' in summary


# ── Integration Tests ─────────────────────────────────────────────────────────


class TestIntentIntegration:
    """End-to-end tests for the full intent pipeline."""

    def test_full_pipeline_vague(self):
        analyzer = IntentAnalyzer()
        planner = PlanGenerator()
        clarifier = ClarificationEngine()

        intent = analyzer.analyze('make me a website')
        assert intent.needs_clarification is True

        session = clarifier.generate_session(intent)
        assert session.total_questions > 0

    def test_full_pipeline_detailed(self):
        analyzer = IntentAnalyzer()
        planner = PlanGenerator()

        intent = analyzer.analyze(
            'build a react + fastapi saas dashboard with authentication, '
            'stripe payments, real-time analytics, for enterprise users, '
            'production ready with tests and deployment'
        )
        assert intent.needs_clarification is False

        plan = planner.generate(intent)
        assert plan.total_features > 0
        assert plan.estimated_total_hours > 0

    def test_vague_to_plan_flow(self):
        """Test that vague prompts get clarification before planning."""
        analyzer = IntentAnalyzer()
        planner = PlanGenerator()
        clarifier = ClarificationEngine()

        # Step 1: Analyze
        intent = analyzer.analyze('make something cool')

        # Step 2: Clarify
        session = clarifier.generate_session(intent)
        assert session.total_questions > 0

        # Step 3: Simulate answers
        intent.context.domain = 'saas'
        intent.features = ['authentication', 'dashboard']
        intent.context.project_type = ProjectType.PRODUCTION

        # Step 4: Generate plan
        plan = planner.generate(intent)
        assert plan.total_features > 0

    def test_psychology_insights_drive_plan(self):
        """Test that psychology insights affect the plan."""
        analyzer = IntentAnalyzer()
        planner = PlanGenerator()

        # Beginner user
        intent = analyzer.analyze('help me make a simple portfolio website')
        plan = planner.generate(intent)

        # Should have simpler plan
        assert plan.estimated_total_hours < 20

        # Expert user
        intent = analyzer.analyze(
            'build a scalable microservice with kubernetes and grpc'
        )
        plan = planner.generate(intent)

        # Should have more complex plan
        assert plan.total_features > 0
