"""Pre-start goal detector that analyzes initial messages for massive project goals.

When a user's initial message matches known manager triggers (massive project,
large goal, complex system, etc.), the detector auto-decomposes the goal into
structured sub-tasks and injects them into the conversation context BEFORE
the agent starts.

This ensures the agent enters manager mode automatically — no skill trigger
reliance needed.
"""

import logging
import os
import re
from typing import Any

from wren.app_server.orchestration.working_memory import WorkingMemory

_logger = logging.getLogger(__name__)

# Keywords that indicate a massive/complex project goal
MANAGER_TRIGGER_PATTERNS = [
    r'\b(build|create|develop|implement)\s+(a|an|the)\s+(full|complete|entire|complex|large)\b',
    r'\b(massive|complex|large.?scale|big|major)\s+(project|goal|system|app|platform|feature)\b',
    r'\b(full.?stack|end.?to.?end|complete\s+system)\b',
    r'\b(microservices|multi.?service|distributed\s+system)\b',
    r'\b(architect|architecture|design\s+the\s+(whole|entire|full))\b',
    r'\b(decompose|break\s+down|split\s+into)\b',
    r'\b(phase[12]|milestone|epic)\b',
]

# Technology-specific triggers that suggest multi-step projects
TECH_TRIGGERS = [
    r'\b(database|postgres|mysql|redis|mongo)\b',
    r'\b(docker|kubernetes|k8s|container)\b',
    r'\b(api|graphql|rest|grpc|endpoint)\b',
    r'\b(auth|auth[sz]|login|oauth|jwt|sso)\b',
    r'\b(deploy|ci/cd|pipeline|infrastructure)\b',
    r'\b(frontend|backend|full.?stack|ui|ux)\b',
    r'\b(microservice|service|module|component)\b',
    r'\b(pipeline|workflow|etl|data\s+processing)\b',
]

# Aggressive threshold — triggers on fewer keywords
COMPLEX_GOAL_THRESHOLD = 3  # any 3 patterns or 2 patterns + 3 tech triggers


class GoalDetector:
    """Analyzes initial conversation messages for massive project goals.

    If the goal is complex enough, it:
    1. Auto-decomposes into sub-tasks
    2. Writes decomposition to working memory
    3. Returns a system instruction payload that gets injected into
       the agent's context before it starts executing
    """

    def __init__(self, project_root: str | None = None):
        self._project_root = project_root or os.getcwd()

    def analyze(self, message: str) -> dict[str, Any]:
        """Analyze an initial message for manager-mode suitability.

        Returns a dict with:
            is_complex_goal: bool
            trigger_count: int
            tech_count: int
            auto_decomposition: list[dict] | None — decomposed sub-tasks
            system_instruction: str | None — injected context
        """
        msg_lower = message.lower()
        pattern_matches = sum(
            1 for p in MANAGER_TRIGGER_PATTERNS if re.search(p, msg_lower)
        )
        tech_matches = sum(1 for t in TECH_TRIGGERS if re.search(t, msg_lower))

        score = pattern_matches + (tech_matches * 0.5)
        is_complex = score >= COMPLEX_GOAL_THRESHOLD or pattern_matches >= 2

        result: dict[str, Any] = {
            'is_complex_goal': is_complex,
            'trigger_count': pattern_matches,
            'tech_count': tech_matches,
            'score': score,
            'auto_decomposition': None,
            'system_instruction': None,
        }

        if is_complex:
            decomposition = self._decompose(message, tech_matches)
            result['auto_decomposition'] = decomposition

            # Write to working memory so the agent sees it via summary()
            wm = WorkingMemory(self._project_root)
            wm.add_decision(
                f'Goal auto-detected as complex project. Decomposed into '
                f'{len(decomposition)} sub-tasks.',
                context='goal_detector',
            )
            for task in decomposition:
                wm.add_todo(
                    task=task['name'],
                    depends_on=task.get('depends_on', []),
                )

            result['system_instruction'] = self._build_instruction(
                message, decomposition
            )
            _logger.info(
                'GoalDetector: complex goal detected (score=%.1f), %d sub-tasks',
                score,
                len(decomposition),
            )

        return result

    def injectable_context(self, message: str) -> str | None:
        """Return a system-level instruction block if the message is a complex goal.

        This gets injected into the LLM context BEFORE the agent starts,
        so the agent enters manager mode immediately — no skill trigger delay.
        """
        result = self.analyze(message)
        return result.get('system_instruction')

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _decompose(
        self,
        message: str,
        tech_count: int,
    ) -> list[dict[str, Any]]:
        """Auto-decompose a goal into sub-tasks based on keyword analysis.

        Uses pattern matching to identify likely project phases and injects
        sensible defaults for common tech stacks. The agent can refine these
        once it starts.
        """
        msg_lower = message.lower()
        tasks: list[dict[str, Any]] = []

        # Phase 1: Setup & Infrastructure
        infra_tasks = []
        if re.search(r'\b(docker|container|k8s|kubernetes|deploy)\b', msg_lower):
            infra_tasks.append(
                {
                    'name': 'Setup infrastructure',
                    'description': 'Provision Docker containers, configure networking, set up CI/CD pipeline',
                    'depends_on': [],
                    'estimated_effort': 'medium',
                    'acceptance_criteria': [
                        'All services containerized',
                        'CI pipeline passes',
                    ],
                }
            )
        if re.search(r'\b(database|postgres|mysql|redis|mongo|sqlite)\b', msg_lower):
            infra_tasks.append(
                {
                    'name': 'Setup database',
                    'description': 'Provision database, create schemas, run migrations',
                    'depends_on': ['Setup infrastructure'] if infra_tasks else [],
                    'estimated_effort': 'medium',
                    'acceptance_criteria': [
                        'Database accessible',
                        'Migrations run cleanly',
                        'Seed data loaded',
                    ],
                }
            )

        tasks.extend(infra_tasks)
        infra_dep = [t['name'] for t in infra_tasks]

        # Phase 2: Core domain logic
        backend_task = None
        if re.search(r'\b(api|backend|server|graphql|rest|grpc|endpoint)\b', msg_lower):
            backend_task = {
                'name': 'Implement backend API',
                'description': 'Build REST/GraphQL API with business logic, validation, and error handling',
                'depends_on': infra_dep,
                'estimated_effort': 'large',
                'acceptance_criteria': [
                    'All endpoints return correct responses',
                    'Input validation works',
                    'Error handling covers edge cases',
                ],
            }
            tasks.append(backend_task)

        frontend_task = None
        if re.search(
            r'\b(frontend|ui|ux|web|react|vue|angular|component)\b', msg_lower
        ):
            frontend_task = {
                'name': 'Implement frontend UI',
                'description': 'Build user interface with components, state management, and routing',
                'depends_on': [backend_task['name']] if backend_task else infra_dep,
                'estimated_effort': 'large',
                'acceptance_criteria': [
                    'All pages render correctly',
                    'State management works',
                    'Responsive layout',
                ],
            }
            tasks.append(frontend_task)

        # Auth layer
        if re.search(r'\b(auth|login|oauth|jwt|sso|permission)\b', msg_lower):
            auth_task = {
                'name': 'Implement authentication & authorization',
                'description': 'Add user login, role-based access, session management',
                'depends_on': [backend_task['name']] if backend_task else infra_dep,
                'estimated_effort': 'medium',
                'acceptance_criteria': [
                    'Users can register and login',
                    'Role-based access enforced',
                    'Sessions expire correctly',
                ],
            }
            tasks.append(auth_task)

        # Testing
        testing_deps = []
        if backend_task:
            testing_deps.append(backend_task['name'])
        if frontend_task:
            testing_deps.append(frontend_task['name'])
        tasks.append(
            {
                'name': 'Write tests & verify',
                'description': 'Write unit tests, integration tests, and run full verification suite',
                'depends_on': testing_deps or infra_dep,
                'estimated_effort': 'medium',
                'acceptance_criteria': [
                    'All tests pass',
                    'Coverage meets threshold',
                    'Edge cases covered',
                ],
            }
        )

        # Final integration
        all_deps = [t['name'] for t in tasks if t['name'] != 'Write tests & verify']
        tasks.append(
            {
                'name': 'Integration & final review',
                'description': 'Run end-to-end tests, verify all components work together, final polish',
                'depends_on': all_deps,
                'estimated_effort': 'small',
                'acceptance_criteria': [
                    'All sub-tasks complete',
                    'E2E tests pass',
                    'Documentation updated',
                ],
            }
        )

        return tasks

    def _build_instruction(
        self,
        message: str,
        decomposition: list[dict[str, Any]],
    ) -> str:
        """Build a manager-mode system instruction to inject into agent context."""
        task_lines = []
        for i, t in enumerate(decomposition, 1):
            deps = f' [after: {", ".join(t["depends_on"])}]' if t['depends_on'] else ''
            task_lines.append(f'  {i}. **{t["name"]}**{deps} — {t["description"]}')

        return f"""## MANAGER MODE AUTO-ACTIVATED

The user's request was detected as a **complex project goal**. You are in **manager mode**.

### Your role
You are the **manager**. Do NOT implement everything yourself.
Decompose, delegate, review, and integrate.

### Auto-detected sub-task plan

{chr(10).join(task_lines)}

### How to operate
1. Review the decomposition above — refine it with the user if needed
2. For each sub-task whose dependencies are met, delegate to a sub-agent
   using `task()` with the sub-task's description and acceptance criteria
3. Track progress in `.wren/working_memory.json`
4. After each sub-task, run a quick self-reflection
5. After all sub-tasks, integrate and present the final result

### Working memory
Already initialized at `.wren/working_memory.json`. Call
`WorkingMemory.summary()` to see current state.
"""
