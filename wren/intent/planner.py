"""Plan Generator — Creates Detailed Specifications Before Code.

Takes extracted intent and generates a comprehensive plan that includes:
- Architecture decisions
- Feature breakdown
- Tech stack justification
- Implementation order
- Success criteria
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from wren.intent.analyzer import ExtractedIntent
from wren.intent.psychology import (
    UserContext,
    ProjectType,
    ExpertiseLevel,
)


class PlanPhase(Enum):
    """Phases of implementation."""

    FOUNDATION = 'foundation'  # Project setup, core architecture
    CORE_FEATURES = 'core_features'  # Main functionality
    SECONDARY_FEATURES = 'secondary_features'  # Nice-to-haves
    POLISH = 'polish'  # Design, animations, UX
    TESTING = 'testing'  # Tests, validation
    DEPLOYMENT = 'deployment'  # Docker, CI/CD, launch


@dataclass
class Feature:
    """A single feature in the plan."""

    name: str
    description: str
    priority: str  # critical, high, medium, low
    complexity: str  # simple, moderate, complex
    estimated_hours: float
    dependencies: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)


@dataclass
class ArchitectureDecision:
    """An architectural decision with rationale."""

    decision: str
    rationale: str
    alternatives: list[str]
    tradeoffs: str
    confidence: float  # 0-1


@dataclass
class ImplementationStep:
    """A single step in the implementation plan."""

    step_number: int
    phase: PlanPhase
    title: str
    description: str
    files_to_create: list[str] = field(default_factory=list)
    files_to_modify: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    estimated_minutes: int = 0
    verification: str = ''  # How to verify this step works


@dataclass
class ImplementationPlan:
    """Complete implementation plan."""

    # Overview
    project_name: str
    project_type: str
    one_line_summary: str

    # Architecture
    architecture_decisions: list[ArchitectureDecision]
    tech_stack: list[str]
    directory_structure: dict[str, str]

    # Features
    features: list[Feature]

    # Implementation steps
    phases: dict[PlanPhase, list[ImplementationStep]]

    # Success criteria
    success_criteria: list[str]
    quality_gates: list[str]

    # Estimates
    total_features: int
    total_steps: int
    estimated_total_hours: float

    # Risks
    risks: list[str]
    mitigations: list[str]


class PlanGenerator:
    """Generates detailed implementation plans from intent."""

    def generate(self, intent: ExtractedIntent) -> ImplementationPlan:
        """Generate a comprehensive implementation plan."""
        context = intent.context

        # Generate architecture decisions
        arch_decisions = self._generate_architecture_decisions(context)

        # Generate directory structure
        dir_structure = self._generate_directory_structure(context)

        # Generate features
        features = self._generate_features(intent)

        # Generate implementation steps
        phases = self._generate_phases(intent, features)

        # Generate success criteria
        success_criteria = self._generate_success_criteria(context)

        # Generate quality gates
        quality_gates = self._generate_quality_gates(context)

        # Calculate estimates
        total_hours = sum(f.estimated_hours for f in features)

        # Generate risks
        risks, mitigations = self._generate_risks(context)

        return ImplementationPlan(
            project_name=self._generate_project_name(intent),
            project_type=context.project_type.value,
            one_line_summary=self._generate_summary(intent),
            architecture_decisions=arch_decisions,
            tech_stack=intent.recommended_stack,
            directory_structure=dir_structure,
            features=features,
            phases=phases,
            success_criteria=success_criteria,
            quality_gates=quality_gates,
            total_features=len(features),
            total_steps=sum(len(steps) for steps in phases.values()),
            estimated_total_hours=total_hours,
            risks=risks,
            mitigations=mitigations,
        )

    def _generate_project_name(self, intent: ExtractedIntent) -> str:
        """Generate a project name from the intent."""
        # Use domain if available
        if intent.context.domain != 'general':
            return f'{intent.context.domain.title()} App'

        # Use primary goal
        words = intent.primary_goal.split()[:3]
        return ' '.join(w.title() for w in words)

    def _generate_summary(self, intent: ExtractedIntent) -> str:
        """Generate a one-line summary."""
        parts = []

        if intent.context.domain != 'general':
            parts.append(intent.context.domain.title())

        if intent.features:
            parts.append(f'with {", ".join(intent.features[:3])}')

        return ' '.join(parts) if parts else intent.primary_goal[:60]

    def _generate_architecture_decisions(
        self, context: UserContext
    ) -> list[ArchitectureDecision]:
        """Generate key architecture decisions."""
        decisions = []

        # Frontend architecture
        decisions.append(
            ArchitectureDecision(
                decision='Component-based React architecture',
                rationale='React provides excellent component reusability and a mature ecosystem',
                alternatives=['Vue.js', 'Svelte', 'Angular'],
                tradeoffs='React has larger bundle size but more community support',
                confidence=0.9,
            )
        )

        # Backend architecture
        if context.project_type in [ProjectType.PRODUCTION, ProjectType.ENTERPRISE]:
            decisions.append(
                ArchitectureDecision(
                    decision='Layered architecture (Router → Service → Repository)',
                    rationale='Clean separation of concerns, testable, maintainable',
                    alternatives=['Monolithic', 'Serverless', 'Microservices'],
                    tradeoffs='More files but better organization',
                    confidence=0.85,
                )
            )

        # Database
        decisions.append(
            ArchitectureDecision(
                decision='PostgreSQL as primary database',
                rationale='ACID compliance, excellent for structured data, great tooling',
                alternatives=['MongoDB', 'SQLite', 'MySQL'],
                tradeoffs='More setup than SQLite, less flexible than MongoDB for documents',
                confidence=0.8,
            )
        )

        # API design
        decisions.append(
            ArchitectureDecision(
                decision='RESTful API with OpenAPI specification',
                rationale='Standard, well-documented, easy to integrate',
                alternatives=['GraphQL', 'gRPC', 'tRPC'],
                tradeoffs='Less flexible than GraphQL but simpler to implement',
                confidence=0.85,
            )
        )

        return decisions

    def _generate_directory_structure(self, context: UserContext) -> dict[str, str]:
        """Generate recommended directory structure."""
        structure = {
            'frontend/': 'React application',
            'frontend/src/': 'Source code',
            'frontend/src/components/': 'Reusable UI components',
            'frontend/src/pages/': 'Route-level components',
            'frontend/src/hooks/': 'Custom React hooks',
            'frontend/src/api/': 'API client functions',
            'frontend/src/types/': 'TypeScript type definitions',
            'backend/': 'Python backend',
            'backend/app/': 'FastAPI application',
            'backend/app/routers/': 'API route handlers',
            'backend/app/services/': 'Business logic',
            'backend/app/models/': 'Database models',
            'backend/app/schemas/': 'Pydantic schemas',
            'backend/tests/': 'Test files',
            'docs/': 'Documentation',
        }

        if context.project_type in [ProjectType.PRODUCTION, ProjectType.ENTERPRISE]:
            structure.update(
                {
                    'backend/app/middleware/': 'Custom middleware',
                    'backend/app/utils/': 'Utility functions',
                    'backend/alembic/': 'Database migrations',
                    '.github/workflows/': 'CI/CD pipelines',
                    'docker/': 'Docker configuration',
                }
            )

        return structure

    def _generate_features(self, intent: ExtractedIntent) -> list[Feature]:
        """Generate detailed feature list."""
        features = []

        # Always include these
        features.append(
            Feature(
                name='Project Setup',
                description='Initialize project with chosen tech stack',
                priority='critical',
                complexity='simple',
                estimated_hours=1.0,
                acceptance_criteria=['Project runs locally', 'Linting configured'],
            )
        )

        features.append(
            Feature(
                name='Core UI Layout',
                description='Main layout with navigation and responsive design',
                priority='critical',
                complexity='moderate',
                estimated_hours=3.0,
                acceptance_criteria=[
                    'Responsive on mobile/tablet/desktop',
                    'Navigation works',
                ],
            )
        )

        # Add requested features
        feature_specs = {
            'authentication': Feature(
                name='Authentication System',
                description='Login, signup, password reset, session management',
                priority='critical',
                complexity='complex',
                estimated_hours=8.0,
                dependencies=['Project Setup', 'Core UI Layout'],
                acceptance_criteria=[
                    'Users can sign up and log in',
                    'Sessions persist across page reloads',
                    'Password reset flow works',
                ],
            ),
            'dashboard': Feature(
                name='Dashboard',
                description='Main dashboard with key metrics and visualizations',
                priority='high',
                complexity='moderate',
                estimated_hours=5.0,
                dependencies=['Authentication System'],
                acceptance_criteria=[
                    'Dashboard displays key metrics',
                    'Charts render correctly',
                    'Data refreshes automatically',
                ],
            ),
            'payments': Feature(
                name='Payment Integration',
                description='Stripe integration for subscriptions and one-time payments',
                priority='high',
                complexity='complex',
                estimated_hours=10.0,
                dependencies=['Authentication System'],
                acceptance_criteria=[
                    'Users can enter payment details',
                    'Subscriptions create correctly',
                    'Webhooks handle events',
                ],
            ),
            'real-time': Feature(
                name='Real-time Features',
                description='WebSocket-based real-time updates',
                priority='medium',
                complexity='complex',
                estimated_hours=6.0,
                dependencies=['Core UI Layout'],
                acceptance_criteria=[
                    'Updates appear in real-time',
                    'Connection handles reconnection',
                    'Multiple clients sync',
                ],
            ),
            'admin': Feature(
                name='Admin Panel',
                description='Admin interface for managing users and content',
                priority='medium',
                complexity='moderate',
                estimated_hours=6.0,
                dependencies=['Authentication System'],
                acceptance_criteria=[
                    'Admins can view all users',
                    'Content can be managed',
                    'Roles are enforced',
                ],
            ),
            'api': Feature(
                name='API Layer',
                description='RESTful API with proper error handling',
                priority='critical',
                complexity='moderate',
                estimated_hours=4.0,
                dependencies=['Project Setup'],
                acceptance_criteria=[
                    'All endpoints return proper status codes',
                    'Error responses are consistent',
                    'API documentation is generated',
                ],
            ),
            'database': Feature(
                name='Database Layer',
                description='Database models, migrations, and repository pattern',
                priority='critical',
                complexity='moderate',
                estimated_hours=4.0,
                dependencies=['Project Setup'],
                acceptance_criteria=[
                    'Models are defined',
                    'Migrations run successfully',
                    'CRUD operations work',
                ],
            ),
            'search': Feature(
                name='Search Functionality',
                description='Full-text search with filtering and pagination',
                priority='medium',
                complexity='moderate',
                estimated_hours=4.0,
                dependencies=['Database Layer'],
                acceptance_criteria=[
                    'Search returns relevant results',
                    'Filters work correctly',
                    'Pagination functions',
                ],
            ),
            'testing': Feature(
                name='Test Suite',
                description='Unit tests, integration tests, and E2E tests',
                priority='high',
                complexity='moderate',
                estimated_hours=6.0,
                dependencies=['Core UI Layout', 'API Layer'],
                acceptance_criteria=[
                    'Unit tests pass',
                    'Integration tests pass',
                    'Coverage > 80%',
                ],
            ),
            'deployment': Feature(
                name='Deployment Configuration',
                description='Docker, CI/CD, and deployment scripts',
                priority='high',
                complexity='moderate',
                estimated_hours=4.0,
                dependencies=['Test Suite'],
                acceptance_criteria=[
                    'Docker build succeeds',
                    'CI pipeline runs',
                    'Can deploy to production',
                ],
            ),
        }

        for feature_name in intent.features:
            if feature_name in feature_specs:
                features.append(feature_specs[feature_name])

        return features

    def _generate_phases(
        self, intent: ExtractedIntent, features: list[Feature]
    ) -> dict[PlanPhase, list[ImplementationStep]]:
        """Generate implementation phases with detailed steps."""
        phases: dict[PlanPhase, list[ImplementationStep]] = {
            PlanPhase.FOUNDATION: [],
            PlanPhase.CORE_FEATURES: [],
            PlanPhase.SECONDARY_FEATURES: [],
            PlanPhase.POLISH: [],
            PlanPhase.TESTING: [],
            PlanPhase.DEPLOYMENT: [],
        }

        step_counter = 1

        # Foundation phase
        phases[PlanPhase.FOUNDATION].extend(
            [
                ImplementationStep(
                    step_number=step_counter,
                    phase=PlanPhase.FOUNDATION,
                    title='Initialize Project',
                    description='Set up project structure with chosen tech stack',
                    files_to_create=[
                        'frontend/package.json',
                        'frontend/tsconfig.json',
                        'frontend/vite.config.ts',
                        'backend/pyproject.toml',
                        'backend/app/__init__.py',
                    ],
                    commands=[
                        'npm create vite@latest frontend -- --template react-ts',
                        'cd backend && poetry init',
                    ],
                    estimated_minutes=30,
                    verification='Both frontend and backend start without errors',
                ),
                ImplementationStep(
                    step_number=step_counter + 1,
                    phase=PlanPhase.FOUNDATION,
                    title='Configure Linting and Formatting',
                    description='Set up ESLint, Prettier, Ruff, and pre-commit hooks',
                    files_to_create=[
                        'frontend/.eslintrc.js',
                        'frontend/.prettierrc',
                        'backend/pyproject.toml (ruff config)',
                        '.pre-commit-config.yaml',
                    ],
                    commands=[
                        'cd frontend && npm install -D eslint prettier',
                        'cd backend && poetry add --group dev ruff',
                    ],
                    estimated_minutes=20,
                    verification='Linting passes on all files',
                ),
            ]
        )
        step_counter += 2

        # Core features phase
        for feature in features:
            if feature.priority in ['critical', 'high']:
                phases[PlanPhase.CORE_FEATURES].append(
                    ImplementationStep(
                        step_number=step_counter,
                        phase=PlanPhase.CORE_FEATURES,
                        title=f'Implement {feature.name}',
                        description=feature.description,
                        estimated_minutes=int(feature.estimated_hours * 60),
                        verification=f'{feature.name} acceptance criteria met',
                    )
                )
                step_counter += 1

        # Secondary features phase
        for feature in features:
            if feature.priority in ['medium', 'low']:
                phases[PlanPhase.SECONDARY_FEATURES].append(
                    ImplementationStep(
                        step_number=step_counter,
                        phase=PlanPhase.SECONDARY_FEATURES,
                        title=f'Implement {feature.name}',
                        description=feature.description,
                        estimated_minutes=int(feature.estimated_hours * 60),
                        verification=f'{feature.name} acceptance criteria met',
                    )
                )
                step_counter += 1

        # Polish phase
        phases[PlanPhase.POLISH].extend(
            [
                ImplementationStep(
                    step_number=step_counter,
                    phase=PlanPhase.POLISH,
                    title='Responsive Design',
                    description='Ensure all pages work on mobile, tablet, and desktop',
                    estimated_minutes=60,
                    verification='Pages look good on all screen sizes',
                ),
                ImplementationStep(
                    step_number=step_counter + 1,
                    phase=PlanPhase.POLISH,
                    title='Animations and Transitions',
                    description='Add smooth animations and page transitions',
                    estimated_minutes=45,
                    verification='Animations are smooth and non-jarring',
                ),
            ]
        )
        step_counter += 2

        # Testing phase
        phases[PlanPhase.TESTING].extend(
            [
                ImplementationStep(
                    step_number=step_counter,
                    phase=PlanPhase.TESTING,
                    title='Write Unit Tests',
                    description='Write unit tests for all services and utilities',
                    estimated_minutes=120,
                    verification='All unit tests pass',
                ),
                ImplementationStep(
                    step_number=step_counter + 1,
                    phase=PlanPhase.TESTING,
                    title='Write Integration Tests',
                    description='Write integration tests for API endpoints',
                    estimated_minutes=90,
                    verification='All integration tests pass',
                ),
            ]
        )
        step_counter += 2

        # Deployment phase
        phases[PlanPhase.DEPLOYMENT].extend(
            [
                ImplementationStep(
                    step_number=step_counter,
                    phase=PlanPhase.DEPLOYMENT,
                    title='Docker Configuration',
                    description='Create Dockerfiles and docker-compose.yml',
                    files_to_create=[
                        'docker/Dockerfile.frontend',
                        'docker/Dockerfile.backend',
                        'docker-compose.yml',
                    ],
                    estimated_minutes=45,
                    verification='Docker build succeeds',
                ),
                ImplementationStep(
                    step_number=step_counter + 1,
                    phase=PlanPhase.DEPLOYMENT,
                    title='CI/CD Pipeline',
                    description='Set up GitHub Actions for testing and deployment',
                    files_to_create=[
                        '.github/workflows/test.yml',
                        '.github/workflows/deploy.yml',
                    ],
                    estimated_minutes=30,
                    verification='CI pipeline runs successfully',
                ),
            ]
        )

        return phases

    def _generate_success_criteria(self, context: UserContext) -> list[str]:
        """Generate success criteria."""
        criteria = [
            'Application runs without errors',
            'All critical features work as expected',
            'Code passes linting and type checks',
            'Basic tests are in place',
        ]

        if context.project_type in [ProjectType.PRODUCTION, ProjectType.ENTERPRISE]:
            criteria.extend(
                [
                    'Error handling is comprehensive',
                    'Security best practices are followed',
                    'Performance is acceptable (< 2s load time)',
                    'Documentation is complete',
                ]
            )

        if context.expertise == ExpertiseLevel.BEGINNER:
            criteria.append('Code is well-commented and explained')

        return criteria

    def _generate_quality_gates(self, context: UserContext) -> list[str]:
        """Generate quality gates."""
        gates = [
            'Linting passes (0 errors)',
            'Type checking passes (0 errors)',
            'All tests pass',
        ]

        if context.project_type in [ProjectType.PRODUCTION, ProjectType.ENTERPRISE]:
            gates.extend(
                [
                    'No security vulnerabilities (npm audit, safety)',
                    'Test coverage > 80%',
                    'API documentation is generated',
                    'Docker build succeeds',
                ]
            )

        return gates

    def _generate_risks(self, context: UserContext) -> tuple[list[str], list[str]]:
        """Generate risks and mitigations."""
        risks = []
        mitigations = []

        if 'payments' in context.features:
            risks.append('Payment integration complexity')
            mitigations.append('Use Stripe Checkout for simplified flow')

        if 'real-time' in context.features:
            risks.append('WebSocket connection management')
            mitigations.append('Use Socket.io with automatic reconnection')

        if context.project_type == ProjectType.ENTERPRISE:
            risks.append('Scope creep in enterprise features')
            mitigations.append('Implement MVP first, iterate based on feedback')

        if not context.tech_preferences:
            risks.append('Tech stack mismatch with user expertise')
            mitigations.append('Use proven, well-documented technologies')

        return risks, mitigations
