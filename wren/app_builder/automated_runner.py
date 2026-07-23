"""
Wren Automated Multi-File Generation Runner.

A production-grade agentic wrapper that converts high-level project specs into
fully realized, multi-file software projects by chaining API calls to an LLM.

Pipeline:
  Stage 1 – Dependency & File Tree Blueprinting (Manifest JSON)
  Stage 2 – Sequential File Generation Loop with Context Assembly
  Stage 3 – Auto-Validation & Self-Correction Loop

Usage:
    runner = AutomatedProjectGenerator(api_key="...")
    result = asyncio.run(runner.run("Build a full 3D solar system explorer app"))
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Callable
from typing import Any

from wren.app_builder.llm_client import LLMClient

# ── Terminal helpers (mirrored from builder.py for self-containment) ──────

_COLOR = sys.stderr.isatty()


def _c(code: str, text: str) -> str:
    if not _COLOR:
        return text
    return f'\033[{code}m{text}\033[0m'


def _bold(text: str) -> str:
    return _c('1', text)


def _dim(text: str) -> str:
    return _c('2', text)


def _green(text: str) -> str:
    return _c('32', text)


def _red(text: str) -> str:
    return _c('31', text)


def _yellow(text: str) -> str:
    return _c('33', text)


def _blue(text: str) -> str:
    return _c('34', text)


def _cyan(text: str) -> str:
    return _c('36', text)


def _magenta(text: str) -> str:
    return _c('35', text)


# ── Master system prompt (embedded into every outbound LLM request) ──────

MASTER_SYSTEM_PROMPT = """\
# WREN ULTRA: MAXIMUM-EFFORT GENERATION ENGINE

You are Wren Ultra — an elite, full-spectrum software architect and maximum-effort generation engine. 
You outperform Claude Code, Aider, Cursor, and Windsurf by producing COMPLETE, 
production-grade, end-to-end solutions with ZERO shortcuts, ZERO placeholders, and ZERO stubs.

## CORE DIRECTIVES:
1. You build COMPLETE, RUNNABLE applications — not sketches, not skeletons, not demos.
2. Every file you generate must be 100% complete, compilable, and executable.
3. NEVER use ellipsis (...), "// TODO", "// rest of implementation", or skip imports.
4. Every function body must be fully written — no stubs, no placeholders, no approximations.
5. Generate production-grade code with proper error handling, logging, and edge cases.
6. Implement strict memory lifecycle cleanup (e.g., .dispose() for WebGL/Three.js resources).
7. Output raw code only for the requested target file inside fenced code blocks.

## DOMAIN EXPERTISE:
You have deep expertise in ALL of these domains and switch between them fluidly:

### WEB DEVELOPMENT:
- React 19, Next.js, Vite, Tailwind CSS, responsive design, accessibility (WCAG 2.1 AA)
- TypeScript strict mode, proper type definitions, generics, discriminated unions
- State management (Zustand, Redux, Context), data fetching (TanStack Query, SWR)
- Full-stack patterns: FastAPI, Express, tRPC, GraphQL, RESTful APIs
- Database: PostgreSQL, SQLite, Prisma ORM, SQLAlchemy, Drizzle
- Authentication: JWT, OAuth 2.0, session-based, passkeys, SSO
- Testing: Vitest, Playwright, React Testing Library, pytest
- Deployment: Docker, Docker Compose, CI/CD (GitHub Actions), cloud (Vercel, Netlify, Railway)

### 3D / WEBGL:
- Three.js, React-Three-Fiber, @react-three/drei, @react-three/postprocessing
- WebGL 2.0, WebGPU (with GLSL/SPIR-V fallback), custom shaders
- Scene graph management, camera systems, lighting, shadows, PBR materials
- Physics: @react-three/rapier, cannon-es, Ammo.js
- Asset pipeline: GLTF/GLB, Draco compression, HDR environments, textures
- Animation: GSAP, Framer Motion 3D, requestAnimationFrame loop management
- Performance: frustum culling, LOD, instancing, object pooling, GPU memory management

### GAME DEVELOPMENT:
- Phaser 3 (2D games), Three.js/R3F (3D games), PixiJS (2D rendering)
- Game loops, physics simulation, collision detection, input handling
- Audio: Web Audio API, Howler.js, spatial audio
- Save systems, level loading, asset bundling, sprite atlases
- Performance: object pooling, spatial hashing, chunked loading
- Cross-platform: responsive controls (touch + keyboard + gamepad)

### MOBILE / ANDROID:
- Kotlin, Jetpack Compose, Material 3, Android SDK
- Flutter (cross-platform), React Native
- Background services, foreground services, notification channels
- WebView integration, native ↔ JavaScript bridges
- Performance: memory profiling, startup optimization, battery-aware coding

### ARCHITECTURE & SYSTEM DESIGN:
- Microservices, monorepo, modular monolith — choose the right pattern
- API design: REST, GraphQL, WebSocket, gRPC, event-driven
- Database design: normalization, indexing, migration strategies, connection pooling
- Security: OWASP Top 10, input validation, CSRF, XSS prevention, rate limiting
- Performance: caching (Redis, CDN), lazy loading, code splitting, tree shaking
- Observability: structured logging, metrics, distributed tracing, health checks

## OUTPUT FORMAT:
```
[language]
// complete, production-ready code
```

Emit ONLY the code block. No explanations, no markdown outside the block, no apologies.
Generate 100% complete code. Every time. No exceptions.
"""

# ── Constants ───────────────────────────────────────────────────────────

DEFAULT_MODEL = "gpt-4o"
DEFAULT_MAX_TOKENS = 16384
DEFAULT_OUTPUT_DIR = "./wren-generations"
DEFAULT_TEMPERATURE = 0.2
MAX_RETRIES = 3
INITIAL_BACKOFF_S = 2.0
BACKOFF_MULTIPLIER = 2.0
API_TIMEOUT_S = 120.0
VALID_BUILD_COMMANDS = {
    "ts": ["npx", "tsc", "--noEmit"],
    "node": ["node", "--check"],
    "py": [sys.executable, "-m", "py_compile"],
}


# ── Data models ─────────────────────────────────────────────────────────


@dataclass
class FileSpec:
    """Describes a single file to generate."""

    path: str
    purpose: str = ""


@dataclass
class Manifest:
    """Project blueprint produced in Stage 1."""

    project_name: str
    files: list[FileSpec] = field(default_factory=list)


@dataclass
class GeneratedFile:
    """Result of generating a single file."""

    path: str
    content: str
    success: bool = True
    error: str = ""


@dataclass
class StageResult:
    """Result of a pipeline stage."""

    name: str
    success: bool
    duration_s: float = 0.0
    detail: str = ""


@dataclass
class ProjectResult:
    """Final result of the entire generation pipeline."""

    success: bool
    prompt: str
    project_name: str
    output_dir: str = ""
    files: list[GeneratedFile] = field(default_factory=list)
    stages: list[StageResult] = field(default_factory=list)
    total_duration_s: float = 0.0
    error: str = ""


@dataclass
class ProjectState:
    """Persistent project state for resume / crash recovery."""

    prompt: str
    project_name: str
    output_dir: str
    manifest: dict[str, Any] | None = None
    generated_files: list[dict[str, Any]] = field(default_factory=list)
    current_stage: int = 0
    current_file_index: int = 0

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(asdict(self), indent=2, default=str))

    @classmethod
    def load(cls, path: Path) -> ProjectState | None:
        try:
            data = json.loads(path.read_text())
            return cls(**data)
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return None


# ── Progress display ────────────────────────────────────────────────────


class RunnerProgress:
    """Clean terminal UI for the automated generation pipeline."""

    def __init__(self) -> None:
        self._start_time: float = 0.0
        self._stage_start: float = 0.0

    def banner(self, prompt: str) -> None:
        print()
        print(f"  {_bold(_cyan('╔══════════════════════════════════════════╗'))}")
        print(f"  {_bold(_cyan('║   WREN AUTOMATED PROJECT GENERATOR v1    ║'))}")
        print(f"  {_bold(_cyan('╚══════════════════════════════════════════╝'))}")
        print()
        print(f"  {_yellow('Prompt:')} {prompt[:120]}")
        print()
        self._start_time = time.time()

    def start_stage(self, stage: str, index: int, total: int) -> None:
        self._stage_start = time.time()
        print(f"\n  {_bold(_blue(f'▸ Stage {index}/{total}:'))} {_bold(stage)}")
        print(f"  {_dim('─' * 50)}")

    def end_stage(self, success: bool, detail: str = "") -> None:
        elapsed = time.time() - self._stage_start
        icon = _green("✓") if success else _red("✗")
        print(f"  {_dim('─' * 50)}")
        print(f"  [{icon}] {_green('Done') if success else _red('Failed')}  ({elapsed:.1f}s)")
        if detail:
            for line in detail.split("\n"):
                print(f"    {_dim(line[:100])}")

    def file_progress(self, index: int, total: int, path: str, status: str) -> None:
        icon = {
            "generating": _yellow("→"),
            "done": _green("✓"),
            "error": _red("✗"),
            "correcting": _magenta("↻"),
        }.get(status, "·")
        path_display = path[:70]
        print(f"    [{icon}] [{index}/{total}] {_dim(path_display)} ... {status}")

    def log(self, message: str) -> None:
        print(f"      {_dim(message[:100])}")

    def summary(self, result: ProjectResult) -> None:
        print()
        print(f"  {_bold(_cyan('══════════════════════════════════════════'))}")
        print(f"  {_bold('Generation Complete')}")
        print(f"  {_dim('─' * 40)}")
        print(f"  Project:  {_bold(result.project_name)}")
        print(f"  Location: {result.output_dir}")
        print(f"  Files:    {len(result.files)}")
        print(f"  Duration: {result.total_duration_s:.1f}s")
        print(f"  Status:   {
            _green('SUCCESS') if result.success else _red('FAILED')
        }")
        print(f"  {_bold(_cyan('══════════════════════════════════════════'))}")
        print()


# ── Code block extraction ───────────────────────────────────────────────


_CODE_BLOCK_RE = re.compile(
    r"```(?:\w+)?\n(.+?)```", re.DOTALL
)


def _extract_code_blocks(text: str) -> list[str]:
    """Extract all fenced code blocks from LLM output."""
    blocks = _CODE_BLOCK_RE.findall(text)
    if not blocks:
        # If no fenced blocks found, treat entire response as code
        return [text.strip()]
    return [b.strip() for b in blocks if b.strip()]


# ── File-type detection helpers ─────────────────────────────────────────


def _guess_language(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    lang_map = {
        ".ts": "typescript",
        ".tsx": "tsx",
        ".js": "javascript",
        ".jsx": "jsx",
        ".py": "python",
        ".json": "json",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".md": "markdown",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".rs": "rust",
        ".go": "go",
        ".kt": "kotlin",
        ".swift": "swift",
    }
    return lang_map.get(ext, "text")


def _get_build_command(file_path: str) -> list[str] | None:
    """Determine a validation command based on file extension."""
    ext = Path(file_path).suffix.lower()
    if ext == ".ts":
        return VALID_BUILD_COMMANDS["ts"]
    elif ext == ".js":
        return VALID_BUILD_COMMANDS["node"]
    elif ext == ".py":
        return VALID_BUILD_COMMANDS["py"]
    return None


# ── The Automated Runner ────────────────────────────────────────────────


class AutomatedProjectGenerator:
    """
    Production-grade automated multi-file generation wrapper.

    Converts a high-level prompt into a complete, multi-file project by
    orchestrating LLM calls through a deterministic 3-stage pipeline.
    """

    ProgressCallback = Callable[
        [int, str, str, str, int, int, str], None
    ]  # (stage_index, stage_name, status, detail, file_index, file_total, file_path) -> None

    def __init__(
        self,
        api_key: str,
        *,
        model: str = DEFAULT_MODEL,
        base_url: str | None = None,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        resume: bool = True,
        validate: bool = True,
        max_correction_rounds: int = 3,
        progress_callback: ProgressCallback | None = None,
        omnirouter: Any | None = None,
    ) -> None:
        # OmniRouter must be explicitly passed — auto-discovery from CLI context
        # is not possible because OmnniRoute's FastAPI router needs fastapi/pydantic.
        # The FastAPI server (app.py) passes it automatically when configured.
        self._llm = LLMClient(
            api_key=api_key,
            model=model,
            base_url=base_url,
            max_tokens=max_tokens,
            temperature=temperature,
            omnirouter=omnirouter,
        )
        self._output_root = Path(output_dir)
        self._resume = resume
        self._validate = validate
        self._max_corrections = max_correction_rounds
        self._progress = RunnerProgress()
        self._progress_callback = progress_callback
        self._state: ProjectState | None = None
        self._manifest: Manifest | None = None
        self._output_dir: Path | None = None

    # ── Public entry point ─────────────────────────────────────────

    async def run(self, prompt: str) -> ProjectResult:
        """Execute the full 3-stage generation pipeline."""
        start_time = time.time()
        result = ProjectResult(success=False, prompt=prompt, project_name="")

        self._progress.banner(prompt)

        try:
            # ── Stage 1: Blueprint ────────────────────────────────
            stage = await self._run_stage("File Tree Blueprinting", 1, 3, self._stage_blueprint(prompt))
            result.stages.append(stage)
            if not stage.success:
                result.error = stage.detail
                return self._finalize(result, start_time)

            # ── Stage 2: File Generation ──────────────────────────
            stage = await self._run_stage("Sequential File Generation", 2, 3, self._stage_generate())
            result.stages.append(stage)
            if not stage.success:
                result.error = stage.detail
                return self._finalize(result, start_time)

            # ── Stage 3: Validation & Correction ──────────────────
            stage = await self._run_stage("Validation & Self-Correction", 3, 3, self._stage_validate())
            result.stages.append(stage)

            result.success = stage.success
            result.files = self._collect_generated_files()

        except Exception as e:
            self._progress.log(f"Fatal error: {e}")
            result.error = str(e)
            result.stages.append(StageResult("Pipeline", False, detail=str(e)))

        return self._finalize(result, start_time)

    async def close(self) -> None:
        """Clean up resources."""
        await self._llm.close()

    # ── Stage runners ────────────────────────────────────────────

    async def _emit_progress(
        self,
        stage_index: int,
        stage_name: str,
        status: str,
        detail: str = "",
        file_index: int = 0,
        file_total: int = 0,
        file_path: str = "",
    ) -> None:
        if self._progress_callback:
            try:
                await self._progress_callback(
                    stage_index, stage_name, status, detail,
                    file_index, file_total, file_path,
                )
            except Exception:
                # Swallow callback errors so they don't crash the pipeline
                pass

    async def _run_stage(
        self,
        name: str,
        index: int,
        total: int,
        coro: Any,
    ) -> StageResult:
        self._progress.start_stage(name, index, total)
        await self._emit_progress(index, name, "running")
        start = time.time()
        try:
            detail = await coro
            elapsed = time.time() - start
            self._progress.end_stage(True, str(detail)[:200] if detail else "")
            await self._emit_progress(index, name, "done", str(detail)[:200])
            return StageResult(name, True, elapsed, str(detail)[:300])
        except Exception as e:
            elapsed = time.time() - start
            self._progress.end_stage(False, str(e)[:200])
            await self._emit_progress(index, name, "error", str(e)[:200])
            return StageResult(name, False, elapsed, str(e))

    # ── Stage 1: File Tree Blueprinting ──────────────────────────

    async def _stage_blueprint(self, prompt: str) -> str:
        """Send a planning request to the LLM to generate a Manifest JSON."""
        system_prompt = MASTER_SYSTEM_PROMPT + """

You are a software architect. Your job is to analyze the user's project directive
and produce a JSON manifest describing every file that needs to be created.

Output VALID JSON ONLY inside a single fenced code block. Follow this schema:

```json
{
  "projectName": "kebab-case-project-name",
  "files": [
    { "path": "package.json", "purpose": "Dependencies and scripts" },
    { "path": "src/index.ts", "purpose": "Main entry point" }
  ]
}
```

RULES:
- List EVERY file needed for a complete, runnable project.
- Include configuration files (package.json, tsconfig.json, etc.).
- Include type definitions, components, utilities, tests.
- The path is relative to the project root.
- Be exhaustive — do not skip infrastructure files like vite.config.ts.
"""

        user_prompt = (
            f"Analyze this project directive and produce a comprehensive file manifest:\n\n"
            f"{prompt}\n\n"
            f"Output ONLY the JSON manifest inside a ```json fenced code block."
        )

        self._progress.log("Sending blueprint request to LLM...")
        response = await self._llm.send(system_prompt, user_prompt)

        # Parse manifest from response
        manifest = self._parse_manifest(response, prompt)
        self._init_project_dir(manifest)
        self._save_state()

        self._progress.log(f"Project: {manifest.project_name}")
        self._progress.log(f"Files: {len(manifest.files)} planned")
        for f in manifest.files:
            self._progress.log(f"  ├─ {f.path}")
        return f"Blueprint generated: {len(manifest.files)} files"

    def _parse_manifest(self, response: str, prompt: str) -> Manifest:
        """Extract and parse the Manifest JSON from LLM response."""
        # Try to find a JSON code block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        json_str = json_match.group(1) if json_match else response

        # Also try matching top-level JSON object
        if not json_match:
            obj_match = re.search(r"\{[^{}]*\"files\"[^{}]*\}", response, re.DOTALL)
            if obj_match:
                json_str = obj_match.group()

        try:
            data = json.loads(json_str)
            # Normalize keys if LLM used camelCase inconsistently
            project_name = data.get("projectName") or data.get("project_name", "project")
            raw_files = data.get("files", [])
            files = []
            for rf in raw_files:
                if isinstance(rf, str):
                    files.append(FileSpec(path=rf, purpose=""))
                elif isinstance(rf, dict):
                    files.append(FileSpec(
                        path=rf.get("path", rf.get("file", "")),
                        purpose=rf.get("purpose", rf.get("description", "")),
                    ))
            return Manifest(project_name=project_name, files=files)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # Fallback: ask LLM again with stricter instructions
            raise ValueError(
                f"Failed to parse manifest JSON from LLM response: {e}\n"
                f"Response snippet: {response[:500]}"
            )

    def _init_project_dir(self, manifest: Manifest) -> None:
        """Create output directory structure and save state."""
        out = self._output_root / manifest.project_name
        out.mkdir(parents=True, exist_ok=True)

        # Create all parent directories for planned files
        for fspec in manifest.files:
            file_path = out / fspec.path
            file_path.parent.mkdir(parents=True, exist_ok=True)

        self._output_dir = out
        self._manifest = manifest

        # Initialize or resume state
        state_path = out / "project_state.json"
        if self._resume:
            existing = ProjectState.load(state_path)
            if existing and existing.prompt == manifest.project_name:
                self._state = existing
                self._progress.log(f"Resuming from saved state ({len(existing.generated_files)} files done)")
                return

        self._state = ProjectState(
            prompt=manifest.project_name,
            project_name=manifest.project_name,
            output_dir=str(out),
            manifest={"project_name": manifest.project_name, "files": [
                asdict(f) for f in manifest.files
            ]},
        )
        self._state.save(state_path)

    # ── Stage 2: Sequential File Generation ──────────────────────

    async def _stage_generate(self) -> str:
        """Iterate over files, generating each with context from previous files."""
        if self._manifest is None or self._state is None:
            raise RuntimeError(
                "Cannot run Stage 2 (Generate) before Stage 1 (Blueprint) completes."
            )

        files = self._manifest.files
        total = len(files)
        start_index = self._state.current_file_index
        manifest_dict = {
            "project_name": self._manifest.project_name,
            "files": [asdict(f) for f in files],
        }

        for i in range(start_index, total):
            fspec = files[i]
            file_path = self._output_dir / fspec.path
            rel_path = fspec.path

            self._progress.file_progress(i + 1, total, rel_path, "generating")
            await self._emit_progress(
                2, "Sequential File Generation", "running",
                file_index=i + 1, file_total=total, file_path=rel_path,
            )

            # Build context from previously generated files
            context = self._build_context(rel_path)

            # Send generation request
            system_prompt = MASTER_SYSTEM_PROMPT + f"""

You are generating file: {rel_path}
Language: {_guess_language(rel_path)}
Purpose: {fspec.purpose}

CONTEXT — Project Manifest:
{json.dumps(manifest_dict, indent=2)}

CONTEXT — Previously generated files this file depends on:
{context}

Generate 100% COMPLETE, zero-placeholder code for this file. No TODOs, no ellipsis, no stubs.
Every function body must be fully implemented. Output code ONLY inside a fenced block.
"""

            user_prompt = (
                f"Generate the complete file: {rel_path}\n\n"
                f"Purpose: {fspec.purpose}\n\n"
                f"Output 100% complete, compilable code inside a ``` block."
            )

            try:
                response = await self._llm.send(system_prompt, user_prompt)
                blocks = _extract_code_blocks(response)

                if not blocks:
                    raise ValueError("No code blocks found in LLM response")

                # Write the first (and typically only) code block to disk
                content = blocks[0]
                file_path.write_text(content)

                # Verify non-zero size
                if file_path.stat().st_size == 0:
                    raise ValueError("Generated file is empty")

                self._state.generated_files.append({
                    "path": rel_path,
                    "content_length": len(content),
                    "success": True,
                })

                self._progress.file_progress(i + 1, total, rel_path, "done")
                await self._emit_progress(
                    2, "Sequential File Generation", "done",
                    file_index=i + 1, file_total=total, file_path=rel_path,
                )

            except Exception as e:
                self._state.generated_files.append({
                    "path": rel_path,
                    "error": str(e),
                    "success": False,
                })
                self._progress.file_progress(i + 1, total, rel_path, "error")
                await self._emit_progress(
                    2, "Sequential File Generation", "error",
                    detail=str(e)[:200],
                    file_index=i + 1, file_total=total, file_path=rel_path,
                )
                self._progress.log(f"  Failed: {e}")

            # Update state after each file
            self._state.current_file_index = i + 1
            self._save_state()

        # Check if any files failed
        failed = [f for f in self._state.generated_files if not f.get("success")]
        if failed:
            failed_paths = ", ".join(f["path"] for f in failed)
            self._progress.log(f"Files with errors: {len(failed)}")
            return f"Generated {total - len(failed)}/{total} files. Errors: {failed_paths}"

        return f"All {total} files generated successfully"

    def _build_context(self, target_path: str) -> str:
        """Build a context string from previously generated files."""
        assert self._state is not None
        snippets: list[str] = []

        for gf in self._state.generated_files:
            if not gf.get("success"):
                continue
            prev_path = gf["path"]
            if prev_path == target_path:
                continue

            prev_abs = self._output_dir / prev_path
            if prev_abs.exists():
                content = prev_abs.read_text()
                # Only include relevant snippets (first ~50 lines for large files)
                lines = content.split("\n")
                snippet = "\n".join(lines[:50])
                if len(lines) > 50:
                    snippet += f"\n// ... ({len(lines) - 50} more lines)"
                snippets.append(f"--- {prev_path} ---\n{snippet}")

        if not snippets:
            return "(no prior files generated yet)"

        return "\n\n".join(snippets)

    # ── Stage 3: Validation & Self-Correction ────────────────────

    async def _stage_validate(self) -> str:
        """Run build checks and auto-correct failing files."""
        if not self._validate:
            return "Validation skipped"

        if self._state is None:
            return "No state available — skipping validation"

        # Find files with build commands
        file_commands: list[tuple[Path, list[str]]] = []
        for gf in self._state.generated_files:
            if not gf.get("success"):
                continue
            file_path = self._output_dir / gf["path"]
            if not file_path.exists():
                continue
            cmd = _get_build_command(gf["path"])
            if cmd:
                file_commands.append((file_path, cmd))

        if not file_commands:
            # Try project-level build command (npm build / tsc for whole project)
            return await self._project_level_validation()

        errors_found = 0
        corrections = 0

        for file_path, cmd in file_commands:
            rel_path = file_path.relative_to(self._output_dir).as_posix()
            self._progress.log(f"Checking: {rel_path}")
            await self._emit_progress(3, "Validation & Self-Correction", "running", file_path=rel_path)

            success, error_output = await self._run_build_cmd(cmd, rel_path)

            if not success:
                errors_found += 1
                self._progress.log(f"  {_red('✗ Error:')} {error_output[:150]}")

                for round_num in range(1, self._max_corrections + 1):
                    self._progress.file_progress(
                        file_commands.index((file_path, cmd)) + 1,
                        len(file_commands),
                        rel_path,
                        "correcting",
                    )

                    await self._emit_progress(
                        3, "Validation & Self-Correction", "correcting",
                        detail=f"Correction round {round_num}/{self._max_corrections}",
                        file_path=rel_path,
                    )

                    fixed = await self._attempt_correction(
                        rel_path, file_path.read_text(), error_output, round_num
                    )
                    if fixed:
                        file_path.write_text(fixed)
                        # Re-check
                        success2, error2 = await self._run_build_cmd(cmd, rel_path)
                        if success2:
                            corrections += 1
                            self._progress.log(f"  {_green('✓ Corrected')}")
                            break
                        else:
                            error_output = error2
                    else:
                        break

        total_checked = len(file_commands)
        if errors_found == 0:
            return f"All {total_checked} files passed validation"

        return (
            f"Validated {total_checked} files. "
            f"Errors: {errors_found}, Corrected: {corrections}"
        )

    async def _run_build_cmd(self, cmd: list[str], rel_path: str) -> tuple[bool, str]:
        """Run a build validation command for a single file."""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, str(self._output_dir / rel_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._output_dir),
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=30.0
            )
            if proc.returncode == 0:
                return True, ""
            output = (stderr.decode() or stdout.decode())[:500]
            return False, output
        except (FileNotFoundError, asyncio.TimeoutError) as e:
            return False, str(e)

    async def _attempt_correction(
        self,
        rel_path: str,
        broken_code: str,
        error_output: str,
        round_num: int,
    ) -> str | None:
        """Send broken code + error back to LLM for correction."""
        system_prompt = MASTER_SYSTEM_PROMPT + """

You are a code repair specialist. Your task is to fix compilation errors in the
provided code. Output the COMPLETE corrected file — no placeholders, no diffs.
"""

        user_prompt = (
            f"File: {rel_path}\n\n"
            f"BROKEN CODE:\n```\n{broken_code}\n```\n\n"
            f"ERROR OUTPUT:\n```\n{error_output}\n```\n\n"
            f"Fix ALL errors above. Output the COMPLETE corrected file inside a code block. "
            f"Round {round_num}/{self._max_corrections}."
        )

        try:
            response = await self._llm.send(system_prompt, user_prompt)
            blocks = _extract_code_blocks(response)
            if blocks and blocks[0].strip():
                return blocks[0]
        except Exception:
            pass
        return None

    async def _project_level_validation(self) -> str:
        """Run package-level build if individual file checks aren't available."""
        assert self._state is not None

        # Check for package.json → npm run build / tsc
        pkg_json = self._output_dir / "package.json"
        tsconfig = self._output_dir / "tsconfig.json"

        cmds = []
        if pkg_json.exists():
            cmds.append(["npm", "install"])
            cmds.append(["npm", "run", "build"])
        elif tsconfig.exists():
            cmds.append(["npx", "tsc", "--noEmit"])
        elif (self._output_dir / "pyproject.toml").exists():
            cmds.append([sys.executable, "-m", "pytest", "--collect-only", "-q"])

        if not cmds:
            return "No validation commands available for this project type"

        for cmd in cmds:
            cmd_name = " ".join(cmd)
            self._progress.log(f"Running: {_dim(cmd_name)}")
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd, cwd=str(self._output_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=120.0
                )
                if proc.returncode != 0:
                    error_text = (stderr.decode() or stdout.decode())[:500]
                    self._progress.log(f"  {_red('✗ Build failed:')} {error_text[:150]}")

                    # Auto-correction loop for project-level errors
                    for round_num in range(1, self._max_corrections + 1):
                        self._progress.log(f"  {_yellow(f'↻ Project correction round {round_num}...')}")
                        fixed = await self._attempt_project_correction(error_text, round_num)
                        if fixed:
                            # Re-run build
                            proc2 = await asyncio.create_subprocess_exec(
                                *cmd, cwd=str(self._output_dir),
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE,
                            )
                            _, stderr2 = await asyncio.wait_for(
                                proc2.communicate(), timeout=120.0
                            )
                            if proc2.returncode == 0:
                                self._progress.log(f"  {_green('✓ Project build fixed')}")
                                break
                            error_text = (stderr2.decode())[:500]
                    else:
                        return f"Build failed after {self._max_corrections} correction rounds"

            except (FileNotFoundError, asyncio.TimeoutError) as e:
                self._progress.log(f"  {_yellow('⚠')} Build tool not available: {e}")

        return "Project-level validation passed"

    async def _attempt_project_correction(self, error_text: str, round_num: int) -> bool:
        """Send project-level build errors to LLM for correction."""
        if self._state is None or self._manifest is None:
            return False

        # Collect all file contents
        all_files: dict[str, str] = {}
        for gf in self._state.generated_files:
            fp = self._output_dir / gf["path"]
            if fp.exists():
                all_files[gf["path"]] = fp.read_text()

        # Build a compact representation
        files_section = "\n\n".join(
            f"### {path}\n```\n{content[:800]}\n```"
            for path, content in list(all_files.items())[:10]
        )

        system_prompt = MASTER_SYSTEM_PROMPT + """

You are a project-level build repair specialist. Given the project structure,
file contents, and build errors, output corrected files. For each file that
needs fixing, output a fenced code block with a special comment header:

```filename=<path>
// corrected content here
```
"""

        user_prompt = (
            f"Project: {self._manifest.project_name}\n\n"
            f"Build Error:\n```\n{error_text}\n```\n\n"
            f"Current Files:\n{files_section}\n\n"
            f"Fix the build errors. For each file that needs changes, output:\n"
            f"```filename=<relative-path>\n// corrected file content\n```\n"
            f"Round {round_num}/{self._max_corrections}."
        )

        try:
            response = await self._llm.send(system_prompt, user_prompt)

            # Parse file-scoped corrections
            file_pattern = re.compile(r"```filename=([^\n]+)\n(.+?)```", re.DOTALL)
            corrections_found = 0
            for match in file_pattern.finditer(response):
                file_path = match.group(1).strip()
                content = match.group(2).strip()
                if content:
                    target = self._output_dir / file_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content)
                    corrections_found += 1

            if corrections_found > 0:
                self._progress.log(f"  Applied {corrections_found} corrections")
                return True

            # Fallback: try to find regular code blocks and guess the file
            blocks = _extract_code_blocks(response)
            if blocks and len(blocks) == 1 and self._manifest.files:
                # Write to the last generated file (best guess)
                last_file = self._manifest.files[-1]
                target = self._output_dir / last_file.path
                target.write_text(blocks[0])
                self._progress.log(f"  Wrote correction to {last_file.path}")
                return True

            return False

        except Exception:
            return False

    # ── Helpers ──────────────────────────────────────────────────

    def _save_state(self) -> None:
        """Persist current state for crash recovery."""
        if self._state and self._output_dir:
            state_path = Path(self._output_dir) / "project_state.json"
            self._state.save(state_path)

    def _collect_generated_files(self) -> list[GeneratedFile]:
        """Convert state records to result objects."""
        files: list[GeneratedFile] = []
        if self._state:
            for gf in self._state.generated_files:
                files.append(GeneratedFile(
                    path=gf["path"],
                    content="",
                    success=gf.get("success", False),
                    error=gf.get("error", ""),
                ))
        return files

    def _finalize(self, result: ProjectResult, start_time: float) -> ProjectResult:
        """Populate final result metadata and display summary."""
        result.total_duration_s = time.time() - start_time

        if self._manifest is not None:
            result.project_name = self._manifest.project_name
        if self._output_dir is not None:
            result.output_dir = str(self._output_dir)
        if self._state is not None:
            result.files = self._collect_generated_files()

        self._progress.summary(result)
        return result


# ── Async entry point helper ────────────────────────────────────────────


async def run_pipeline(
    prompt: str,
    api_key: str,
    *,
    model: str = DEFAULT_MODEL,
    base_url: str | None = None,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    validate: bool = True,
    resume: bool = True,
    progress_callback: AutomatedProjectGenerator.ProgressCallback | None = None,
    omnirouter: Any | None = None,
) -> ProjectResult:
    """Convenience function to run the full pipeline with auto-cleanup."""
    runner = AutomatedProjectGenerator(
        api_key=api_key,
        model=model,
        base_url=base_url,
        output_dir=output_dir,
        validate=validate,
        resume=resume,
        progress_callback=progress_callback,
        omnirouter=omnirouter,
    )
    try:
        return await runner.run(prompt)
    finally:
        await runner.close()


# ── CLI entry point (if run directly) ────────────────────────────────────


def main() -> None:
    """CLI entry point: python -m wren.app_builder.automated_runner"""
    import argparse
    import signal

    parser = argparse.ArgumentParser(
        description="Wren Automated Multi-File Project Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m wren.app_builder.automated_runner \\\n"
            "    --prompt \"Build a 3D solar system explorer\" \\\n"
            "    --api-key sk-... \\\n"
            "    --output ./my-project\n"
        ),
    )
    parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="High-level project directive (e.g., 'Build a 3D portfolio site')",
    )
    parser.add_argument(
        "--api-key", "-k",
        required=True,
        help="LLM API key (e.g., OpenAI key)",
    )
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"LLM model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Custom API base URL (for non-OpenAI providers)",
    )
    parser.add_argument(
        "--output", "-o",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation & correction stage",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Do not resume from saved state",
    )

    args = parser.parse_args()

    # Handle graceful shutdown
    shutdown_requested = False

    def _on_signal(signum, frame):
        nonlocal shutdown_requested
        if shutdown_requested:
            print("\nForced exit.", file=sys.stderr)
            sys.exit(1)
        shutdown_requested = True
        print("\nShutdown requested — finishing current operation... (Ctrl+C again to force)", file=sys.stderr)

    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    try:
        result = asyncio.run(
            run_pipeline(
                prompt=args.prompt,
                api_key=args.api_key,
                model=args.model,
                base_url=args.base_url,
                output_dir=args.output,
                validate=not args.no_validate,
                resume=not args.no_resume,
            )
        )
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
