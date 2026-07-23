"""
Writer Agent — generates production-grade code files from implementation plans.

The Writer takes an ImplementationPlan (from PlannerAgent) and the architecture
design (from ArchitectAgent) and generates complete, production-grade code for
each file in the plan. It understands:
  - Exact file dependencies and can reference symbols from generated files
  - Design patterns specified in the plan
  - Risk mitigation strategies
  - Testing approach

Each file is generated with full context awareness, ensuring:
  - Correct import paths
  - Consistent type definitions
  - Proper error handling
  - GPU/memory lifecycle management (for 3D)
  - Security best practices (for auth)
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from wren.app_builder.agents.architect_agent import ArchitectureDesign
from wren.app_builder.agents.planner_agent import ImplementationPlan, FilePlan
from wren.app_builder.llm_client import LLMClient

_logger = logging.getLogger(__name__)


# ── Data models ───────────────────────────────────────────────────────────


@dataclass
class GeneratedFileResult:
    """Result of generating a single file."""

    path: str
    content: str
    success: bool = True
    error: str = ""
    from_template: bool = False
    tokens_used: int = 0


@dataclass
class GenerationSession:
    """Tracks state across multiple file generations."""

    project_name: str
    output_dir: Path
    files: list[GeneratedFileResult] = field(default_factory=list)

    def get_symbols(self) -> dict[str, str]:
        """Extract exports/symbols from generated files for import resolution."""
        symbols: dict[str, str] = {}
        for f in self.files:
            if not f.success:
                continue
            # Extract exports: export function/class/const/interface
            for match in re.finditer(
                r"(?:export\s+(?:default\s+)?(?:function|class|const|let|var|interface|type|enum)\s+(\w+))",
                f.content,
            ):
                symbols[match.group(1)] = f.path
            # Extract Python exports
            for match in re.finditer(
                r"^(?:async\s+)?def\s+(\w+)\s*\(|^class\s+(\w+)\s*[:\(]",
                f.content,
                re.MULTILINE,
            ):
                name = match.group(1) or match.group(2)
                symbols[name] = f.path
        return symbols

    def get_recent_context(self, max_files: int = 5) -> str:
        """Build context string from recently generated files."""
        snippets: list[str] = []
        for f in self.files[-max_files:]:
            if f.success and f.content.strip():
                lines = f.content.split("\n")
                snippet = "\n".join(lines[:40])
                if len(lines) > 40:
                    snippet += f"\n// ... ({len(lines) - 40} more lines)"
                snippets.append(f"--- {f.path} ---\n{snippet}")
        return "\n\n".join(snippets)


# ── System Prompt Parts ───────────────────────────────────────────────────

WRITER_BASE_PROMPT = """\
# WREN WRITER: ELITE CODE GENERATION ENGINE

You are Wren Writer — an elite, full-spectrum software engineer that produces 
COMPLETE, production-grade, zero-placeholder code. You NEVER output:
  - "// TODO"
  - "..."
  - "// rest of implementation"
  - "// add your code here"
  - Stubs or skeletons

## CORE DIRECTIVES:
1. Every function body MUST be fully implemented with proper logic, error handling, and edge cases
2. Every import MUST be resolved — no missing dependencies
3. TypeScript: use strict types, no `any` unless absolutely necessary
4. Python: use type hints, proper docstrings, follow PEP 8
5. 3D/WebGL: include proper dispose() cleanup, context loss handling
6. Security: validate inputs, escape outputs, use parameterized queries
7. Error handling: use try/catch with meaningful error messages
8. Performance: avoid unnecessary re-renders, use memo/callbacks appropriately
9. Accessibility: include ARIA labels, keyboard navigation, focus management
10. Testing: include test file alongside implementation when requested
"""

WRITER_3D_PROMPT = """\
## 3D/WEBGL ADDITIONAL DIRECTIVES:
1. Include WebGL context loss handler with recovery
2. Dispose ALL GPU resources on unmount: geometry.dispose(), material.dispose(), texture.dispose()
3. Use requestAnimationFrame with proper cleanup (cancel on unmount)
4. Handle edge cases: window resize, tab visibility change, device pixel ratio
5. Use React.memo for 3D scene components to prevent unnecessary re-renders
6. Include LoadingManager or Suspense fallback for asset loading
7. Add performance monitoring (Stats panel in dev mode)
8. Use InstancedMesh for repeated geometry with same material
"""

WRITER_DB_PROMPT = """\
## DATABASE ADDITIONAL DIRECTIVES:
1. Use connection pooling with proper configuration
2. Include migration strategy (Alembic for Python, Prisma for TS)
3. Use parameterized queries (prevent SQL injection)
4. Add indexes for frequently queried columns
5. Implement proper session management (get_db dependency)
6. Handle N+1 query problem with eager loading
7. Add transaction support for multi-step operations
"""

WRITER_AUTH_PROMPT = """\
## AUTHENTICATION ADDITIONAL DIRECTIVES:
1. Use bcrypt/argon2 for password hashing (never plaintext)
2. Implement token refresh flow with short-lived access tokens
3. Use httpOnly cookies for refresh tokens when possible
4. Add rate limiting on auth endpoints
5. Implement proper password validation (strength requirements)
6. Add account lockout after failed attempts
7. Include proper CORS configuration
"""

WRITER_API_PROMPT = """\
## API ADDITIONAL DIRECTIVES:
1. Add input validation (Pydantic for Python, Zod for TypeScript)
2. Include proper HTTP status codes
3. Add request logging middleware
4. Implement rate limiting
5. Add response compression
6. Include health check endpoint
7. Add proper error response format
"""


def _get_domain_prompts(design: ArchitectureDesign, file_path: str) -> str:
    """Get domain-specific prompt additions based on the file and project."""
    prompts = []

    # Check project-level flags FIRST (catches all files in the domain)
    # THEN check file path patterns for more specific matching
    if design.has_3d:
        prompts.append("\n## 3D/WEBGL CONTEXT: This project uses 3D rendering.")
        if any(
            ext in file_path for ext in [".glsl", "Scene", "three", "shader", "webgl", "renderer", "canvas", "camera"]
        ):
            prompts.append(WRITER_3D_PROMPT)

    if design.database_type not in ("", "none"):
        prompts.append("\n## DATABASE CONTEXT: This project uses a database.")
        if any(
            ext in file_path for ext in ["db", "model", "migration", "schema", "repository", "entity", "table", "sql", "orm"]
        ):
            prompts.append(WRITER_DB_PROMPT)

    if design.auth_strategy not in ("", "none"):
        prompts.append("\n## AUTH CONTEXT: This project has authentication.")
        if any(
            ext in file_path for ext in ["auth", "jwt", "login", "register", "session", "token", "password", "security", "oauth"]
        ):
            prompts.append(WRITER_AUTH_PROMPT)

    if any(ext in file_path for ext in ["router", "route", "api", "endpoint", "controller", "handler", "middleware", "resource"]):
        prompts.append(WRITER_API_PROMPT)

    return "\n".join(prompts)


_CODE_BLOCK_RE = re.compile(r"```(?:\w+)?\n(.+?)```", re.DOTALL)


def _extract_code_blocks(text: str) -> list[str]:
    """Extract all fenced code blocks from LLM output."""
    blocks = _CODE_BLOCK_RE.findall(text)
    if not blocks:
        return [text.strip()]
    return [b.strip() for b in blocks if b.strip()]


# ── Writer Agent ──────────────────────────────────────────────────────────


class WriterAgent:
    """Agent that generates complete code files from an implementation plan."""

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

    async def generate_all(
        self,
        design: ArchitectureDesign,
        plan: ImplementationPlan,
        output_dir: Path,
        max_corrections: int = 3,
    ) -> GenerationSession:
        """Generate all files in the plan in dependency order."""
        session = GenerationSession(
            project_name=design.project_name,
            output_dir=output_dir,
        )

        file_plans = plan.files
        total = len(file_plans)

        for i, file_plan in enumerate(file_plans):
            _logger.info("WriterAgent: generating %s (%d/%d)", file_plan.path, i + 1, total)

            try:
                content = await self._generate_file(
                    design, plan, file_plan, session, i + 1, total
                )

                # Write to disk
                target = output_dir / file_plan.path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)

                result = GeneratedFileResult(
                    path=file_plan.path,
                    content=content,
                    success=True,
                )
                session.files.append(result)

            except Exception as e:
                _logger.error("WriterAgent: failed to generate %s: %s", file_plan.path, e)
                session.files.append(GeneratedFileResult(
                    path=file_plan.path,
                    content="",
                    success=False,
                    error=str(e),
                ))

                # Try correction
                if max_corrections > 0:
                    for round_num in range(1, max_corrections + 1):
                        try:
                            content = await self._correct_file(
                                design, plan, file_plan, session, str(e), round_num
                            )
                            target = output_dir / file_plan.path
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_text(content)
                            session.files[-1] = GeneratedFileResult(
                                path=file_plan.path,
                                content=content,
                                success=True,
                            )
                            _logger.info("WriterAgent: corrected %s (round %d)", file_plan.path, round_num)
                            break
                        except Exception:
                            continue

        return session

    async def _generate_file(
        self,
        design: ArchitectureDesign,
        plan: ImplementationPlan,
        file_plan: FilePlan,
        session: GenerationSession,
        index: int,
        total: int,
    ) -> str:
        """Generate a single file with full context awareness."""

        # Build the context payload
        arch_snippet = json.dumps(design.to_dict(), indent=2)[:2000]
        previous_files = session.get_recent_context()
        symbols = json.dumps(session.get_symbols(), indent=2)
        domain_prompts = _get_domain_prompts(design, file_plan.path)

        system_prompt = (
            WRITER_BASE_PROMPT
            + domain_prompts
            + f"""

## FILE CONTEXT:
File: {file_plan.path}
Purpose: {file_plan.purpose}
Design Pattern: {file_plan.design_pattern}
Complexity: {file_plan.complexity}
Estimated Lines: {file_plan.estimated_lines}
Key Functions: {file_plan.key_functions}
Dependencies: {file_plan.dependencies}
Risk Factors: {file_plan.risk_factors}
Testing: {file_plan.testing_approach}
Notes: {file_plan.notes}

## PROJECT ARCHITECTURE:
{arch_snippet}

## PREVIOUSLY GENERATED FILES (imports context):
{previous_files}

## AVAILABLE EXPORTS/SYMBOLS (for imports):
{symbols}

## GENERATE 100% COMPLETE CODE.
- Every function body fully implemented
- Every import resolved
- Proper error handling
- Edge cases covered
- Output ONLY inside a single ``` fenced code block
"""
        )

        user_prompt = (
            f"Generate the complete, production-ready file: {file_plan.path}\n\n"
            f"Purpose: {file_plan.purpose}\n\n"
            f"Output 100% complete code inside a ``` block."
        )

        response = await self._llm.send(system_prompt, user_prompt, task_type="coding", role="writer")
        blocks = _extract_code_blocks(response)

        if not blocks:
            raise ValueError("No code blocks found in LLM response")

        content = blocks[0]
        if len(content.strip()) < 10:
            raise ValueError("Generated content is too short (likely empty)")

        return content

    async def _correct_file(
        self,
        design: ArchitectureDesign,
        plan: ImplementationPlan,
        file_plan: FilePlan,
        session: GenerationSession,
        error: str,
        round_num: int,
    ) -> str:
        """Attempt to correct a failed file generation."""
        previous_files = session.get_recent_context()

        system_prompt = (
            WRITER_BASE_PROMPT
            + f"""

## CORRECTION ROUND {round_num}

The previous generation of {file_plan.path} failed with error:
{error}

Fix ALL issues. Output the COMPLETE corrected file — no diffs, no placeholders.
Every function must be fully implemented.
"""
        )

        user_prompt = (
            f"Regenerate the complete file: {file_plan.path}\n\n"
            f"Purpose: {file_plan.purpose}\n\n"
            f"Previous context:\n{previous_files}\n\n"
            f"Output the COMPLETE corrected code inside a ``` block."
        )

        response = await self._llm.send(system_prompt, user_prompt, task_type="coding", role="writer")
        blocks = _extract_code_blocks(response)

        if not blocks or len(blocks[0].strip()) < 10:
            raise ValueError("Correction produced empty content")

        return blocks[0]

    async def close(self) -> None:
        await self._llm.close()
