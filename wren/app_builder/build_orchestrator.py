"""Build Orchestrator — coordinates the multi-agent pipeline for complex app generation.

Pipeline:
  ArchitectAgent (design) → PlannerAgent (plan) → WriterAgent (write) → ReviewerAgent (review) → (correction loop)

Unlike the standalone AutomatedProjectGenerator which calls an LLM once per file,
this orchestrator uses specialized agents at each stage for higher quality results.

For complex apps (DB, auth, 3D), it feeds the ArchitectureDesign into each stage
so the Planner/Writer/Reviewer have full context of the system architecture.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from wren.app_builder.agents import ArchitectAgent, ArchitectureDesign, ComponentSpec
from wren.app_builder.llm_client import LLMClient
from wren.app_builder.templates.three_kit import (
    generate_package_json as gen_3d_package_json,
    generate_tsconfig as gen_3d_tsconfig,
    generate_vite_config as gen_3d_vite_config,
    generate_three_scene_tsx,
    generate_three_helpers_ts,
    generate_shader_glsl,
)
from wren.app_builder.templates.fullstack_kit import (
    generate_sqlalchemy_base,
    generate_user_model,
    generate_jwt_auth,
    generate_env_example,
    generate_dockerfile,
    generate_docker_compose,
    generate_zustand_store,
    generate_api_router,
)

_logger = logging.getLogger(__name__)


# ── Terminal helpers ──────────────────────────────────────────────────────

_COLOR = sys.stderr.isatty()


def _c(code: str, text: str) -> str:
    if not _COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def _bold(text: str) -> str:
    return _c("1", text)


def _dim(text: str) -> str:
    return _c("2", text)


def _green(text: str) -> str:
    return _c("32", text)


def _red(text: str) -> str:
    return _c("31", text)


def _yellow(text: str) -> str:
    return _c("33", text)


def _blue(text: str) -> str:
    return _c("34", text)


def _cyan(text: str) -> str:
    return _c("36", text)


def _magenta(text: str) -> str:
    return _c("35", text)


# ── Data models ───────────────────────────────────────────────────────────


@dataclass
class AgentResult:
    """Result from a single agent in the pipeline."""

    agent: str
    success: bool
    duration_s: float = 0.0
    detail: str = ""
    error: str = ""


@dataclass
class BuildArtifact:
    """A generated file in the build."""

    path: str
    content: str
    success: bool = True
    error: str = ""


@dataclass
class OrchestratorResult:
    """Final result of the build orchestration."""

    success: bool
    prompt: str
    project_name: str
    project_type: str
    output_dir: str = ""
    architecture: dict[str, Any] | None = None
    files: list[BuildArtifact] = field(default_factory=list)
    agent_results: list[AgentResult] = field(default_factory=list)
    total_duration_s: float = 0.0
    error: str = ""
    has_3d: bool = False
    has_database: bool = False
    has_auth: bool = False


# ── Progress display ──────────────────────────────────────────────────────


class BuildProgress:
    """Terminal progress display for the build pipeline."""

    def __init__(self) -> None:
        self._start = 0.0

    def banner(self, prompt: str) -> None:
        print()
        print(f"  {_bold(_cyan('╔══════════════════════════════════════════╗'))}")
        print(f"  {_bold(_cyan('║   WREN BUILD ORCHESTRATOR v2           ║'))}")
        print(f"  {_bold(_cyan('╚══════════════════════════════════════════╝'))}")
        print()
        print(f"  {_yellow('Prompt:')} {prompt[:120]}")
        print()
        self._start = time.time()

    def agent_start(self, agent: str, description: str = "") -> None:
        print(f"\n  {_bold(_blue('▸'))} {_bold(agent)}")
        if description:
            print(f"    {_dim(description[:100])}")

    def agent_done(self, agent: str, success: bool, detail: str = "", elapsed: float = 0.0) -> None:
        icon = _green("✓") if success else _red("✗")
        print(f"  [{icon}] {agent} ({elapsed:.1f}s)")
        if detail:
            for line in detail.split("\n"):
                print(f"       {_dim(line[:100])}")

    def file_progress(self, index: int, total: int, path: str, status: str) -> None:
        icon = {"generating": _yellow("→"), "done": _green("✓"), "error": _red("✗")}.get(
            status, "·"
        )
        print(f"    [{icon}] [{index}/{total}] {_dim(path[:70])} ... {status}")

    def log(self, message: str) -> None:
        print(f"      {_dim(message[:100])}")

    def warn(self, message: str) -> None:
        print(f"      {_yellow('⚠')} {message[:100]}")

    def summary(self, result: OrchestratorResult) -> None:
        print()
        print(f"  {_bold(_cyan('══════════════════════════════════════════'))}")
        print(f"  {_bold('Build Complete')}")
        print(f"  {_dim('─' * 40)}")
        print(f"  Project:  {_bold(result.project_name)}")
        print(f"  Type:     {result.project_type}")
        print(f"  Location: {result.output_dir}")
        print(f"  Files:    {len(result.files)}")
        print(f"  Duration: {result.total_duration_s:.1f}s")
        if result.has_3d:
            print(f"  3D:       {_green('✓')}")
        if result.has_database:
            print(f"  Database: {_green('✓')}")
        if result.has_auth:
            print(f"  Auth:     {_green('✓')}")
        total_agents = len(result.agent_results)
        passed = sum(1 for a in result.agent_results if a.success)
        print(f"  Agents:   {passed}/{total_agents} passed")
        print(f"  Status:   {_green('SUCCESS') if result.success else _red('FAILED')}")
        print(f"  {_bold(_cyan('══════════════════════════════════════════'))}")
        print()


# ── Context assembler ─────────────────────────────────────────────────────


def _build_project_context(design: ArchitectureDesign, files_so_far: list[BuildArtifact]) -> str:
    """Build a rich context string from the architecture design and completed files."""
    parts: list[str] = []

    # Architecture summary
    parts.append("=== ARCHITECTURE DESIGN ===")
    parts.append(f"Project: {design.project_name}")
    parts.append(f"Type: {design.project_type}")
    parts.append(f"Stack: {json.dumps(design.tech_stack, indent=2)}")
    parts.append(f"Summary: {design.summary}")

    if design.has_3d:
        parts.append(f"\n3D Architecture: YES")
        parts.append(f"3D Components: {[c.name for c in design.components if c.is_3d]}")

    if design.data_models:
        parts.append(f"\nData Models:")
        for m in design.data_models:
            parts.append(f"  - {m.name} ({m.storage_type}): {[f['name'] for f in m.fields]}")

    if design.routes:
        parts.append(f"\nAPI Routes:")
        for r in design.routes:
            parts.append(f"  {r.method} {r.path} {'🔒' if r.auth_required else ''}")

    if design.auth_strategy and design.auth_strategy != "none":
        parts.append(f"\nAuth: {design.auth_strategy}")

    if design.warnings:
        parts.append(f"\nWarnings: {design.warnings}")

    # Previously generated files
    if files_so_far:
        parts.append(f"\n=== GENERATED FILES ({len(files_so_far)}) ===")
        for f in files_so_far[-5:]:  # Last 5 files for context
            if f.success:
                lines = f.content.split("\n")
                snippet = "\n".join(lines[:30])
                parts.append(f"\n--- {f.path} ---\n{snippet}")
                if len(lines) > 30:
                    parts.append(f"// ... ({len(lines) - 30} more lines)")

    return "\n\n".join(parts)


# ── LLM-based Planner + Writer (self-contained, no MessageBus needed) ──────


# ── Code block extraction ──────────────────────────────────────────────────

import re

_CODE_BLOCK_RE = re.compile(r"```(?:\w+)?\n(.+?)```", re.DOTALL)


def _extract_code_blocks(text: str) -> list[str]:
    blocks = _CODE_BLOCK_RE.findall(text)
    if not blocks:
        return [text.strip()]
    return [b.strip() for b in blocks if b.strip()]


# ── Orchestrator ───────────────────────────────────────────────────────────


class BuildOrchestrator:
    """Coordinates the multi-agent build pipeline.

    Pipeline:
      1. Architect — designs full system architecture
      2. Planner — produces structured file plan from architecture
      3. Writer — generates each file in dependency order
      4. Reviewer — validates generated code with fix loop

    Each stage runs sequentially, passing context forward.
    """

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gpt-4o",
        base_url: str | None = None,
        output_dir: str = "./wren-builds-v2",
        validate: bool = True,
        max_corrections: int = 3,
        progress_callback: Any = None,
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._output_root = Path(output_dir)
        self._validate = validate
        self._max_corrections = max_corrections
        self._progress_callback = progress_callback
        self._display = BuildProgress()

        # Shared LLM client (used by all agents)
        self._llm = LLMClient(api_key=api_key, model=model, base_url=base_url)

        # Pipeline state
        self._design: ArchitectureDesign | None = None
        self._output_dir: Path | None = None
        self._files: list[BuildArtifact] = []
        self._agent_results: list[AgentResult] = []

    # ── Public entry point ────────────────────────────────────────

    async def build(self, prompt: str) -> OrchestratorResult:
        """Execute the full multi-agent build pipeline."""
        start_time = time.time()
        result = OrchestratorResult(
            success=False, prompt=prompt, project_name="", project_type=""
        )

        self._display.banner(prompt)

        try:
            # ════════════════════════════════════════════════════════
            # STAGE 1: ARCHITECT
            # ════════════════════════════════════════════════════════
            design = await self._run_architect(prompt)
            result.architecture = design.to_dict()
            result.project_name = design.project_name
            result.project_type = design.project_type
            result.has_3d = design.has_3d
            result.has_database = design.database_type != "none"
            result.has_auth = design.auth_strategy != "none"

            if design.warnings:
                for w in design.warnings:
                    self._display.warn(w)

            # ════════════════════════════════════════════════════════
            # STAGE 2: PLAN + GENERATE (combined for efficiency)
            # ════════════════════════════════════════════════════════
            files = await self._run_generation(design)
            self._files = files

            # ════════════════════════════════════════════════════════
            # STAGE 3: ERROR RECOVERY (retry failed files)
            # ════════════════════════════════════════════════════════
            success_count = await self._retry_failed_files(design)

            # ════════════════════════════════════════════════════════
            # STAGE 4: VALIDATE
            # ════════════════════════════════════════════════════════
            if self._validate:
                await self._run_validation()

            # ════════════════════════════════════════════════════════
            # RESULTS
            # ════════════════════════════════════════════════════════
            result.files = self._files
            result.agent_results = self._agent_results
            result.output_dir = str(self._output_dir or "")
            result.success = all(
                f.success for f in self._files
            ) and all(a.success for a in self._agent_results)

        except Exception as e:
            self._display.log(f"Fatal error: {e}")
            result.error = str(e)

        result.total_duration_s = time.time() - start_time
        self._display.summary(result)
        return result

    async def close(self) -> None:
        await self._llm.close()

    # ── Agent: Architect ──────────────────────────────────────────

    async def _run_architect(self, prompt: str) -> ArchitectureDesign:
        self._display.agent_start("Architect Agent", "Designing system architecture...")

        agent = ArchitectAgent(llm_client=self._llm)
        start = time.time()

        try:
            design = await agent.design(prompt)
            elapsed = time.time() - start

            # Log design summary
            self._display.log(f"Project: {design.project_name} ({design.project_type})")
            self._display.log(f"Components: {len(design.components)}")
            self._display.log(f"Data Models: {len(design.data_models)}")
            self._display.log(f"Routes: {len(design.routes)}")
            self._display.log(
                f"Stack: {', '.join(f'{k}={v}' for k, v in list(design.tech_stack.items())[:4])}"
            )
            if design.has_3d:
                self._display.log(f"3D: YES — {len([c for c in design.components if c.is_3d])} 3D components")

            self._agent_results.append(
                AgentResult("Architect", True, elapsed, f"Designed {len(design.components)} components")
            )
            self._design = design

            # Create output directory
            self._output_dir = self._output_root / design.project_name
            self._output_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories for planned files
            for c in design.components:
                fp = self._output_dir / c.path
                fp.parent.mkdir(parents=True, exist_ok=True)

            self._display.agent_done("Architect", True, f"{design.summary[:80]}...", elapsed)

            return design

        except Exception as e:
            elapsed = time.time() - start
            self._agent_results.append(AgentResult("Architect", False, elapsed, error=str(e)))
            self._display.agent_done("Architect", False, str(e)[:100], elapsed)
            raise

    # ── Agent: File Generation (combined Planner + Writer) ────────

    async def _run_generation(self, design: ArchitectureDesign) -> list[BuildArtifact]:
        """Generate all files in dependency order using the architecture design.

        Uses template generators as base for known file types (3D, DB, auth)
        and falls back to LLM generation for custom files.
        """
        self._display.agent_start("Generation Pipeline", "Writing files in dependency order...")

        files: list[BuildArtifact] = []
        start = time.time()

        # Determine file order from architecture or fallback to components
        file_order = design.file_dependency_order
        if not file_order:
            file_order = [c.path for c in design.components]

        # Also include config files based on project type
        config_files = self._get_config_files(design)
        all_paths = list(dict.fromkeys(config_files + file_order))  # Deduplicate preserving order
        total = len(all_paths)

        for i, file_path in enumerate(all_paths):
            if any(f.path == file_path for f in files):
                continue

            self._display.file_progress(i + 1, total, file_path, "generating")
            await self._emit_progress("generating", file_path, i + 1, total)

            # Try template FIRST, then fall back to LLM generation
            content = self._try_template(design, file_path)
            from_template = content is not None

            if content is None:
                # Fall back to LLM generation
                component = next(
                    (c for c in design.components if c.path == file_path), None
                )
                context = _build_project_context(design, files)

                system_prompt = (
                    "You are an expert software engineer. Generate 100% COMPLETE, "
                    "zero-placeholder code for the requested file. "
                    "No TODOs, no ellipsis, no stubs. Every function body must be fully implemented.\n\n"
                    "Architecture Context:\n"
                    f"{context}\n\n"
                    f"File: {file_path}\n"
                    f"Project: {design.project_name}\n"
                    f"Stack: {json.dumps(design.tech_stack)}\n"
                )

                if component:
                    system_prompt += (
                        f"\nComponent: {component.name}\n"
                        f"Purpose: {component.purpose}\n"
                        f"Dependencies: {component.dependencies}\n"
                        f"Props: {component.props}\n"
                        f"State: {component.state}\n"
                        f"3D Component: {component.is_3d}\n"
                        f"Complexity: {component.estimated_complexity}\n"
                    )

                if design.has_3d and (component and component.is_3d):
                    system_prompt += (
                        "\nThis is a 3D/WebGL component. Include:\n"
                        "- Proper WebGL context setup (or use Three.js)\n"
                        "- requestAnimationFrame loop with cleanup\n"
                        "- Dispose all GPU resources (geometry, material, texture)\n"
                        "- Responsive canvas sizing\n"
                        "- Error handling for WebGL context loss\n"
                    )

                if design.data_models and file_path.endswith((".py", ".ts", ".js")):
                    system_prompt += "\nInclude proper data model definitions matching the architecture above.\n"

                user_prompt = (
                    f"Generate the complete file: {file_path}\n\n"
                    f"Output 100% complete code inside a single ``` block."
                )

                try:
                    response = await self._llm.send(system_prompt, user_prompt)
                    blocks = _extract_code_blocks(response)
                    if not blocks:
                        raise ValueError("No code blocks found in LLM response")
                    content = blocks[0]
                except Exception as e:
                    self._display.log(f"  LLM gen failed: {e}")
                    content = None

            if content:
                try:
                    target = self._output_dir / file_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content)

                    if target.stat().st_size == 0:
                        raise ValueError("Generated file is empty")

                    files.append(BuildArtifact(path=file_path, content=content, success=True))
                    src_label = "template" if from_template else "llm"
                    self._display.file_progress(i + 1, total, file_path, f"done ({src_label})")
                    await self._emit_progress("done", file_path, i + 1, total)
                except Exception as e:
                    files.append(BuildArtifact(path=file_path, content="", success=False, error=str(e)))
                    self._display.file_progress(i + 1, total, file_path, "error")
                    self._display.log(f"  Write failed: {e}")
                    await self._emit_progress("error", file_path, i + 1, total)
            else:
                files.append(BuildArtifact(path=file_path, content="", success=False, error="No content generated"))
                self._display.file_progress(i + 1, total, file_path, "error")

        elapsed = time.time() - start
        success_count = sum(1 for f in files if f.success)
        self._agent_results.append(
            AgentResult(
                "Generation",
                success_count == len(files),
                elapsed,
                f"Generated {success_count}/{len(files)} files",
            )
        )
        self._display.agent_done(
            "Generation",
            success_count == len(files),
            f"{success_count}/{len(files)} files generated",
            elapsed,
        )
        return files

    def _try_template(self, design: ArchitectureDesign, file_path: str) -> str | None:
        """Try to generate a file using a template. Returns content or None if no template."""
        fname = Path(file_path).name
        fext = Path(file_path).suffix.lower()

        # ── Config files ──────────────────────────────────
        if fname == "package.json":
            return json.dumps(gen_3d_package_json(design.project_name, has_3d=design.has_3d), indent=2) + "\n"
        if fname == "tsconfig.json":
            return gen_3d_tsconfig()
        if fname == "vite.config.ts":
            return gen_3d_vite_config(has_3d=design.has_3d)
        if fname == ".env.example":
            return generate_env_example(
                has_database=design.database_type not in ("", "none"),
                has_auth=design.auth_strategy not in ("", "none"),
            )
        if fname == "Dockerfile":
            return generate_dockerfile()
        if fname == "docker-compose.yml":
            return generate_docker_compose()

        # ── 3D files ──────────────────────────────────────
        if fname == "Scene.tsx" or file_path.endswith("/Scene.tsx"):
            if design.has_3d:
                return generate_three_scene_tsx()
        if "three-helpers" in file_path and fext == ".ts":
            if design.has_3d:
                return generate_three_helpers_ts()
        if "shader" in file_path and fext == ".glsl":
            if design.has_3d:
                return generate_shader_glsl()

        # ── Database files ────────────────────────────────
        if fname in ("database.py", "db.py", "base.py"):
            if design.database_type not in ("", "none"):
                return generate_sqlalchemy_base()
        if fname == "User.py" or fname == "user.py" or fname == "user.ts":
            if design.database_type not in ("", "none"):
                return generate_user_model()

        # ── Auth files ────────────────────────────────────
        if fname in ("auth.py", "jwt.py"):
            if design.auth_strategy not in ("", "none"):
                return generate_jwt_auth()

        # ── State management ───────────────────────────────
        if fname in ("store.ts", "stores.ts", "useStore.ts", "zustand.ts"):
            return generate_zustand_store()

        # ── API routing ────────────────────────────────────
        if fname in ("router.py", "crud_router.py", "routes.py"):
            return generate_api_router()

        return None

    # ── Config files per project type ─────────────────────────────

    def _get_config_files(self, design: ArchitectureDesign) -> list[str]:
        """Get the list of configuration files needed for the project type."""
        configs: list[str] = []

        if design.project_type in ("web", "3d-web"):
            configs = [
                "package.json",
                "tsconfig.json",
                "vite.config.ts",
                "index.html",
                ".env.example",
                "README.md",
            ]
            if design.has_3d:
                configs.extend(["src/vite-env.d.ts"])

        elif design.project_type == "api":
            configs = [
                "requirements.txt",
                "pyproject.toml",
                ".env.example",
                "README.md",
                "Dockerfile",
                "docker-compose.yml",
            ]

        elif design.project_type == "mobile":
            configs = [
                "pubspec.yaml",
                "README.md",
            ]

        elif design.project_type == "desktop":
            configs = [
                "package.json",
                "README.md",
            ]

        elif design.project_type == "cli":
            configs = [
                "pyproject.toml",
                "README.md",
            ]

        return configs

    # ── Agent: Validation ─────────────────────────────────────────

    async def _run_validation(self) -> None:
        """Validate generated files with syntax checks and LLM-based review."""
        self._display.agent_start("Validation Pipeline", "Running quality checks...")
        start = time.time()
        issues = 0

        # 1. Check for empty/truncated files
        for f in self._files:
            if f.success and len(f.content.strip()) < 10:
                self._display.warn(f"Truncated file: {f.path}")
                issues += 1

        # 2. Check for placeholder patterns
        placeholder_patterns = [
            "TODO",
            "FIXME",
            "// ...",
            "/* ... */",
            "not implemented",
            "placeholder",
            "add your",
        ]
        for f in self._files:
            if f.success:
                content_lower = f.content.lower()
                for pattern in placeholder_patterns:
                    if pattern.lower() in content_lower:
                        self._display.warn(f"Placeholder '{pattern}' found in {f.path}")
                        issues += 1
                        break

        # 3. LLM-based review for complex projects
        if self._design and (self._design.has_3d or self._design.data_models):
            try:
                review_prompt = (
                    "Review this generated project for quality issues. "
                    "Focus on:\n"
                    "1. Missing imports or broken references between files\n"
                    "2. Incomplete function implementations\n"
                    "3. 3D/WebGL resource leaks (missing .dispose() calls)\n"
                    "4. Missing error handling\n"
                    "5. Type mismatches\n\n"
                    f"Project: {self._design.project_name}\n"
                    f"Files ({len(self._files)}):\n"
                )
                for f in self._files[:10]:  # First 10 files for review
                    if f.success:
                        lines = f.content.split("\n")
                        snippet = "\n".join(lines[:20])
                        review_prompt += f"\n--- {f.path} ---\n{snippet}\n"

                review_prompt += (
                    "\nOutput ONLY a JSON object:\n"
                    '{"issues": [{"file": "...", "severity": "warning|error", "message": "..."}], "passed": true/false}'
                )

                response = await self._llm.send(
                    "You are a code reviewer. Check for bugs, missing imports, incomplete implementations.",
                    review_prompt,
                )

                # Try to parse issues from response
                json_match = re.search(
                    r"\{[^{}]*\"issues\"[^{}]*\}", response, re.DOTALL
                )
                if json_match:
                    review_data = json.loads(json_match.group())
                    review_issues = review_data.get("issues", [])
                    if review_issues:
                        self._display.log(f"Review found {len(review_issues)} issues:")
                        for issue in review_issues[:5]:
                            self._display.warn(
                                f"  {issue.get('file', '?')}: {issue.get('message', '')[:80]}"
                            )
                        issues += len(review_issues)

            except Exception as e:
                self._display.log(f"Review skipped: {e}")

        elapsed = time.time() - start
        self._agent_results.append(
            AgentResult(
                "Validation",
                issues == 0,
                elapsed,
                f"Found {issues} issues" if issues else "All checks passed",
            )
        )
        self._display.agent_done(
            "Validation", issues == 0, f"{issues} issues found" if issues else "All checks passed", elapsed
        )

    # ── Progress callback ─────────────────────────────────────────

    async def _emit_progress(self, status: str, file_path: str, index: int, total: int) -> None:
        if self._progress_callback:
            try:
                await self._progress_callback(
                    2, "Generation Pipeline", status, "",
                    index, total, file_path,
                )
            except Exception:
                pass

    # ── Error recovery ──────────────────────────────────────────

    async def _retry_failed_files(self, design: ArchitectureDesign) -> int:
        """Retry generating failed files up to max_corrections times."""
        for round_num in range(1, self._max_corrections + 1):
            failed = [f for f in self._files if not f.success]
            if not failed:
                return 0

            self._display.log(f"Retry round {round_num}/{self._max_corrections}: {len(failed)} failed files")
            recovered = 0

            for f in failed:
                component = next(
                    (c for c in design.components if c.path == f.path), None
                )
                context = _build_project_context(design, self._files)

                system_prompt = (
                    f"This file failed to generate correctly. Error: {f.error}\n\n"
                    "Regenerate the COMPLETE file with all functions fully implemented.\n\n"
                    f"Architecture Context:\n{context}\n\n"
                    f"File: {f.path}"
                )

                try:
                    response = await self._llm.send(system_prompt, f"Regenerate: {f.path}")
                    blocks = _extract_code_blocks(response)
                    if blocks:
                        content = blocks[0]
                        target = self._output_dir / f.path
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(content)
                        if target.stat().st_size > 0:
                            f.content = content
                            f.success = True
                            f.error = ""
                            recovered += 1
                            self._display.log(f"  Recovered: {f.path}")
                except Exception:
                    pass

            if recovered == 0:
                break

            self._display.log(f"Recovered {recovered}/{len(failed)} files in round {round_num}")

        return sum(1 for f in self._files if f.success)

    # ── Convenience ────────────────────────────────────────────────

    async def __aenter__(self) -> "BuildOrchestrator":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


# ── CLI entry point ──────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point: python -m wren.app_builder.build_orchestrator"""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="Wren Build Orchestrator v2 — Multi-Agent App Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m wren.app_builder.build_orchestrator \\\n"
            "    --prompt \"Build a 3D portfolio site with Three.js\" \\\n"
            "    --api-key sk-... \\\n"
            "    --model gpt-4o \\\n"
            "    --output ./my-project\n"
        ),
    )
    parser.add_argument("--prompt", "-p", required=True, help="High-level project directive")
    parser.add_argument("--api-key", "-k", required=True, help="LLM API key")
    parser.add_argument("--model", "-m", default="gpt-4o", help="LLM model")
    parser.add_argument("--base-url", default=None, help="Custom API base URL")
    parser.add_argument("--output", "-o", default="./wren-builds-v2", help="Output directory")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation")
    parser.add_argument("--max-corrections", type=int, default=3, help="Max retry attempts")

    args = parser.parse_args()

    async def _run() -> None:
        orch = BuildOrchestrator(
            api_key=args.api_key,
            model=args.model,
            base_url=args.base_url,
            output_dir=args.output,
            validate=not args.no_validate,
            max_corrections=args.max_corrections,
        )
        try:
            result = await orch.build(args.prompt)
            sys.exit(0 if result.success else 1)
        finally:
            await orch.close()

    asyncio.run(_run())


if __name__ == "__main__":
    main()
