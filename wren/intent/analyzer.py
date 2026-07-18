"""Intent Analyzer — Deep Understanding of User Prompts.

Extracts intent, context, and implicit requirements from user prompts
using psychology frameworks and modern analysis techniques.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from wren.intent.psychology import (
    PsychologyFramework,
    UserContext,
    PsychologicalInsight,
    ProjectType,
)


class IntentConfidence(Enum):
    """How confident we are in the extracted intent."""

    LOW = 'low'  # Need clarification
    MEDIUM = 'medium'  # Reasonable guess
    HIGH = 'high'  # Clear intent
    VERY_HIGH = 'very_high'  # Explicitly stated


@dataclass
class ExtractedIntent:
    """Fully extracted intent from user prompt."""

    # Core intent
    original_prompt: str
    cleaned_prompt: str  # Prompt with noise removed

    # What they want
    primary_goal: str  # Main thing they want to build
    secondary_goals: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)

    # Context
    context: UserContext = field(default_factory=UserContext)

    # Confidence
    confidence: IntentConfidence = IntentConfidence.MEDIUM
    confidence_score: float = 0.5  # 0-1

    # Psychological insights
    insights: list[PsychologicalInsight] = field(default_factory=list)

    # What's missing
    ambiguous_parts: list[str] = field(default_factory=list)
    needs_clarification: bool = False
    clarification_questions: list[str] = field(default_factory=list)

    # Recommendations
    recommended_stack: list[str] = field(default_factory=list)
    recommendedApproach: str = ''


class IntentAnalyzer:
    """Deep intent extraction from user prompts."""

    def __init__(self) -> None:
        self.psychology = PsychologyFramework()

        # Noise words to remove
        self._noise_words = {
            'please',
            'kindly',
            'just',
            'really',
            'very',
            'basically',
            'actually',
            'simply',
            'make',
            'create',
            'build',
            'do',
            'i want',
            'i need',
            'can you',
            'could you',
            'would you',
            'help me',
            'write',
            'code',
            'help',
        }

        # Strength indicators
        self._strength_words = {
            'must': 0.9,
            'need': 0.8,
            'require': 0.8,
            'should': 0.7,
            'want': 0.6,
            'like': 0.5,
            'maybe': 0.3,
            'consider': 0.3,
            'possibly': 0.2,
        }

    def analyze(self, prompt: str) -> ExtractedIntent:
        """Deep analysis of user prompt."""
        # Clean prompt
        cleaned = self._clean_prompt(prompt)

        # Extract core goal
        primary_goal = self._extract_primary_goal(cleaned, prompt)
        secondary_goals = self._extract_secondary_goals(cleaned)

        # Get psychology context
        context = self.psychology.analyze(prompt)
        insights = self.psychology.get_insights(context)

        # Extract features
        features = self._extract_features(cleaned)

        # Calculate confidence
        confidence, score = self._calculate_confidence(prompt, context)

        # Detect ambiguity
        ambiguous = self._detect_ambiguity(prompt, context)

        # Generate clarification questions if needed
        needs_clarification = score < 0.6 or len(ambiguous) > 2
        clarification_questions = self._generate_clarification_questions(
            context, ambiguous, needs_clarification
        )

        # Recommend stack
        recommended_stack = self._recommend_stack(context)

        # Generate approach recommendation
        recommended_approach = self._recommend_approach(context)

        return ExtractedIntent(
            original_prompt=prompt,
            cleaned_prompt=cleaned,
            primary_goal=primary_goal,
            secondary_goals=secondary_goals,
            features=features,
            context=context,
            confidence=confidence,
            confidence_score=score,
            insights=insights,
            ambiguous_parts=ambiguous,
            needs_clarification=needs_clarification,
            clarification_questions=clarification_questions,
            recommended_stack=recommended_stack,
            recommendedApproach=recommended_approach,
        )

    def _clean_prompt(self, prompt: str) -> str:
        """Remove noise words, keep substantive content."""
        words = prompt.lower().split()
        cleaned_words = [w for w in words if w not in self._noise_words]
        return ' '.join(cleaned_words)

    def _extract_primary_goal(self, cleaned: str, original: str) -> str:
        """Extract the main thing they want to build."""
        # Look for explicit mentions
        goal_patterns = [
            (
                r'(?:make|create|build|write)\s+(?:a|an|the)\s+(.+?)(?:\s+that|\s+which|\s+with|\s+for|$)',
                1,
            ),
            (
                r'(?:i want|i need)\s+(?:a|an|the)\s+(.+?)(?:\s+that|\s+which|\s+with|\s+for|$)',
                1,
            ),
            (
                r'(?:website|app|application|platform|tool|service)\s+(?:for|that|which)\s+(.+?)(?:\.|$)',
                1,
            ),
        ]

        import re

        for pattern, group in goal_patterns:
            match = re.search(pattern, original.lower())
            if match:
                return match.group(group).strip()

        # Fallback: use cleaned prompt as goal
        return cleaned[:100] if len(cleaned) > 100 else cleaned

    def _extract_secondary_goals(self, cleaned: str) -> list[str]:
        """Extract additional goals beyond the primary."""
        secondary = []

        secondary_patterns = [
            'also',
            'additionally',
            'plus',
            'and also',
            'as well as',
            'with',
            'including',
            'featuring',
        ]

        for pattern in secondary_patterns:
            if pattern in cleaned:
                idx = cleaned.index(pattern)
                after = cleaned[idx + len(pattern) :].strip()
                if after:
                    secondary.append(after[:80])

        return secondary

    def _extract_features(self, cleaned: str) -> list[str]:
        """Extract features from the cleaned prompt."""
        features = []

        feature_keywords = {
            'authentication': [
                'auth',
                'login',
                'signup',
                'register',
                'account',
                'password',
            ],
            'dashboard': ['dashboard', 'analytics', 'overview', 'stats', 'metrics'],
            'payments': [
                'payment',
                'stripe',
                'checkout',
                'billing',
                'subscribe',
                'pricing',
            ],
            'real-time': [
                'real-time',
                'realtime',
                'websocket',
                'live',
                'chat',
                'instant',
            ],
            'admin': ['admin', 'admin panel', 'management', 'cms', 'backoffice'],
            'api': ['api', 'rest', 'graphql', 'endpoint', 'webhook'],
            'database': ['database', 'db', 'postgres', 'mysql', 'mongo', 'storage'],
            'search': ['search', 'filter', 'query', 'find', 'lookup'],
            'file-upload': ['upload', 'file', 'image', 'document', 'media'],
            'email': ['email', 'notification', 'newsletter', 'smtp'],
            'responsive': ['responsive', 'mobile', 'tablet', 'adaptive'],
            'i18n': [
                'i18n',
                'internationalization',
                'localization',
                'multi-language',
                'translate',
            ],
            'testing': ['test', 'testing', 'unit test', 'integration test'],
            'deployment': ['deploy', 'deployment', 'docker', 'kubernetes', 'ci/cd'],
        }

        for feature, keywords in feature_keywords.items():
            if any(kw in cleaned for kw in keywords):
                features.append(feature)

        return features

    def _calculate_confidence(
        self, prompt: str, context: UserContext
    ) -> tuple[IntentConfidence, float]:
        """Calculate how confident we are in the extracted intent."""
        score = 0.5  # Base score

        # Length indicates clarity
        if len(prompt) > 100:
            score += 0.1  # Detailed prompt
        if len(prompt) > 200:
            score += 0.1  # Very detailed

        # Explicit features boost confidence
        if context.features:
            score += min(0.2, len(context.features) * 0.05)

        # Tech preferences boost confidence
        if context.tech_preferences:
            score += 0.1

        # Domain detection boosts confidence
        if context.domain != 'general':
            score += 0.1

        # Strength words
        for word, strength in self._strength_words.items():
            if word in prompt.lower():
                score += strength * 0.05

        # Cap at 1.0
        score = min(1.0, score)

        # Map to confidence level
        if score >= 0.85:
            confidence = IntentConfidence.VERY_HIGH
        elif score >= 0.7:
            confidence = IntentConfidence.HIGH
        elif score >= 0.5:
            confidence = IntentConfidence.MEDIUM
        else:
            confidence = IntentConfidence.LOW

        return confidence, score

    def _detect_ambiguity(self, prompt: str, context: UserContext) -> list[str]:
        """Detect ambiguous parts that need clarification."""
        ambiguous = []

        # Vague feature requests
        vague_words = ['etc', 'and so on', 'things like', 'stuff', 'whatever']
        for word in vague_words:
            if word in prompt.lower():
                ambiguous.append(f'Vague reference: "{word}"')

        # Missing critical info
        if not context.tech_preferences:
            ambiguous.append('No tech stack specified')

        if context.domain == 'general' and not context.features:
            ambiguous.append('Domain and features unclear')

        # Too many features for prototype
        if context.project_type == ProjectType.PROTOTYPE and len(context.features) > 5:
            ambiguous.append('Too many features for a prototype')

        return ambiguous

    def _generate_clarification_questions(
        self,
        context: UserContext,
        ambiguous: list[str],
        needed: bool,
    ) -> list[str]:
        """Generate smart clarification questions."""
        if not needed:
            return []

        questions = []

        # Always ask about purpose if unclear
        if context.domain == 'general':
            questions.append(
                'What is the primary purpose of this project? '
                '(e.g., portfolio, SaaS, e-commerce, internal tool)'
            )

        # Ask about features if unclear
        if not context.features:
            questions.append(
                'What are the key features you need? '
                '(e.g., authentication, dashboard, payments, real-time)'
            )

        # Ask about tech if unclear
        if not context.tech_preferences:
            questions.append(
                'Do you have a preferred tech stack? '
                '(e.g., React, Vue, Python, Node.js)'
            )

        # Ask about audience
        questions.append(
            'Who is the target audience? '
            '(e.g., developers, consumers, enterprise users)'
            if context.domain != 'portfolio'
            else ''
        )

        # Ask about quality bar
        if context.project_type == ProjectType.PROTOTYPE:
            questions.append(
                'Is this a quick prototype or production-ready? '
                'This affects code quality and feature scope.'
            )

        return [q for q in questions if q]

    def _recommend_stack(self, context: UserContext) -> list[str]:
        """Recommend tech stack based on context."""
        stack = []

        # Frontend
        if 'react' in context.tech_preferences:
            stack.append('React')
        elif 'vue' in context.tech_preferences:
            stack.append('Vue')
        elif context.project_type in [ProjectType.PRODUCTION, ProjectType.ENTERPRISE]:
            stack.append('React')  # Default for production
        else:
            stack.append('React')  # Safe default

        # Backend
        if (
            'python' in context.tech_preferences
            or 'fastapi' in context.tech_preferences
        ):
            stack.append('FastAPI')
        elif 'node' in context.tech_preferences:
            stack.append('Node.js')
        elif context.domain in ['fintech', 'healthcare']:
            stack.append('FastAPI')  # Python for compliance domains
        else:
            stack.append('FastAPI')  # Safe default

        # Database
        if 'postgresql' in context.tech_preferences or context.domain in [
            'fintech',
            'saas',
        ]:
            stack.append('PostgreSQL')
        elif 'mongodb' in context.tech_preferences:
            stack.append('MongoDB')
        else:
            stack.append('PostgreSQL')  # Safe default

        # Styling
        if 'tailwind' in context.tech_preferences:
            stack.append('Tailwind CSS')
        else:
            stack.append('Tailwind CSS')  # Safe default

        return stack

    def _recommend_approach(self, context: UserContext) -> str:
        """Recommend development approach."""
        if context.project_type == ProjectType.PROTOTYPE:
            return (
                'Rapid prototyping: Build core features first, '
                'skip tests and deployment initially. '
                'Focus on validating the idea.'
            )
        if context.project_type == ProjectType.MVP:
            return (
                'MVP approach: Build essential features with '
                'basic tests and deployment. '
                'Launch fast, iterate based on feedback.'
            )
        if context.project_type == ProjectType.PRODUCTION:
            return (
                'Production approach: Full TDD, error handling, '
                'logging, security, and deployment pipeline. '
                'Build for reliability and scale.'
            )
        if context.project_type == ProjectType.ENTERPRISE:
            return (
                'Enterprise approach: Comprehensive testing, '
                'security audit, compliance, monitoring, '
                'and documentation. Build for maintainability.'
            )
        return 'Balanced approach: Clean code with moderate testing and documentation.'
