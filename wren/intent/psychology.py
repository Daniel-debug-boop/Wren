"""Psychology Framework for Intent Understanding.

Uses established psychology principles to understand what users actually want:
- Maslow's Hierarchy (functional → aesthetic → self-actualization)
- Jobs-to-be-Done (what job is the user hiring this for?)
- Cognitive Load Theory (how complex should the output be?)
- Expertise Detection (beginner vs expert user)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ExpertiseLevel(Enum):
    """User expertise level affects output complexity."""

    BEGINNER = 'beginner'  # Needs explanations, simple code
    INTERMEDIATE = 'intermediate'  # Moderate complexity
    ADVANCED = 'advanced'  # Full complexity
    EXPERT = 'expert'  # Minimal hand-holding


class ProjectType(Enum):
    """What the user is building."""

    PROTOTYPE = 'prototype'  # Quick proof of concept
    MVP = 'mvp'  # Minimum viable product
    PRODUCTION = 'production'  # Full production app
    ENTERPRISE = 'enterprise'  # Enterprise-grade system
    PERSONAL = 'personal'  # Personal project/hobby
    PORTFOLIO = 'portfolio'  # Showcasing skills


class UrgencyLevel(Enum):
    """How fast the user needs it."""

    IMMEDIATE = 'immediate'  # Need it now
    SOON = 'soon'  # Within days
    FLEXIBLE = 'flexible'  # No rush
    EXPLORATORY = 'exploratory'  # Just exploring


class ComplexityPreference(Enum):
    """How complex the user wants the solution."""

    SIMPLE = 'simple'  # Minimal, clean
    MODERATE = 'moderate'  # Balanced
    COMPREHENSIVE = 'comprehensive'  # Full-featured
    ENTERPRISE = 'enterprise'  # Maximum features


@dataclass
class UserContext:
    """Extracted context about the user and their needs."""

    # What they're building
    project_type: ProjectType = ProjectType.PROTOTYPE
    domain: str = ''  # e.g., 'fintech', 'healthcare', 'ecommerce'
    purpose: str = ''  # e.g., 'portfolio', 'SaaS', 'internal tool'

    # Who they are
    expertise: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE
    role: str = ''  # e.g., 'developer', 'designer', 'founder'
    team_size: int = 1  # Solo vs team

    # What they need
    features: list[str] = field(default_factory=list)
    tech_preferences: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    # How they want it
    urgency: UrgencyLevel = UrgencyLevel.FLEXIBLE
    complexity: ComplexityPreference = ComplexityPreference.MODERATE
    quality_bar: str = 'production'  # prototype, production, enterprise

    # Implicit needs (inferred)
    implicit_needs: list[str] = field(default_factory=list)
    missing_requirements: list[str] = field(default_factory=list)


@dataclass
class PsychologicalInsight:
    """Insight derived from psychology frameworks."""

    framework: str  # Which framework this comes from
    insight: str  # What we learned
    confidence: float  # 0-1 how confident we are
    action: str  # What we should do about it


class PsychologyFramework:
    """Understands user intent through psychology principles."""

    def __init__(self) -> None:
        self._domain_keywords: dict[str, list[str]] = {
            'fintech': ['payment', 'bank', 'finance', 'money', 'trading', 'stripe'],
            'healthcare': ['patient', 'medical', 'health', 'clinic', 'hospital'],
            'ecommerce': ['shop', 'store', 'product', 'cart', 'checkout', 'sell'],
            'social': ['chat', 'feed', 'post', 'comment', 'follow', 'social'],
            'education': ['course', 'learn', 'teach', 'student', 'quiz'],
            'enterprise': ['crm', 'erp', 'dashboard', 'analytics', 'admin'],
            'portfolio': ['portfolio', 'showcase', 'resume', 'cv', 'personal'],
            'blog': ['blog', 'article', 'post', 'content', 'cms'],
            'saas': ['saas', 'subscription', 'plan', 'pricing', 'tenant'],
        }

        self._expertise_signals: dict[str, list[str]] = {
            'beginner': ['help', 'how', 'start', 'learn', 'simple', 'easy', 'basic'],
            'intermediate': ['build', 'create', 'make', 'app', 'website', 'feature'],
            'advanced': ['api', 'microservice', 'scalable', 'architecture', 'pattern'],
            'expert': [
                'optimize',
                'performance',
                'concurrent',
                'distributed',
                'kernel',
            ],
        }

        self._urgency_signals: dict[str, list[str]] = {
            'immediate': ['asap', 'urgent', 'now', 'quickly', 'fast', 'rush'],
            'soon': ['soon', 'this week', 'deadline', 'sprint'],
            'flexible': ['whenever', 'no rush', 'eventually', 'someday'],
            'exploratory': ['explore', 'experiment', 'try', 'test', 'learn'],
        }

    def analyze(self, prompt: str) -> UserContext:
        """Deep analysis of user prompt using psychology frameworks."""
        context = UserContext()
        prompt_lower = prompt.lower()

        # Detect domain
        context.domain = self._detect_domain(prompt_lower)

        # Detect expertise level
        context.expertise = self._detect_expertise(prompt_lower)

        # Detect project type
        context.project_type = self._detect_project_type(prompt_lower)

        # Detect urgency
        context.urgency = self._detect_urgency(prompt_lower)

        # Detect complexity preference
        context.complexity = self._detect_complexity(prompt_lower)

        # Extract features
        context.features = self._extract_features(prompt_lower)

        # Extract tech preferences
        context.tech_preferences = self._extract_tech(prompt_lower)

        # Infer implicit needs (Jobs-to-be-Done)
        context.implicit_needs = self._infer_implicit_needs(context)

        # Detect missing requirements
        context.missing_requirements = self._detect_missing_requirements(context)

        return context

    def get_insights(self, context: UserContext) -> list[PsychologicalInsight]:
        """Generate psychological insights from context."""
        insights = []

        # Maslow's Hierarchy insight
        insights.append(self._maslow_insight(context))

        # Jobs-to-be-Done insight
        insights.append(self._jtbd_insight(context))

        # Cognitive Load insight
        insights.append(self._cognitive_load_insight(context))

        # Expertise-Complexity alignment
        insights.append(self._expertise_alignment_insight(context))

        return insights

    def _detect_domain(self, prompt: str) -> str:
        """Detect the domain from keywords."""
        scores: dict[str, int] = {}
        for domain, keywords in self._domain_keywords.items():
            score = sum(1 for kw in keywords if kw in prompt)
            if score > 0:
                scores[domain] = score

        if scores:
            return max(scores, key=scores.get)
        return 'general'

    def _detect_expertise(self, prompt: str) -> ExpertiseLevel:
        """Detect user expertise from language patterns."""
        scores: dict[str, int] = {}
        for level, signals in self._expertise_signals.items():
            score = sum(1 for s in signals if s in prompt)
            if score > 0:
                scores[level] = score

        if scores:
            best = max(scores, key=scores.get)
            return ExpertiseLevel(best)
        return ExpertiseLevel.INTERMEDIATE

    def _detect_project_type(self, prompt: str) -> ProjectType:
        """Detect what type of project this is."""
        type_signals = {
            ProjectType.PROTOTYPE: [
                'prototype',
                'poc',
                'proof of concept',
                'demo',
                'quick',
            ],
            ProjectType.MVP: ['mvp', 'minimum viable', 'first version', 'launch'],
            ProjectType.PRODUCTION: ['production', 'deploy', 'live', 'real users'],
            ProjectType.ENTERPRISE: ['enterprise', 'company', 'team', 'organization'],
            ProjectType.PERSONAL: ['personal', 'hobby', 'fun', 'learn', 'practice'],
            ProjectType.PORTFOLIO: ['portfolio', 'showcase', 'resume', 'job'],
        }

        for ptype, signals in type_signals.items():
            if any(s in prompt for s in signals):
                return ptype

        # Default based on complexity signals
        if any(w in prompt for w in ['simple', 'easy', 'quick']):
            return ProjectType.PROTOTYPE
        if any(w in prompt for w in ['professional', 'production', 'enterprise']):
            return ProjectType.PRODUCTION

        return ProjectType.PROTOTYPE

    def _detect_urgency(self, prompt: str) -> UrgencyLevel:
        """Detect how fast they need it."""
        for level, signals in self._urgency_signals.items():
            if any(s in prompt for s in signals):
                return UrgencyLevel(level)
        return UrgencyLevel.FLEXIBLE

    def _detect_complexity(self, prompt: str) -> ComplexityPreference:
        """Detect desired complexity level."""
        if any(w in prompt for w in ['simple', 'minimal', 'clean', 'basic']):
            return ComplexityPreference.SIMPLE
        if any(w in prompt for w in ['full', 'comprehensive', 'complete', 'all']):
            return ComplexityPreference.COMPREHENSIVE
        if any(w in prompt for w in ['enterprise', 'scalable', 'production']):
            return ComplexityPreference.ENTERPRISE
        return ComplexityPreference.MODERATE

    def _extract_features(self, prompt: str) -> list[str]:
        """Extract mentioned features."""
        feature_keywords = {
            'authentication': ['auth', 'login', 'signup', 'register', 'account'],
            'dashboard': ['dashboard', 'analytics', 'overview', 'stats'],
            'payments': ['payment', 'stripe', 'checkout', 'billing', 'subscribe'],
            'real-time': ['real-time', 'websocket', 'live', 'chat', 'notification'],
            'admin': ['admin', 'admin panel', 'management', 'cms'],
            'api': ['api', 'rest', 'graphql', 'endpoint'],
            'database': ['database', 'db', 'postgres', 'mysql', 'mongo'],
            'search': ['search', 'filter', 'query'],
            'file-upload': ['upload', 'file', 'image', 'document'],
            'email': ['email', 'notification', 'newsletter'],
            'responsive': ['responsive', 'mobile', 'tablet'],
            'i18n': ['i18n', 'internationalization', 'localization', 'multi-language'],
        }

        features = []
        for feature, keywords in feature_keywords.items():
            if any(kw in prompt for kw in keywords):
                features.append(feature)

        return features

    def _extract_tech(self, prompt: str) -> list[str]:
        """Extract technology preferences."""
        tech_keywords = {
            'react': ['react', 'reactjs', 'react.js'],
            'vue': ['vue', 'vuejs', 'vue.js'],
            'angular': ['angular'],
            'svelte': ['svelte'],
            'nextjs': ['next', 'nextjs', 'next.js'],
            'fastapi': ['fastapi', 'fast api'],
            'flask': ['flask'],
            'django': ['django'],
            'node': ['node', 'nodejs', 'node.js', 'express'],
            'python': ['python', 'py'],
            'typescript': ['typescript', 'ts'],
            'tailwind': ['tailwind', 'tailwindcss'],
            'postgresql': ['postgres', 'postgresql'],
            'mongodb': ['mongo', 'mongodb'],
            'redis': ['redis'],
            'docker': ['docker', 'container'],
        }

        tech = []
        for t, keywords in tech_keywords.items():
            if any(kw in prompt for kw in keywords):
                tech.append(t)

        return tech

    def _infer_implicit_needs(self, context: UserContext) -> list[str]:
        """Infer needs the user didn't explicitly mention (Jobs-to-be-Done)."""
        needs = []

        # Every web app needs these
        if context.project_type in [ProjectType.PRODUCTION, ProjectType.ENTERPRISE]:
            needs.extend(
                [
                    'error_handling',
                    'logging',
                    'testing',
                    'security',
                    'performance_optimization',
                ]
            )

        # Domain-specific implicit needs
        if context.domain == 'fintech':
            needs.extend(['audit_logging', 'data_encryption', 'compliance'])
        elif context.domain == 'healthcare':
            needs.extend(['hipaa_compliance', 'data_encryption', 'audit_trail'])
        elif context.domain == 'ecommerce':
            needs.extend(
                ['inventory_management', 'order_tracking', 'email_notifications']
            )
        elif context.domain == 'saas':
            needs.extend(['multi_tenancy', 'subscription_billing', 'usage_tracking'])

        # Feature-specific implicit needs
        if 'authentication' in context.features:
            needs.extend(['password_reset', 'session_management', 'rbac'])
        if 'payments' in context.features:
            needs.extend(['webhook_handling', 'invoice_generation', 'refund_flow'])
        if 'real-time' in context.features:
            needs.extend(['reconnection_logic', 'message_queuing', 'presence'])

        return list(set(needs))

    def _detect_missing_requirements(self, context: UserContext) -> list[str]:
        """Detect requirements that are likely missing from the prompt."""
        missing = []

        # Always missing unless mentioned
        if 'testing' not in context.features:
            missing.append('testing_strategy')
        if 'deployment' not in str(context.constraints):
            missing.append('deployment_plan')
        if not context.tech_preferences:
            missing.append('tech_stack_decision')

        # Domain-specific missing
        if context.domain == 'fintech' and 'security' not in context.features:
            missing.append('security_audit')
        if context.domain == 'healthcare' and 'compliance' not in context.features:
            missing.append('compliance_requirements')

        return missing

    def _maslow_insight(self, context: UserContext) -> PsychologicalInsight:
        """Maslow's Hierarchy: functional → aesthetic → self-actualization."""
        if context.complexity == ComplexityPreference.SIMPLE:
            return PsychologicalInsight(
                framework='maslow',
                insight='User wants functional base (prototype level)',
                confidence=0.8,
                action='Focus on core functionality, minimal design',
            )
        if context.complexity == ComplexityPreference.ENTERPRISE:
            return PsychologicalInsight(
                framework='maslow',
                insight='User wants self-actualization (enterprise grade)',
                confidence=0.9,
                action='Full feature set, premium design, scalability',
            )
        return PsychologicalInsight(
            framework='maslow',
            insight='User wants balanced functionality + aesthetics',
            confidence=0.7,
            action='Good design with solid functionality',
        )

    def _jtbd_insight(self, context: UserContext) -> PsychologicalInsight:
        """Jobs-to-be-Done: what job is the user hiring this for?"""
        job_map = {
            ProjectType.PROTOTYPE: 'validate an idea quickly',
            ProjectType.MVP: 'launch and get first users',
            ProjectType.PRODUCTION: 'serve real users at scale',
            ProjectType.ENTERPRISE: 'run business operations',
            ProjectType.PERSONAL: 'learn and have fun',
            ProjectType.PORTFOLIO: 'impress potential employers',
        }

        job = job_map.get(context.project_type, 'build something')

        return PsychologicalInsight(
            framework='jtbd',
            insight=f'User is hiring this to: {job}',
            confidence=0.85,
            action=f'Optimize for {job} as primary success metric',
        )

    def _cognitive_load_insight(self, context: UserContext) -> PsychologicalInsight:
        """Cognitive Load Theory: match complexity to user capacity."""
        if context.expertise == ExpertiseLevel.BEGINNER:
            return PsychologicalInsight(
                framework='cognitive_load',
                insight='Beginner user: reduce cognitive load',
                confidence=0.9,
                action='Simple code, clear comments, step-by-step explanations',
            )
        if context.expertise == ExpertiseLevel.EXPERT:
            return PsychologicalInsight(
                framework='cognitive_load',
                insight='Expert user: maximize information density',
                confidence=0.9,
                action='Concise code, advanced patterns, minimal explanation',
            )
        return PsychologicalInsight(
            framework='cognitive_load',
            insight='Intermediate user: balanced complexity',
            confidence=0.7,
            action='Moderate comments, clean architecture',
        )

    def _expertise_alignment_insight(
        self, context: UserContext
    ) -> PsychologicalInsight:
        """Ensure expertise level matches output complexity."""
        if (
            context.expertise == ExpertiseLevel.BEGINNER
            and context.complexity == ComplexityPreference.ENTERPRISE
        ):
            return PsychologicalInsight(
                framework='expertise_alignment',
                insight='Mismatch: beginner wants enterprise complexity',
                confidence=0.85,
                action='Simplify enterprise features, add explanations',
            )
        if (
            context.expertise == ExpertiseLevel.EXPERT
            and context.complexity == ComplexityPreference.SIMPLE
        ):
            return PsychologicalInsight(
                framework='expertise_alignment',
                insight='Mismatch: expert wants simple output',
                confidence=0.85,
                action='Keep it simple but well-architected',
            )
        return PsychologicalInsight(
            framework='expertise_alignment',
            insight='Expertise and complexity are aligned',
            confidence=0.7,
            action='Proceed as planned',
        )
