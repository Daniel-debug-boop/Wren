"""
Planner Agent — transforms architecture designs into step-by-step implementation plans.

The Planner takes an ArchitectureDesign (from ArchitectAgent) and produces a detailed
ImplementationPlan that maps out:
  - Exact file generation order (topological sort respecting dependencies)
  - Code patterns and conventions to use per file
  - Testing strategy per module
  - Risk assessment and mitigation strategies
  - Estimated effort per file

This plan is consumed by WriterAgent to generate actual code.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Any

from wren.app_builder.agents.architect_agent import ArchitectureDesign, ComponentSpec
from wren.app_builder.llm_client import LLMClient

_logger = logging.getLogger(__name__)


# ── Data models ───────────────────────────────────────────────────────────


@dataclass
class FilePlan:
    """Detailed plan for generating a single file."""

    path: str
    purpose: str
    dependencies: list[str] = field(default_factory=list)
    design_pattern: str = ""
    estimated_lines: int = 0
    complexity: str = "medium"  # low, medium, high
    risk_factors: list[str] = field(default_factory=list)
    testing_approach: str = ""
    key_functions: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class ImplementationPlan:
    """Complete implementation plan produced by the PlannerAgent."""

    project_name: str
    summary: str
    phases: list[dict[str, Any]] = field(default_factory=list)  # [{name, description, files: [...]}]
    files: list[FilePlan] = field(default_factory=list)
    tech_decisions: list[dict[str, str]] = field(default_factory=list)  # [{decision, rationale, alternatives}]
    risks: list[dict[str, str]] = field(default_factory=list)  # [{risk, mitigation, severity}]
    test_strategy: str = ""
    estimated_total_lines: int = 0
    estimated_complexity: str = "medium"

    def get_file_order(self) -> list[str]:
        """Get files sorted by dependency order."""
        return [f.path for f in self.files]

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "summary": self.summary,
            "phases": self.phases,
            "files": [asdict(f) for f in self.files],
            "tech_decisions": self.tech_decisions,
            "risks": self.risks,
            "test_strategy": self.test_strategy,
            "estimated_total_lines": self.estimated_total_lines,
            "estimated_complexity": self.estimated_complexity,
        }


# ── System Prompt ─────────────────────────────────────────────────────────


PLANNER_SYSTEM_PROMPT = """\
# WREN PLANNER: STRATEGIC IMPLEMENTATION ARCHITECT

You are Wren Planner — a world-class implementation strategist. You transform 
architecture blueprints into precise, executable implementation plans that 
rival those of senior staff engineers at FAANG companies.

## YOUR TASK:
Given a complete ArchitectureDesign (components, data models, routes, tech stack),
produce a JSON implementation plan that answers:

1. WHAT ORDER should files be generated? (Dependency-first, topological sort)
2. WHAT DESIGN PATTERNS apply to each file? (Singleton, Factory, Repository, etc.)
3. WHAT ARE THE RISKS? (WebGL context loss, race conditions, auth security)
4. HOW should each file be tested? (Unit, integration, e2e)
5. WHAT TECH DECISIONS are needed? (Library choices, caching strategy, error handling)

## OUTPUT JSON SCHEMA:

```json
{
  "projectName": "project-name",
  "summary": "One-paragraph implementation strategy",
  "phases": [
    {
      "name": "Phase 1: Foundation",
      "description": "Core infrastructure and configuration",
      "files": ["package.json", "tsconfig.json", "vite.config.ts"]
    },
    {
      "name": "Phase 2: Data Layer",
      "description": "Database models and API layer",
      "files": ["src/db.py", "src/models.py"]
    },
    {
      "name": "Phase 3: UI Components",
      "description": "React components and 3D scenes",
      "files": ["src/components/Scene.tsx", "src/App.tsx"]
    }
  ],
  "files": [
    {
      "path": "src/components/Scene.tsx",
      "purpose": "Main 3D scene with Three.js rendering",
      "dependencies": ["src/utils/three-helpers.ts", "package.json"],
      "designPattern": "Component pattern with render-loop separation",
      "estimatedLines": 180,
      "complexity": "high",
      "riskFactors": ["WebGL context loss needs recovery", "GPU memory leaks on unmount"],
      "testingApproach": "Snapshot + manual visual verification",
      "keyFunctions": ["Scene()", "useFrame animation loop"],
      "notes": ["Use React.memo for performance", "Implement dispose() in useEffect cleanup"]
    }
  ],
  "techDecisions": [
    {
      "decision": "Use Zustand over Redux for state management",
      "rationale": "Smaller bundle size, simpler API, sufficient for this project scale",
      "alternatives": ["Redux Toolkit", "Jotai", "Context API"]
    },
    {
      "decision": "Use SQLite for local development",
      "rationale": "Zero configuration, file-based, sufficient for MVP",
      "alternatives": ["PostgreSQL", "MySQL"]
    }
  ],
  "risks": [
    {
      "risk": "WebGL context loss on mobile devices",
      "mitigation": "Implement graceful fallback with Canvas2D, auto-retry with exponential backoff",
      "severity": "high"
    },
    {
      "risk": "JWT token exposure in client-side code",
      "mitigation": "Use httpOnly cookies for refresh tokens, short-lived access tokens (15min)",
      "severity": "critical"
    }
  ],
  "testStrategy": "Vitest for unit tests (components, utils), Playwright for e2e (auth flow, 3D rendering)",
  "estimatedTotalLines": 4500,
  "estimatedComplexity": "high"
}
```

## ANALYSIS FRAMEWORK:
For each file in the plan, consider:

### 3D / WEBGL FILES:
- GPU resource lifecycle (geometry.dispose(), material.dispose(), texture.dispose())
- WebGL context loss handling with recovery
- Responsive canvas sizing (ResizeObserver)
- Animation frame management (cleanup on unmount)
- Asset loading with progress indicators
- LOD (Level of Detail) for performance

### DATABASE FILES:
- Connection pooling configuration
- Migration strategy
- Query optimization (N+1 prevention)
- Transaction handling

### API FILES:
- Input validation (Pydantic/schema)
- Rate limiting
- Error handling middleware
- CORS configuration
- Response compression

### AUTH FILES:
- Token refresh flow
- Password hashing (bcrypt/argon2)
- Session management
- OAuth state parameter for CSRF protection

## OUTPUT RULES:
- Files MUST be in dependency order (dependencies before dependents)
- Every file from the architecture must be included
- Be specific about risk mitigation — not just "add error handling" but HOW
- Include estimated line counts for planning
- Design patterns must be concrete and appropriate
"""


# ── Planner Agent ─────────────────────────────────────────────────────────


class PlannerAgent:
    """Agent that transforms an ArchitectureDesign into an ImplementationPlan."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        api_key: str = "",
        model: str = "gpt-4o",
        base_url: str | None = None,
    ):
        if llm_client:
            self._llm = llm_client
        else:
            self._llm = LLMClient(api_key=api_key, model=model, base_url=base_url)

    async def plan(self, design: ArchitectureDesign) -> ImplementationPlan:
        """Create a detailed implementation plan from an architecture design."""
        _logger.info("PlannerAgent: planning implementation for %s", design.project_name)
        start = time.time()

        # Build a compact representation of the architecture for the prompt
        arch_summary = self._summarize_architecture(design)

        system_prompt = PLANNER_SYSTEM_PROMPT

        user_prompt = (
            f"Create a detailed implementation plan for this architecture:\n\n"
            f"{arch_summary}\n\n"
            f"Output ONLY the JSON plan inside a ```json fenced code block."
        )

        response = await self._llm.send(system_prompt, user_prompt)
        plan = self._parse_plan(response, design)

        elapsed = time.time() - start
        _logger.info(
            "PlannerAgent: plan complete — %d files, %d tech decisions, %d risks (%.1fs)",
            len(plan.files),
            len(plan.tech_decisions),
            len(plan.risks),
            elapsed,
        )
        return plan

    def _summarize_architecture(self, design: ArchitectureDesign) -> str:
        """Build a compact architecture summary for the prompt."""
        parts: list[str] = []

        parts.append(f"=== ARCHITECTURE DESIGN ===")
        parts.append(f"Project: {design.project_name}")
        parts.append(f"Type: {design.project_type}")
        parts.append(f"Summary: {design.summary}")
        parts.append(f"Tech Stack: {json.dumps(design.tech_stack, indent=2)}")
        parts.append(f"Auth: {design.auth_strategy}")
        parts.append(f"Database: {design.database_type}")
        parts.append(f"Has 3D: {design.has_3d}")
        parts.append(f"Has Game: {design.has_game}")

        # Components
        parts.append(f"\n=== COMPONENTS ({len(design.components)}) ===")
        for c in design.components:
            parts.append(
                f"  {c.name} ({c.path})\n"
                f"    Purpose: {c.purpose}\n"
                f"    Complexity: {c.estimated_complexity}\n"
                f"    3D: {c.is_3d}\n"
                f"    Game: {c.is_game}\n"
                f"    Dependencies: {c.dependencies}"
            )

        # Data models
        if design.data_models:
            parts.append(f"\n=== DATA MODELS ({len(design.data_models)}) ===")
            for m in design.data_models:
                field_names = [f["name"] for f in m.fields]
                parts.append(f"  {m.name} ({m.storage_type}): fields={field_names}")

        # Routes
        if design.routes:
            parts.append(f"\n=== ROUTES ({len(design.routes)}) ===")
            for r in design.routes:
                auth = " 🔒" if r.auth_required else ""
                parts.append(f"  {r.method} {r.path}{auth}")

        # File dependency order
        if design.file_dependency_order:
            parts.append(f"\n=== FILE DEPENDENCY ORDER ===")
            for i, f in enumerate(design.file_dependency_order, 1):
                parts.append(f"  {i}. {f}")

        # Warnings
        if design.warnings:
            parts.append(f"\n=== WARNINGS ===")
            for w in design.warnings:
                parts.append(f"  ⚠ {w}")

        return "\n".join(parts)

    def _parse_plan(self, response: str, design: ArchitectureDesign) -> ImplementationPlan:
        """Parse the LLM response into an ImplementationPlan."""
        # Extract JSON from code block
        json_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL
        )
        json_str = json_match.group(1) if json_match else response

        if not json_match:
            obj_match = re.search(r"\{[^{}]*\"projectName\"[^{}]*\}", response, re.DOTALL)
            if obj_match:
                json_str = obj_match.group()

        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Failed to parse implementation plan JSON: {e}\n"
                f"Response snippet: {response[:500]}"
            )

        # Parse files
        files = []
        for fp in data.get("files", []):
            if isinstance(fp, dict):
                files.append(FilePlan(
                    path=fp.get("path", ""),
                    purpose=fp.get("purpose", ""),
                    dependencies=fp.get("dependencies", []),
                    design_pattern=fp.get("designPattern", ""),
                    estimated_lines=fp.get("estimatedLines", 0),
                    complexity=fp.get("complexity", "medium"),
                    risk_factors=fp.get("riskFactors", []),
                    testing_approach=fp.get("testingApproach", ""),
                    key_functions=fp.get("keyFunctions", []),
                    notes=fp.get("notes", []),
                ))

        return ImplementationPlan(
            project_name=data.get("projectName", design.project_name),
            summary=data.get("summary", ""),
            phases=data.get("phases", []),
            files=files,
            tech_decisions=data.get("techDecisions", []),
            risks=data.get("risks", []),
            test_strategy=data.get("testStrategy", ""),
            estimated_total_lines=data.get("estimatedTotalLines", 0),
            estimated_complexity=data.get("estimatedComplexity", "medium"),
        )

    async def close(self) -> None:
        await self._llm.close()
