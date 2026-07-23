"""Architect Agent — designs the full system architecture before a single file is generated.

The Architect takes a high-level prompt and produces a comprehensive
ArchitectureDesign document covering:
  - System architecture (frontend/backend/DB layout)
  - Component tree with props/state
  - Data models and database schema
  - API routes and endpoints
  - Authentication strategy
  - 3D/WebGL scene architecture (if applicable)
  - File dependency graph (which files depend on which)
  - Technology stack recommendations

This design document is consumed by PlannerAgent → WriterAgent → ReviewerAgent.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Any

_logger = logging.getLogger(__name__)


# ── Data models ───────────────────────────────────────────────────────────


@dataclass
class ComponentSpec:
    """Specification for a single UI or logic component."""

    name: str
    path: str  # Relative file path (e.g., "src/components/Scene.tsx")
    purpose: str
    props: list[str] = field(default_factory=list)
    state: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)  # Other components/files this depends on
    is_3d: bool = False
    is_game: bool = False
    estimated_complexity: str = "medium"  # low, medium, high


@dataclass
class DataModelSpec:
    """Specification for a data model / database entity."""

    name: str
    fields: list[dict[str, str]] = field(default_factory=list)  # [{name, type, constraints}]
    relationships: list[dict[str, str]] = field(default_factory=list)
    storage_type: str = "memory"  # memory, sqlite, postgres, firebase


@dataclass
class RouteSpec:
    """Specification for an API route or page route."""

    path: str
    method: str = "GET"  # GET, POST, PUT, DELETE
    purpose: str = ""
    auth_required: bool = False
    response_type: str = "json"


@dataclass
class ArchitectureDesign:
    """Complete architecture design document produced by the ArchitectAgent."""

    project_name: str
    project_type: str  # web, mobile, api, desktop, cli, 3d-web
    summary: str
    tech_stack: dict[str, str] = field(default_factory=dict)
    components: list[ComponentSpec] = field(default_factory=list)
    data_models: list[DataModelSpec] = field(default_factory=list)
    routes: list[RouteSpec] = field(default_factory=list)
    auth_strategy: str = "none"
    database_type: str = "none"
    file_dependency_order: list[str] = field(default_factory=list)  # Ordered file paths
    warnings: list[str] = field(default_factory=list)
    has_3d: bool = False
    has_game: bool = False
    additional_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "project_type": self.project_type,
            "summary": self.summary,
            "tech_stack": self.tech_stack,
            "components": [asdict(c) for c in self.components],
            "data_models": [asdict(d) for d in self.data_models],
            "routes": [asdict(r) for r in self.routes],
            "auth_strategy": self.auth_strategy,
            "database_type": self.database_type,
            "file_dependency_order": self.file_dependency_order,
            "warnings": self.warnings,
            "has_3d": self.has_3d,
            "has_game": self.has_game,
            "additional_context": self.additional_context,
        }


from wren.app_builder.llm_client import LLMClient


# ── System Prompt for Architecture Design ─────────────────────────────────

ARCHITECT_SYSTEM_PROMPT = """\
# WREN ARCHITECT: FULL-SPECTRUM SYSTEM DESIGNER

You are Wren Architect — a world-class software architect that produces exhaustive, 
production-ready architecture blueprints. Your designs rival those of senior staff 
engineers at FAANG companies. You NEVER miss system components.

## ANALYSIS FRAMEWORK:
For EVERY project directive, analyze ALL of these dimensions:

1. PROJECT TYPE: web | 3d-web | game-2d | game-3d | mobile | api | desktop | cli
2. RENDERING NEEDS: Vanilla HTML/CSS | React/Vue/Svelte | Three.js/R3F | Phaser/PixiJS | Canvas2D | WebGPU
3. GAME ENGINE NEEDS: Phaser 3 (2D) | Three.js/R3F (3D) | Custom game loop | No game logic
4. DATABASE: None | SQLite | PostgreSQL | MySQL | Firebase/Firestore | Supabase | Redis
5. AUTHENTICATION: None | JWT | OAuth 2.0 | Session | Passkeys | Firebase Auth | Supabase Auth
6. API LAYER: None | REST | GraphQL | tRPC | WebSocket | gRPC
7. STATE MANAGEMENT: None | Zustand | Redux | Context | Jotai | Valtio
8. TESTING: None | Vitest | Jest | Playwright | Cypress | pytest
9. DEPLOYMENT: Static | Docker | Vercel | Netlify | Railway | GitHub Pages
10. FILE ORGANIZATION: Feature-first | Type-first | Domain-driven | Monorepo

## OUTPUT JSON SCHEMA:

```json
{
  "projectName": "kebab-case-project-name",
  "projectType": "web|3d-web|game-2d|game-3d|mobile|api|desktop|cli",
  "summary": "One-paragraph architecture summary explaining the full system design",
  "techStack": {
    "frontend": "React 19 + Vite + Tailwind",
    "backend": "FastAPI + SQLAlchemy",
    "database": "SQLite",
    "auth": "JWT with refresh tokens",
    "3d": "Three.js + React-Three-Fiber",
    "game": "Phaser 3 (2D) or Three.js/R3F (3D)",
    "testing": "Vitest + Playwright",
    "deployment": "Docker + Railway",
    "state": "Zustand with persist middleware",
    "api": "RESTful with tRPC optional"
  },
  "components": [
    {
      "name": "SolarSystem",
      "path": "src/components/SolarSystem.tsx",
      "purpose": "Main 3D scene with orbiting planets and interactive camera",
      "props": ["speed", "cameraPosition"],
      "state": ["planets", "selectedPlanet", "rotationSpeed"],
      "dependencies": ["src/utils/three-helpers.ts", "src/data/planets.ts"],
      "is3d": true,
      "isGame": false,
      "estimatedComplexity": "high"
    },
    {
      "name": "GameScene",
      "path": "src/scenes/GameScene.ts",
      "purpose": "Phaser 3 game scene with physics, sprites, and input handling",
      "props": [],
      "state": ["score", "lives", "level", "entities"],
      "dependencies": ["src/config/game-config.ts"],
      "is3d": false,
      "isGame": true,
      "estimatedComplexity": "high"
    }
  ],
  "dataModels": [
    {
      "name": "User",
      "fields": [
        {"name": "id", "type": "int", "constraints": "primary key autoincrement"},
        {"name": "email", "type": "string", "constraints": "unique not null"},
        {"name": "password_hash", "type": "string", "constraints": "not null"},
        {"name": "display_name", "type": "string", "constraints": "not null"},
        {"name": "avatar_url", "type": "string", "constraints": "nullable"},
        {"name": "role", "type": "string", "constraints": "default 'user'"},
        {"name": "created_at", "type": "datetime", "constraints": "auto"},
        {"name": "last_login", "type": "datetime", "constraints": "nullable"}
      ],
      "relationships": [
        {"type": "has_many", "model": "Score", "foreign_key": "user_id"}
      ],
      "storageType": "sqlite"
    },
    {
      "name": "Score",
      "fields": [
        {"name": "id", "type": "int", "constraints": "primary key autoincrement"},
        {"name": "user_id", "type": "int", "constraints": "foreign key not null"},
        {"name": "value", "type": "int", "constraints": "not null"},
        {"name": "level", "type": "string", "constraints": "not null"},
        {"name": "achieved_at", "type": "datetime", "constraints": "auto"}
      ],
      "relationships": [],
      "storageType": "sqlite"
    }
  ],
  "routes": [
    {"path": "/api/auth/register", "method": "POST", "purpose": "User registration", "authRequired": false, "responseType": "json"},
    {"path": "/api/auth/login", "method": "POST", "purpose": "User login", "authRequired": false, "responseType": "json"},
    {"path": "/api/auth/refresh", "method": "POST", "purpose": "Token refresh", "authRequired": true, "responseType": "json"},
    {"path": "/api/auth/me", "method": "GET", "purpose": "Get current user", "authRequired": true, "responseType": "json"},
    {"path": "/api/scores", "method": "GET", "purpose": "List high scores", "authRequired": false, "responseType": "json"},
    {"path": "/api/scores", "method": "POST", "purpose": "Submit score", "authRequired": true, "responseType": "json"}
  ],
  "authStrategy": "JWT with access (30min) + refresh (7d) tokens, bcrypt password hashing",
  "databaseType": "sqlite",
  "fileDependencyOrder": [
    "package.json",
    "tsconfig.json",
    "vite.config.ts",
    "src/vite-env.d.ts",
    "src/types/index.ts",
    "src/utils/three-helpers.ts",
    "src/utils/db.ts",
    "src/utils/auth.ts",
    "src/models/User.ts",
    "src/models/Score.ts",
    "src/data/planets.ts",
    "src/config/game-config.ts",
    "src/components/Scene.tsx",
    "src/scenes/GameScene.ts",
    "src/App.tsx",
    "src/main.tsx",
    "index.html"
  ],
  "warnings": [
    "Consider adding offline support via IndexedDB",
    "WebGL context loss handling needed for 3D components",
    "Game audio may need Howler.js for cross-browser support"
  ],
  "has3d": true,
  "isGame": false,
  "additionalContext": {}
}
```

## ABSOLUTE RULES:
- BE EXHAUSTIVE: Every single file must be listed. No omissions.
- DEPENDENCY ORDER: Topologically sorted — dependencies first, dependents after.
- REALISTIC TECH STACK: Suggest modern, battle-tested libraries. No deprecated packages.
- 3D/GAME: If requested, include render loop, physics, input handling, and asset loading.
- DATABASE: Include ALL models with complete field definitions and relationships.
- AUTH: Include ALL endpoints, middleware, token strategy, and password hashing.
- TESTING: Include test file paths in the dependency order.
- INFRASTRUCTURE: Dockerfile, docker-compose.yml, .env.example, CI/CD config.
- NEVER skip: package.json, tsconfig, vite.config, README, .gitignore, env files.
"""


# ── Architect Agent ───────────────────────────────────────────────────────


class ArchitectAgent:
    """Agent that designs the full system architecture from a high-level prompt.

    Produces an ArchitectureDesign document consumed by the PlannerAgent.
    """

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

    async def design(self, prompt: str) -> ArchitectureDesign:
        """Analyze a project prompt and produce a full architecture design."""
        _logger.info("ArchitectAgent: designing architecture for: %s", prompt[:80])
        start = time.time()

        system_prompt = ARCHITECT_SYSTEM_PROMPT
        user_prompt = (
            f"Design a complete architecture for this project:\n\n"
            f"{prompt}\n\n"
            f"Output ONLY the JSON architecture document inside a ```json fenced code block."
        )

        response = await self._llm.send(system_prompt, user_prompt)
        design = self._parse_design(response, prompt)

        elapsed = time.time() - start
        _logger.info(
            "ArchitectAgent: design complete — %d components, %d models, %d routes (%.1fs)",
            len(design.components),
            len(design.data_models),
            len(design.routes),
            elapsed,
        )
        return design

    def _parse_design(self, response: str, prompt: str) -> ArchitectureDesign:
        """Parse the LLM response into an ArchitectureDesign."""
        # Extract JSON from code block
        json_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL
        )
        json_str = json_match.group(1) if json_match else response

        # Fallback: find top-level JSON object
        if not json_match:
            obj_match = re.search(r"\{[^{}]*\"projectName\"[^{}]*\}", response, re.DOTALL)
            if obj_match:
                json_str = obj_match.group()

        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Failed to parse architecture JSON: {e}\n"
                f"Response snippet: {response[:500]}"
            )

        # Parse components
        components = [
            ComponentSpec(
                name=c.get("name", ""),
                path=c.get("path", ""),
                purpose=c.get("purpose", ""),
                props=c.get("props", []),
                state=c.get("state", []),
                dependencies=c.get("dependencies", []),
                is_3d=c.get("is3d", False),
                is_game=c.get("isGame", False),
                estimated_complexity=c.get("estimatedComplexity", "medium"),
            )
            for c in data.get("components", [])
        ]

        # Parse data models
        data_models = [
            DataModelSpec(
                name=m.get("name", ""),
                fields=m.get("fields", []),
                relationships=m.get("relationships", []),
                storage_type=m.get("storageType", "memory"),
            )
            for m in data.get("dataModels", [])
        ]

        # Parse routes
        routes = [
            RouteSpec(
                path=r.get("path", ""),
                method=r.get("method", "GET"),
                purpose=r.get("purpose", ""),
                auth_required=r.get("authRequired", False),
                response_type=r.get("responseType", "json"),
            )
            for r in data.get("routes", [])
        ]

        return ArchitectureDesign(
            project_name=data.get("projectName", "project"),
            project_type=data.get("projectType", "web"),
            summary=data.get("summary", prompt[:200]),
            tech_stack=data.get("techStack", {}),
            components=components,
            data_models=data_models,
            routes=routes,
            auth_strategy=data.get("authStrategy", "none"),
            database_type=data.get("databaseType", "none"),
            file_dependency_order=data.get("fileDependencyOrder", []),
            warnings=data.get("warnings", []),
            has_3d=data.get("has3d", False),
            has_game=data.get("isGame", False),
            additional_context=data.get("additionalContext", {}),
        )

    async def close(self) -> None:
        await self._llm.close()
