<div align="center">
  <picture>
    <source srcset="./assets/logo-320.webp" type="image/webp">
    <img src="./logo.png" alt="Wren" width="280" style="max-width:45%;height:auto;">
  </picture>

  <h1 align="center">Wren</h1>
  <p align="center">
    <strong>AI Engineering Platform — Self-hosted. Private. Your models, your data.</strong>
  </p>

  <p align="center">
    <a href="#quick-start"><strong>Quick Start</strong></a> ·
    <a href="#features"><strong>Features</strong></a> ·
    <a href="#architecture"><strong>Architecture</strong></a> ·
    <a href="#configuration"><strong>Configuration</strong></a> ·
    <a href="#development"><strong>Development</strong></a>
  </p>

  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.12%2B-blue?logo=python" alt="Python 3.12+">
    <img src="https://img.shields.io/badge/Node-22%2B-green?logo=node.js" alt="Node 22+">
    <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT License">
    <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react" alt="React 19">
    <img src="https://img.shields.io/badge/Status-Production_Ready-brightgreen" alt="Production Ready">
  </p>
</div>

---

## Overview

**Wren** is a professional, self-hosted AI engineering platform that brings agentic coding, review, and execution into a unified workspace. It combines a Monaco-based IDE, real-time terminal, and multi-LLM chat with a powerful agent orchestration system — all running on your own infrastructure.

Unlike cloud-based AI coding tools, Wren keeps your code and data private. Connect your own LLM provider, run agents locally or in sandboxed containers, and own every part of the pipeline.

---

## Quick Start

### Prerequisites

- **Python 3.12+** and **Poetry** for the backend
- **Node.js 22+** and **npm** for the frontend
- **Docker** (optional, for sandboxed agent execution)

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/Daniel-debug-boop/Wren.git
cd Wren

# Build everything (frontend + backend)
make build

# Run locally (without Docker)
export INSTALL_DOCKER=0 RUNTIME=local
make run FRONTEND_PORT=12000 FRONTEND_HOST=0.0.0.0 BACKEND_HOST=0.0.0.0
```

Open **http://localhost:12000** in your browser and start building.

### Running the Frontend Standalone

```bash
cd frontend
npm install
npm run dev          # Development mode
npm run build        # Production build
```

### Running the Backend Standalone

```bash
poetry install
make start-backend   # Starts on port 3000
```

---

## Features

### AI Agentic Workflows
- **Multi-agent orchestration** — coordinate specialized agents for complex tasks
- **Human-in-the-loop** — review, approve, and guide agent actions in real time
- **44+ installed skills** — code review, debugging, refactoring, testing, and more
- **Custom skills** — extend Wren with your own agent capabilities

### Built-in Development Environment
- **Monaco Editor** — full-featured code editor with syntax highlighting, IntelliSense, and multi-file editing
- **Integrated terminal** — xterm.js powered terminal for running commands
- **File explorer** — browse, create, and manage project files
- **Git integration** — clone repositories, manage branches, and commit from within the IDE

### Multi-LLM Support
- **OpenAI, Anthropic, OpenRouter, and any OpenAI-compatible API** — bring your own provider
- **Per-task model routing** — use cheap models for simple tasks, powerful models for complex reasoning
- **Configurable parameters** — temperature, max tokens, reasoning effort, and more

### Enterprise-Ready
- **Self-hosted** — zero data leaves your infrastructure
- **Docker/VM sandboxing** — execute untrusted code in isolated environments
- **Kubernetes support** — scale agents across clusters
- **Role-based access** — manage users and permissions

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Browser (UI)                    │
│         React 19 + React Router v8 SSR          │
└──────────────────┬──────────────────────────────┘
                   │ HTTP / WebSocket
                   ▼
┌─────────────────────────────────────────────────┐
│              Python Backend (FastAPI)            │
│         Port 3000 · Uvicorn · Poetry            │
├──────────────────────┬──────────────────────────┤
│   Agent Orchestrator │   LLM Gateway (LiteLLM)  │
│   Session Manager    │   Skills Registry        │
│   Git Provider       │   Sandbox Controller     │
└──────────────────────┴──────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, TypeScript, React Router v8 (SSR), Tailwind CSS 4, Framer Motion, TanStack Query, Zustand |
| **Backend** | Python 3.12+, FastAPI, Uvicorn, LiteLLM, Pydantic |
| **Runtime** | Docker / Local, tmux for process management |
| **Database** | PickleDB (embedded), optional PostgreSQL via asyncpg |
| **Editors** | Monaco Editor, xterm.js |
| **Testing** | Vitest (frontend), pytest (backend), Playwright (e2e) |

---

## Configuration

### Quick Start: Production .env

The app uses environment variables for all configuration. Set these in your shell or `.env` file before starting:

```bash
# ── LLM Provider ───────────────────────────────────────
LLM_API_KEY="sk-or-v1-xxxxxxxx"    # Auto-detects provider (OpenAI, Anthropic, Groq, etc.)
LLM_MODEL="openrouter/auto"        # Default model
LLM_BASE_URL=""                     # Custom base URL (auto-detected otherwise)

# ── Server ──────────────────────────────────────────────
BACKEND_HOST="0.0.0.0"             # Bind address (0.0.0.0 for production)
BACKEND_PORT=3000                    # Backend port
FRONTEND_HOST="0.0.0.0"
FRONTEND_PORT=3001                   # Frontend port

# ── Runtime ─────────────────────────────────────────────
INSTALL_DOCKER=0                     # 0 = no Docker needed
RUNTIME=local                        # local | docker | kubernetes
WORKSPACE_BASE="./workspace"         # Project output directory

# ── Features ────────────────────────────────────────────
ENABLE_BILLING=false                 # false = free mode
ENABLE_AUTH=false                    # false = no login required
ENABLE_OMNIROUTE=true                # true = intelligent LLM routing
ENABLE_COMPRESSION=true              # true = auto token compression
```

### config.toml (Advanced)

For advanced configuration, create a `config.toml` in the project root:

```toml
[core]
workspace_base = "./workspace"

[llm]
model = "openrouter/auto"
api_key = "sk-or-v1-..."
base_url = "https://openrouter.ai/api/v1"

[sandbox]
base_container_image = "wren-sandbox:latest"
timeout = 300
```

---

## Development

### Commands

```bash
make build              # Build everything
make run                # Run full stack
make start-backend      # Backend only
make start-frontend     # Frontend only
make lint               # Run all linters
make test               # Run all tests
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev             # Dev server with hot reload
npm run build           # Production build (370ms, 27KB CSS gzip'd to 6KB)
npm run test            # Run vitest tests
npm run lint:fix        # Fix lint issues
```

### Backend Development

```bash
poetry install
poetry shell            # Activate virtual environment
make start-backend      # Starts uvicorn on port 3000
poetry run pytest       # Run Python tests
```

### Verifying Production Readiness

```bash
# Frontend
cd frontend && npx tsc --noEmit    # TypeScript check (0 errors ✓)
npm run build                       # Production bundle

# Backend
curl http://localhost:3000/api/v1/alive   # Health check → {"status":"ok","version":"1.0.0"}

# OmniRoute
curl http://localhost:3000/api/v1/omniroute/status   # Full routing status
```

---

## Deployment

### Docker (Recommended for Production)

```bash
docker compose up -d
```

This uses the multi-stage Dockerfile at `containers/app/Dockerfile` — builds frontend with Node then backend with Python in a slim production image.

### Standalone Production

```bash
# Terminal 1: Backend
poetry run uvicorn wren.server.listen:app --host 0.0.0.0 --port 3000

# Terminal 2: Frontend
cd frontend && npm run build && node server.js
```

### Production Checklist

| Check | Command | Expected |
|-------|---------|----------|
| TypeScript | `cd frontend && npx tsc --noEmit` | `EXIT:0` |
| Frontend build | `cd frontend && npm run build` | `✓ built in <1s` |
| Backend health | `curl localhost:3000/api/v1/alive` | `{"status":"ok"}` |
| OmniRoute | `curl localhost:3000/api/v1/omniroute/status` | `{"initialized":true,...}` |
| Docker | `docker compose build` | Builds successfully |

---

## Project Structure

```
Wren/
├── frontend/              # React 19 + TypeScript SSR app
│   ├── src/
│   │   ├── routes/        # Home, Generate, Chat, Settings, API Keys, Skills, Orchestrate
│   │   ├── api/           # API client layer (fetch wrappers)
│   │   └── index.css      # Design system tokens (amber accent, dark theme)
│   ├── build/             # Production build output (client + SSR)
│   └── public/            # Static assets, manifest, favicons, PWA service worker
├── wren/                  # Python backend (FastAPI + OmniRoute)
│   ├── app_server/        # FastAPI application with routers
│   ├── app_builder/       # Dual pipeline: Automated 3-stage + Multi-agent 5-stage
│   ├── omniroute/         # Intelligent AI routing (250+ providers, 18 strategies)
│   └── cli/               # CLI tools and app builder
├── wren-sdk/              # Python SDK for agent development
├── wren-android/          # Native Android APK (Kotlin + Chaquopy Python)
│   ├── app/               # Compose UI, WebView, Service, BootReceiver
│   └── build.gradle.kts   # SDK 35, minSdk 26, arm64 + x86_64
├── tests/                 # 50+ Python unit tests (pytest)
├── android/               # APK build script (TWA + Termux)
├── termux/                # Android Termux launcher
├── containers/            # Dockerfiles for app, dev, harness
├── skills/                # 44+ agent skill definitions
├── .github/workflows/     # 11 CI workflows (lint, test, PR, e2e)
└── config.toml            # Advanced configuration
```

---

## Android APK — Build Your Own Installable App

The project includes a **native Android app** built with Kotlin + Jetpack Compose + Chaquopy (embedded Python runtime).

### Features
- **One-tap install** — APK includes everything, no setup
- **Background server** — Python server runs as foreground service
- **Auto-start** — Server starts on phone boot
- **Job notifications** — Get notified when your project is ready
- **Settings UI** — Configure LLM API key and model from the app
- **WebView UI** — Full Wren chat interface embedded

### Build the APK (on your computer)

**Prerequisites:**
- **Android Studio** (latest, free from [developer.android.com](https://developer.android.com/studio))
- **Android SDK 35** (bundled with Android Studio)
- **Linux, macOS, or Windows with WSL**

**Step-by-step:**

```bash
# 1. Clone the repository
cd ~
git clone https://github.com/Daniel-debug-boop/Wren.git
cd Wren

# 2. Build the frontend production bundle (needed by Android)
cd frontend
npm install && npm run build
cd ..

# 3. Build the Android APK
cd wren-android

# Option A: Using the build script (recommended)
# First time: Open wren-android/ in Android Studio → File → Open
# Then: Build → Build Bundle(s) / APK(s) → Build APK(s)

# Option B: Command-line (requires ANDROID_HOME set)
export ANDROID_HOME=$HOME/Android/Sdk
./gradlew assembleDebug

# 4. Find your APK
find . -name "*.apk"
# → app/build/outputs/apk/debug/app-debug.apk

# 5. Install on phone
# Transfer the APK to your phone and tap to install
# Enable "Install from unknown sources" in Settings if needed
```

**Release APK (for Play Store):**

```bash
# 1. Generate a keystore
keytool -genkey -v -keystore release-keystore.jks \
  -alias wren -keyalg RSA -keysize 2048 -validity 10000

# 2. Set signing config in build.gradle.kts
#    (uncomment the signingConfig block)

# 3. Build signed release APK
cd wren-android
export KEYSTORE_PASSWORD="your-password"
export KEY_ALIAS="wren"
export KEY_PASSWORD="your-password"
./gradlew assembleRelease

# 4. APK ready for Play Store upload
# → app/build/outputs/apk/release/app-release.apk
```

**APK size:** ~150MB (includes Python runtime + dependencies)
**Minimum Android:** 8.0 (API 26)
**Architecture:** ARM64 (phones) + x86_64 (emulator)

### Android Technical Architecture

```
Android App (Kotlin + Jetpack Compose)
├── BootstrapActivity   → First-launch setup screen with progress
├── MainActivity        → WebView loading http://127.0.0.1:12000
├── WrenService         → Foreground service keeping server alive
├── ServerManager       → Starts Python backend via Chaquopy
├── BootReceiver        → Auto-starts server on phone boot
└── SettingsActivity    → LLM config, model selection, port
         │
         ▼ (via Chaquopy)
Python Backend (embedded in APK)
├── FastAPI (uvicorn)
├── OmniRoute (routing engine)
└── App Builder (3-stage pipeline)
```

---

## Contributing

Contributions are welcome! Please read our guidelines:

1. **Fork** the repository and create a feature branch
2. **Run pre-commit hooks** before committing
3. **Write tests** for new functionality
4. **Keep changes focused** — one feature per PR
5. **Open a Pull Request** describing your changes and rationale

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

### Code of Conduct

This project follows a [Code of Conduct](./CODE_OF_CONDUCT.md). By participating, you agree to maintain a respectful and inclusive community.

---

## Community & Support

- **Issues** — [GitHub Issues](https://github.com/Daniel-debug-boop/Wren/issues)
- **Discussions** — [GitHub Discussions](https://github.com/Daniel-debug-boop/Wren/discussions)
- **Changelog** — See [CHANGELOG.md](./CHANGELOG.md) for release notes
- **Android** — APK builds available in `wren-android/` directory

---

## License

**MIT License** — see [LICENSE](./LICENSE) for details.

Copyright © 2024-2026 Daniel and contributors.

---

<p align="center">
  <sub>Built with ❤️ for developers who value privacy and control over their AI tools.</sub>
</p>
