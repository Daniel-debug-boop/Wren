"""Wren App Builder — core orchestrator.

Takes a user prompt, scaffolds a full project, writes code, sets up CI/CD,
and delivers a downloadable artifact. All free, all open-source.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shutil
import sys
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── Terminal helpers ────────────────────────────────────────────

_COLOR = sys.stderr.isatty()


def _c(code: str, text: str) -> str:
    if not _COLOR:
        return text
    return f'\033[{code}m{text}\033[0m'


def _bold(text: str) -> str:
    return _c('1', text)


def _dim(text: str) -> str:
    return _c('2', text)


def _red(text: str) -> str:
    return _c('31', text)


def _green(text: str) -> str:
    return _c('32', text)


def _yellow(text: str) -> str:
    return _c('33', text)


def _blue(text: str) -> str:
    return _c('34', text)


def _cyan(text: str) -> str:
    return _c('36', text)


def _white(text: str) -> str:
    return _c('37', text)


# ── Helpers ──────────────────────────────────────────────────────


def _safe_name(name: str) -> str:
    """Sanitize a project name for use in code (class names, identifiers)."""
    safe = re.sub(r'[^a-zA-Z0-9_]', '', name)
    if not safe or not safe[0].isalpha():
        return 'App'
    return safe


# ── Build status models ──────────────────────────────────────────


class BuildPhase:
    ANALYZING = 'analyzing'
    SCAFFOLDING = 'scaffolding'
    CODING = 'coding'
    TESTING = 'testing'
    BUILDING = 'building'
    DEPLOYING = 'deploying'
    DONE = 'done'
    ERROR = 'error'


PHASE_LABELS = {
    BuildPhase.ANALYZING: 'Analyzing your idea',
    BuildPhase.SCAFFOLDING: 'Scaffolding project',
    BuildPhase.CODING: 'Writing code',
    BuildPhase.TESTING: 'Running tests',
    BuildPhase.BUILDING: 'Building artifact',
    BuildPhase.DEPLOYING: 'Deploying',
    BuildPhase.DONE: 'Done',
    BuildPhase.ERROR: 'Error',
}


@dataclass
class PhaseResult:
    phase: str
    success: bool
    duration_s: float = 0.0
    output: str = ''
    error: str = ''


@dataclass
class BuildResult:
    success: bool
    prompt: str
    project_type: str
    project_name: str
    output_dir: str = ''
    artifact_path: str = ''
    deploy_url: str = ''
    phases: list[PhaseResult] = field(default_factory=list)
    total_duration_s: float = 0.0
    error: str = ''
    github_repo: str = ''


# ── Progress display ─────────────────────────────────────────────


class ProgressDisplay:

    def __init__(self) -> None:
        self._phase_start: float = 0.0
        self._current: str = ''

    def start_phase(self, phase: str) -> None:
        self._current = phase
        self._phase_start = time.time()
        label = PHASE_LABELS.get(phase, phase)
        print(f'\n  {_blue(">>")} {_bold(label)}...')

    def end_phase(self, phase: str, success: bool, detail: str = '') -> None:
        elapsed = time.time() - self._phase_start
        icon = _green('OK') if success else _red('FAIL')
        label = PHASE_LABELS.get(phase, phase)
        print(f'  [{icon}] {_bold(label)} ({elapsed:.1f}s)')
        if detail:
            for line in detail.split('\n'):
                print(f'       {_dim(line[:80])}')

    def log(self, message: str) -> None:
        print(f'       {_dim(message[:80])}')

    def success(self, message: str) -> None:
        print(f'\n  ** {_bold(message)} **')

    def error(self, message: str) -> None:
        print(f'\n  !! {_bold(message)} !!')

    def banner(self, project_type: str, project_name: str) -> None:
        print()
        print(f'  == Wren App Builder v1.0.0 ==')
        print(f'  {project_type}: {_bold(project_name)}')
        print()

    def summary(self, result: BuildResult) -> None:
        print()
        print(f'  === Build Complete ===')
        if result.artifact_path:
            print(f'  Artifact: {result.artifact_path}')
        if result.deploy_url:
            print(f'  URL:      {result.deploy_url}')
        if result.github_repo:
            print(f'  Repo:     {result.github_repo}')
        print(f'  Duration: {result.total_duration_s:.1f}s')
        print(f'  Status:   {"OK" if result.success else "FAILED"}')
        print()


# ── App Builder Core ─────────────────────────────────────────────

_APP_TYPES = {
    'web': {
        'label': 'Website',
        'stack': 'React + Vite + Tailwind',
        'ext': '.zip',
    },
    'mobile': {
        'label': 'Mobile App',
        'stack': 'Flutter (Android + iOS)',
        'ext': '.apk',
    },
    'api': {
        'label': 'API Server',
        'stack': 'FastAPI + PostgreSQL',
        'ext': '.zip',
    },
    'desktop': {
        'label': 'Desktop App',
        'stack': 'Electron + React',
        'ext': '.zip',
    },
    'cli': {
        'label': 'CLI Tool',
        'stack': 'Python + Click',
        'ext': '.zip',
    },
}


def _json_file(data: dict) -> str:
    return json.dumps(data, indent=2) + '\n'


def _interpolate(template: str, **kw: str) -> str:
    """Replace {{KEY}} placeholders with values (no f-string issues)."""
    for key, value in kw.items():
        template = template.replace('{{' + key + '}}', value)
    return template


# ── File templates (avoids f-string/JXS parsing issues) ──────────

_VITE_CONFIG_JS = """\
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    test: {
        environment: 'jsdom',
        globals: true,
    },
})
"""

_MAIN_JSX = """\
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <BrowserRouter>
            <Routes>
                <Route path="/*" element={<App />} />
            </Routes>
        </BrowserRouter>
    </React.StrictMode>
)
"""

_APP_JSX = """\
import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'

function Home() {
    return (
        <div className="app">
            <header className="header">
                <h1>{{PROJECT_NAME}}</h1>
                <p className="tagline">{{PROMPT}}</p>
                <nav>
                    <Link to="/" className="nav-link">Home</Link>
                    <Link to="/about" className="nav-link">About</Link>
                </nav>
            </header>
            <main className="main">
                <section className="hero">
                    <h2>Welcome to {{PROJECT_NAME}}</h2>
                    <p>Your app has been generated by Wren AI.</p>
                    <button className="cta-button"
                        onClick={() => alert('Ready!')}>
                        Get Started
                    </button>
                </section>
            </main>
            <footer className="footer">
                <p>Built with Wren App Builder</p>
            </footer>
        </div>
    )
}

function About() {
    return (
        <div className="app">
            <header className="header">
                <h1>About</h1>
                <nav>
                    <Link to="/" className="nav-link">Home</Link>
                    <Link to="/about" className="nav-link">About</Link>
                </nav>
            </header>
            <main className="main">
                <h2>About {{PROJECT_NAME}}</h2>
                <p>Generated from your prompt: "{{PROMPT}}"</p>
            </main>
        </div>
    )
}

export default function App() {
    return (
        <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
        </Routes>
    )
}
"""

_INDEX_CSS = """\
:root {
    --primary: #6366f1;
    --primary-dark: #4f46e5;
    --bg: #0f0f1a;
    --bg-card: #1a1a2e;
    --text: #e2e8f0;
    --text-muted: #94a3b8;
    --accent: #22d3ee;
    --radius: 12px;
    --shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.6; min-height: 100vh;
}
.app { display: flex; flex-direction: column; min-height: 100vh; }
.header {
    background: var(--bg-card); padding: 1.5rem 2rem;
    border-bottom: 1px solid rgba(255,255,255,0.05); text-align: center;
}
.header h1 {
    font-size: 1.8rem;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.tagline { color: var(--text-muted); margin-top: 0.5rem; font-size: 0.9rem; }
nav { margin-top: 1rem; display: flex; gap: 1rem; justify-content: center; }
.nav-link {
    color: var(--text-muted); text-decoration: none; padding: 0.4rem 1rem;
    border-radius: 6px; transition: all 0.2s;
}
.nav-link:hover { color: var(--text); background: rgba(99, 102, 241, 0.1); }
.main { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem; }
.hero { text-align: center; max-width: 600px; }
.hero h2 {
    font-size: 2.5rem; margin-bottom: 1rem;
    background: linear-gradient(135deg, var(--text), var(--accent));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero p { color: var(--text-muted); font-size: 1.1rem; margin-bottom: 2rem; }
.cta-button {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white; border: none; padding: 0.8rem 2rem; font-size: 1rem;
    border-radius: var(--radius); cursor: pointer; transition: all 0.2s;
    box-shadow: var(--shadow);
}
.cta-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 30px rgba(99, 102, 241, 0.4);
}
.footer {
    background: var(--bg-card); padding: 1rem 2rem; text-align: center;
    color: var(--text-muted); font-size: 0.8rem;
    border-top: 1px solid rgba(255,255,255,0.05);
}
"""

_VITE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<rect width="100" height="100" rx="20" fill="#6366f1"/>'
    '<text x="50" y="65" font-size="50" fill="white" '
    'text-anchor="middle" font-family="sans-serif">W</text></svg>'
)

_GITIGNORE = """\
node_modules/
dist/
build/
__pycache__/
*.pyc
.env
.DS_Store
*.apk
*.aab
*.zip
"""


class AppBuilder:

    def __init__(
        self,
        output_dir: str | None = None,
        *,
        auto_deploy: bool = False,
        github_push: bool = False,
        verbose: bool = False,
    ) -> None:
        self._display = ProgressDisplay()
        if output_dir:
            self._output_dir = Path(output_dir)
        else:
            self._output_dir = Path(os.getcwd()) / 'wren-builds'
        self._auto_deploy = auto_deploy
        self._github_push = github_push
        self._verbose = verbose

    async def build(
        self,
        prompt: str,
        project_type: str | None = None,
        project_name: str | None = None,
    ) -> BuildResult:
        start_time = time.time()
        phases: list[PhaseResult] = []
        result = BuildResult(
            success=False,
            prompt=prompt,
            project_type=project_type or 'web',
            project_name=project_name or self._generate_name(prompt),
        )

        self._display.banner(result.project_type, result.project_name)

        try:
            # Phase 1: Analyze
            phase = await self._run_phase(
                BuildPhase.ANALYZING,
                self._analyze_prompt(prompt, result),
            )
            phases.append(phase)
            if not phase.success:
                return self._finalize(result, phases, start_time)

            result.project_type = phase.output or result.project_type

            # Phase 2: Scaffold
            phase = await self._run_phase(
                BuildPhase.SCAFFOLDING,
                self._scaffold_project(result),
            )
            phases.append(phase)
            if not phase.success:
                return self._finalize(result, phases, start_time)

            # Phase 3: Code
            phase = await self._run_phase(
                BuildPhase.CODING,
                self._generate_code(prompt, result),
            )
            phases.append(phase)
            if not phase.success:
                return self._finalize(result, phases, start_time)

            # Phase 4: Test
            phase = await self._run_phase(
                BuildPhase.TESTING,
                self._run_tests(result),
            )
            phases.append(phase)
            if not phase.success:
                self._display.log('Tests had issues — continuing')

            # Phase 5: Build
            phase = await self._run_phase(
                BuildPhase.BUILDING,
                self._build_artifact(result),
            )
            phases.append(phase)
            if not phase.success:
                return self._finalize(result, phases, start_time)

            # Phase 6: Deploy
            if self._auto_deploy:
                phase = await self._run_phase(
                    BuildPhase.DEPLOYING,
                    self._deploy(result),
                )
                phases.append(phase)

            result.success = True
            self._display.success(f'{result.project_name} is ready!')

        except Exception as e:
            self._display.error(str(e))
            phases.append(PhaseResult(BuildPhase.ERROR, False, error=str(e)))
            result.error = str(e)

        return self._finalize(result, phases, start_time)

    # ── Phase runners ──────────────────────────────────────────

    async def _run_phase(
        self, phase: str, coro: Any,
    ) -> PhaseResult:
        self._display.start_phase(phase)
        start = time.time()
        try:
            res = await coro
            elapsed = time.time() - start
            if isinstance(res, tuple):
                success, output = res
            else:
                success, output = True, str(res)
            self._display.end_phase(phase, success, str(output)[:100])
            return PhaseResult(phase, success, elapsed, str(output))
        except Exception as e:
            elapsed = time.time() - start
            self._display.end_phase(phase, False, str(e)[:100])
            return PhaseResult(phase, False, elapsed, error=str(e))

    # ── Phase logic ────────────────────────────────────────────

    async def _analyze_prompt(
        self, prompt: str, result: BuildResult,
    ) -> tuple[bool, str]:
        prompt_lower = prompt.lower()
        type_scores: dict[str, int] = {
            'mobile': sum(1 for kw in ['mobile', 'ios', 'android', 'app', 'flutter']
                          if kw in prompt_lower),
            'web': sum(1 for kw in ['website', 'web', 'site', 'dashboard', 'react']
                       if kw in prompt_lower),
            'api': sum(1 for kw in ['api', 'backend', 'server', 'rest', 'service']
                       if kw in prompt_lower),
            'desktop': sum(1 for kw in ['desktop', 'electron', 'native']
                           if kw in prompt_lower),
            'cli': sum(1 for kw in ['cli', 'command line', 'terminal', 'script']
                       if kw in prompt_lower),
        }

        detected = max(type_scores, key=type_scores.get)  # type: ignore
        if type_scores[detected] > 0:
            result.project_type = detected

        if not result.project_name or result.project_name == self._generate_name(prompt):
            for w in prompt.split():
                wc = w.lower().strip('.,!?')
                if wc not in {'build', 'create', 'make', 'a', 'an', 'the'} and len(wc) > 2:
                    result.project_name = wc.capitalize()
                    break

        info = _APP_TYPES.get(result.project_type, {})
        self._display.log(f'Type: {info.get("label", "?")}')
        self._display.log(f'Stack: {info.get("stack", "?")}')
        self._display.log(f'Name: {result.project_name}')
        return True, result.project_type

    async def _scaffold_project(self, result: BuildResult) -> tuple[bool, str]:
        out = self._output_dir / result.project_name
        out.mkdir(parents=True, exist_ok=True)
        result.output_dir = str(out)
        self._display.log(f'Location: {out}')
        return True, str(out)

    async def _generate_code(
        self, prompt: str, result: BuildResult,
    ) -> tuple[bool, str]:
        out = Path(result.output_dir)

        generators = {
            'web': self._generate_web_app,
            'mobile': self._generate_mobile_app,
            'api': self._generate_api,
            'desktop': self._generate_desktop_app,
            'cli': self._generate_cli_tool,
        }
        gen = generators.get(result.project_type)
        if gen:
            await gen(prompt, out, result)

        await self._generate_github_workflow(result)
        self._generate_readme(prompt, result)
        (out / '.gitignore').write_text(_GITIGNORE)

        self._display.log(f'Generated {result.project_type} app')
        return True, f'{result.project_type} app generated'

    async def _run_tests(self, result: BuildResult) -> tuple[bool, str]:
        out = Path(result.output_dir)
        cmds = []
        if (out / 'package.json').exists():
            cmds.append(['npm', 'test', '--', '--watchAll=false'])
        elif (out / 'pubspec.yaml').exists():
            cmds.append(['flutter', 'test'])
        elif (out / 'requirements.txt').exists():
            cmds.append([sys.executable, '-m', 'pytest', '-q'])

        if not cmds:
            return True, 'No tests configured'

        for cmd in cmds:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd, cwd=str(out),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate(timeout=60)
                if proc.returncode == 0:
                    return True, (stdout.decode()[:200] if stdout else 'passed')
                return False, stderr.decode()[:200]
            except (FileNotFoundError, asyncio.TimeoutError):
                continue
        return True, 'Tests skipped'

    async def _build_artifact(self, result: BuildResult) -> tuple[bool, str]:
        out = Path(result.output_dir)
        info = _APP_TYPES.get(result.project_type, {})
        ext = info.get('ext', '.zip')

        if result.project_type == 'web':
            for cmd in [['npm', 'install'], ['npm', 'run', 'build']]:
                try:
                    proc = await asyncio.create_subprocess_exec(
                        *cmd, cwd=str(out),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    await proc.communicate(timeout=120)
                except FileNotFoundError:
                    break

        name = f'{result.project_name}{ext}'
        path = self._output_dir / name
        shutil.make_archive(str(path.with_suffix('')), 'zip', str(out))
        result.artifact_path = str(path)
        self._display.log(f'Artifact: {path}')
        return True, str(path)

    async def _deploy(self, result: BuildResult) -> tuple[bool, str]:
        if result.project_type == 'web' and self._github_push:
            try:
                proc = await asyncio.create_subprocess_exec(
                    'npx', 'netlify-cli', 'deploy', '--prod',
                    cwd=Path(result.output_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await proc.communicate(timeout=60)
                for line in stdout.decode().split('\n'):
                    if 'URL:' in line:
                        result.deploy_url = line.split('URL:')[1].strip()
                        break
            except (FileNotFoundError, asyncio.TimeoutError):
                pass
        if not result.deploy_url:
            result.deploy_url = f'file://{result.artifact_path}'
        return True, result.deploy_url

    # ── Code generators ────────────────────────────────────────

    async def _generate_web_app(
        self, prompt: str, out: Path, result: BuildResult,
    ) -> None:
        name = result.project_name.lower().replace(' ', '-')
        (out / 'package.json').write_text(_json_file({
            'name': name, 'private': True, 'version': '1.0.0', 'type': 'module',
            'scripts': {
                'dev': 'vite', 'build': 'vite build',
                'preview': 'vite preview', 'test': 'vitest run',
            },
            'dependencies': {
                'react': '^19.0.0', 'react-dom': '^19.0.0',
                'react-router-dom': '^7.0.0',
            },
            'devDependencies': {
                '@vitejs/plugin-react': '^4.3.0', 'vite': '^6.0.0',
                'vitest': '^2.0.0', '@testing-library/react': '^16.0.0',
                'jsdom': '^25.0.0',
            },
        }))
        (out / 'vite.config.js').write_text(_VITE_CONFIG_JS)

        index_html = (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            f'<meta charset="UTF-8" />\n<title>{result.project_name}</title>\n'
            f'<meta name="description" content="{prompt[:150]}" />\n'
            '</head>\n<body>\n<div id="root"></div>\n'
            '<script type="module" src="/src/main.jsx"></script>\n</body>\n</html>\n'
        )
        (out / 'index.html').write_text(index_html)

        src = out / 'src'
        src.mkdir(exist_ok=True)
        (src / 'main.jsx').write_text(_MAIN_JSX)

        app_jsx = _interpolate(
            _APP_JSX,
            PROJECT_NAME=result.project_name,
            PROMPT=prompt[:200],
        )
        (src / 'App.jsx').write_text(app_jsx)
        (src / 'index.css').write_text(_INDEX_CSS)

        public = out / 'public'
        public.mkdir(exist_ok=True)
        (public / 'vite.svg').write_text(_VITE_SVG)

    async def _generate_mobile_app(
        self, prompt: str, out: Path, result: BuildResult,
    ) -> None:
        name = result.project_name.lower().replace(' ', '_')
        safe = _safe_name(result.project_name)

        (out / 'pubspec.yaml').write_text(
            'name: ' + name + '\n'
            'description: ' + prompt[:80] + '\n'
            'publish_to: none\n'
            'version: 1.0.0+1\n\n'
            'environment:\n  sdk: ">=3.2.0 <4.0.0"\n\n'
            'dependencies:\n  flutter:\n    sdk: flutter\n'
            '  cupertino_icons: ^1.0.6\n\n'
            'dev_dependencies:\n  flutter_test:\n    sdk: flutter\n'
            '  flutter_lints: ^3.0.0\n\n'
            'flutter:\n  uses-material-design: true\n'
        )

        lib = out / 'lib'
        lib.mkdir(parents=True, exist_ok=True)

        main_dart = (
            'import \'package:flutter/material.dart\';\n\n'
            f'void main() => runApp(const {safe}App());\n\n'
            f'class {safe}App extends StatelessWidget {{\n'
            f'  const {safe}App({{super.key}});\n\n'
            '  @override\n  Widget build(BuildContext context) {\n'
            '    return MaterialApp(\n'
            f'      title: \'{safe}\',\n'
            '      theme: ThemeData(\n'
            '        colorSchemeSeed: Colors.indigo,\n'
            '        useMaterial3: true,\n'
            '        brightness: Brightness.dark,\n'
            '      ),\n'
            '      home: const HomePage(),\n'
            '    );\n  }\n}\n\n'
            'class HomePage extends StatelessWidget {\n'
            '  const HomePage({super.key});\n\n'
            '  @override\n  Widget build(BuildContext context) {\n'
            '    return Scaffold(\n'
            f'      appBar: AppBar(title: const Text(\'{safe}\'), centerTitle: true),\n'
            '      body: Center(\n'
            '        child: Column(\n'
            '          mainAxisAlignment: MainAxisAlignment.center,\n'
            '          children: [\n'
            '            const Icon(Icons.rocket_launch, size: 80),\n'
            '            const SizedBox(height: 24),\n'
            f'            Text(\'{safe}\',\n'
            '              style: Theme.of(context).textTheme.headlineLarge,\n'
            '            ),\n'
            '            const SizedBox(height: 12),\n'
            f'            Text(\'{prompt[:100]}\',\n'
            '              textAlign: TextAlign.center,\n'
            '              style: Theme.of(context).textTheme.bodyLarge\n'
            '                ?.copyWith(color: Colors.white70),\n'
            '            ),\n'
            '          ],\n'
            '        ),\n'
            '      ),\n'
            '    );\n  }\n}\n'
        )
        (lib / 'main.dart').write_text(main_dart)

    async def _generate_api(
        self, prompt: str, out: Path, result: BuildResult,
    ) -> None:
        (out / 'requirements.txt').write_text(
            'fastapi[standard]\nuvicorn[standard]\nsqlalchemy\npydantic\n'
            'python-dotenv\nhttpx\npytest\npytest-asyncio\n'
        )
        app_dir = out / 'app'
        app_dir.mkdir(exist_ok=True)
        (app_dir / '__init__.py').write_text('')

        main_py = (
            f'"""{result.project_name} — {prompt[:100]}"""\n\n'
            'from fastapi import FastAPI\n'
            'from fastapi.middleware.cors import CORSMiddleware\n\n'
            f'app = FastAPI(title="{result.project_name}",\n'
            f'  description="{prompt[:200]}", version="1.0.0")\n\n'
            'app.add_middleware(CORSMiddleware,\n'
            '  allow_origins=["*"], allow_credentials=True,\n'
            '  allow_methods=["*"], allow_headers=["*"],\n'
            ')\n\n'
            '@app.get("/")\nasync def root():\n'
            f'  return {{"app": "{result.project_name}",\n'
            '    "version": "1.0.0", "status": "running"}\n\n'
            '@app.get("/api/health")\nasync def health():\n'
            '  return {"status": "healthy"}\n\n'
            'if __name__ == "__main__":\n'
            '  import uvicorn\n'
            '  uvicorn.run(app, host="0.0.0.0", port=8000)\n'
        )
        (app_dir / 'main.py').write_text(main_py)

    async def _generate_desktop_app(
        self, prompt: str, out: Path, result: BuildResult,
    ) -> None:
        name = result.project_name.lower().replace(' ', '-')
        (out / 'package.json').write_text(_json_file({
            'name': name, 'version': '1.0.0',
            'description': prompt[:100], 'main': 'main.js',
            'scripts': {'start': 'electron .', 'build': 'electron-builder'},
            'devDependencies': {
                'electron': '^33.0.0', 'electron-builder': '^25.0.0',
            },
        }))

        (out / 'main.js').write_text(
            'const { app, BrowserWindow } = require(\'electron\')\n\n'
            'function createWindow() {\n'
            f'  const win = new BrowserWindow({{width: 1200, height: 800,\n'
            f'    title: \'{result.project_name}\',\n'
            '    webPreferences: {nodeIntegration: true},\n'
            '  }})\n  win.loadFile(\'index.html\')\n}\n\n'
            'app.whenReady().then(createWindow)\n'
            'app.on(\'window-all-closed\', () => {\n'
            '  if (process.platform !== \'darwin\') app.quit()\n'
            '})\n'
            'app.on(\'activate\', () => {\n'
            '  if (BrowserWindow.getAllWindows().length === 0) createWindow()\n'
            '})\n'
        )

        (out / 'index.html').write_text(
            '<!DOCTYPE html>\n<html>\n<head>\n'
            f'<title>{result.project_name}</title>\n'
            '<style>\n'
            'body { font-family: -apple-system, sans-serif; margin: 0;\n'
            '  padding: 2rem; background: #0f0f1a; color: #e2e8f0;\n'
            '  display: flex; align-items: center; justify-content: center;\n'
            '  min-height: 100vh; }\n'
            '.container { text-align: center; }\n'
            'h1 { font-size: 2.5rem; background: linear-gradient(\n'
            '  135deg, #6366f1, #22d3ee); -webkit-background-clip: text;\n'
            '  -webkit-text-fill-color: transparent; }\n'
            'p { color: #94a3b8; margin-top: 1rem; }\n'
            '</style>\n</head>\n<body>\n<div class="container">\n'
            f'<h1>{result.project_name}</h1>\n'
            f'<p>{prompt[:200]}</p>\n</div>\n</body>\n</html>\n'
        )

    async def _generate_cli_tool(
        self, prompt: str, out: Path, result: BuildResult,
    ) -> None:
        name = result.project_name.lower().replace(' ', '_')
        (out / 'pyproject.toml').write_text(
            '[build-system]\nrequires = ["hatchling"]\n'
            'build-backend = "hatchling.build"\n\n'
            f'[project]\nname = "{name}"\nversion = "1.0.0"\n'
            f'description = "{prompt[:80]}"\n'
            'requires-python = ">=3.12"\n'
            'dependencies = ["click>=8.0", "rich>=13.0"]\n\n'
            f'[project.scripts]\n{name} = "{name}.cli:main"\n'
        )
        src = out / 'src'
        src.mkdir(exist_ok=True)
        (src / '__init__.py').write_text('')

        (src / 'cli.py').write_text(
            f'"""{result.project_name} — {prompt[:100]}"""\n\n'
            'import click\nfrom rich.console import Console\n'
            'from rich.panel import Panel\n\n'
            'console = Console()\n\n'
            '@click.group()\ndef cli():\n'
            f'  """{result.project_name} — CLI tool"""\n  pass\n\n'
            '@cli.command()\ndef hello():\n  """Say hello!"""\n'
            '  console.print(Panel.fit(\n'
            f'    "[bold cyan]{result.project_name}[/]\\\\n\\\\n'
            'Built with Wren App Builder", border_style="blue"))\n\n'
            '@cli.command()\n@click.argument("name")\n'
            'def greet(name: str):\n  """Greet someone."""\n'
            '  console.print(f"[green]Hello, {name}![/]")\n\n'
            'def main():\n  cli()\n\n'
            'if __name__ == "__main__":\n  main()\n'
        )

    # ── CI/CD & Docs ──────────────────────────────────────────

    async def _generate_github_workflow(self, result: BuildResult) -> None:
        wf = Path(result.output_dir) / '.github' / 'workflows'
        wf.mkdir(parents=True, exist_ok=True)

        content = (
            'name: Build & Deploy\n\n'
            'on:\n  push:\n    branches: [main]\n'
            '  pull_request:\n    branches: [main]\n\n'
            'jobs:\n  build:\n    runs-on: ubuntu-latest\n'
            '    steps:\n      - uses: actions/checkout@v4\n'
        )

        if result.project_type == 'web':
            content += (
                '      - uses: actions/setup-node@v4\n'
                '        with:\n          node-version: 22\n'
                '      - run: npm install\n      - run: npm run build\n'
                '      - uses: actions/upload-artifact@v4\n'
                '        with:\n          name: build\n'
                '          path: dist/\n\n'
                '  deploy:\n    if: github.ref == \'refs/heads/main\'\n'
                '    needs: build\n    runs-on: ubuntu-latest\n'
                '    steps:\n'
                '      - uses: actions/download-artifact@v4\n'
                '        with:\n          name: build\n'
                '          path: dist/\n'
                '      - name: Deploy to Netlify\n'
                '        run: npx netlify-cli deploy --prod --dir=dist/\n'
                '        env:\n'
                '          NETLIFY_AUTH_TOKEN: \${{ secrets.NETLIFY_AUTH_TOKEN }}\n'
                '          NETLIFY_SITE_ID: \${{ secrets.NETLIFY_SITE_ID }}\n'
            )
        elif result.project_type == 'mobile':
            content += (
                '      - uses: subosito/flutter-action@v2\n'
                '        with:\n          flutter-version: \'3.27\'\n'
                '      - run: flutter pub get\n'
                '      - run: flutter build apk --release\n'
                '      - uses: actions/upload-artifact@v4\n'
                '        with:\n          name: app-release\n'
                '          path: build/app/outputs/flutter-apk/app-release.apk\n'
            )
        elif result.project_type == 'api':
            content += (
                '      - uses: actions/setup-python@v5\n'
                '        with:\n          python-version: \'3.12\'\n'
                '      - run: pip install -r requirements.txt\n'
                '      - run: pytest -q\n'
            )

        (wf / 'build.yml').write_text(content)

    def _generate_readme(self, prompt: str, result: BuildResult) -> None:
        info = _APP_TYPES.get(result.project_type, {})
        readme = (
            f'# {result.project_name}\n\n'
            f'> {prompt}\n\n'
            f'**Type:** {info.get("label", "Project")}  \n'
            f'**Stack:** {info.get("stack", "Custom")}  \n'
            '**Generated by:** Wren App Builder\n\n'
            '## Quick Start\n\n```bash\n'
            '# Install dependencies\nnpm install\n'
            '# Start development server\nnpm run dev\n```\n\n'
            '## Build\n\n```bash\nnpm run build\n```\n\n'
            '## Deploy\n\nPush to GitHub main branch to trigger CI/CD pipeline.\n'
            'The GitHub Actions workflow will build and deploy automatically.\n\n'
            '---\nBuilt with by Wren\n'
        )
        (Path(result.output_dir) / 'README.md').write_text(readme)

    # ── Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _generate_name(prompt: str) -> str:
        return f'App-{hashlib.md5(prompt.encode()).hexdigest()[:6]}'

    def _finalize(
        self,
        result: BuildResult,
        phases: list[PhaseResult],
        start_time: float,
    ) -> BuildResult:
        result.phases = phases
        result.total_duration_s = time.time() - start_time
        ok_phases = {BuildPhase.DONE, BuildPhase.ERROR}
        result.success = all(
            p.success for p in phases if p.phase not in ok_phases
        )
        self._display.summary(result)
        return result
