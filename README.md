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

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_API_KEY` | API key for your LLM provider | — |
| `LLM_MODEL` | Default model (e.g., `gpt-4o`, `claude-sonnet-4`) | `gpt-4o` |
| `LLM_BASE_URL` | Custom API base URL for OpenAI-compatible providers | — |
| `WORKSPACE_DIR` | Path for agent project files | `./workspace` |
| `FRONTEND_PORT` | Frontend dev server port | `3001` |
| `BACKEND_HOST` | Backend server host | `127.0.0.1` |
| `BACKEND_PORT` | Backend server port | `3000` |
| `INSTALL_DOCKER` | Set to `0` to skip Docker checks | `1` |
| `RUNTIME` | Execution runtime (`local`, `docker`, `kubernetes`) | `docker` |

### config.toml

For advanced configuration, create a `config.toml` in the project root:

```toml
[core]
workspace_base = "./workspace"

[llm]
model = "gpt-4o"
api_key = "sk-..."
base_url = "https://api.openai.com/v1"

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
npm run dev             # Dev server with hot reload
npm run dev:mock        # Mock mode (no backend needed)
npm run build           # Production build
npm run test            # Run tests
npm run lint:fix        # Fix lint issues
```

### Backend Development

```bash
poetry shell            # Activate virtual environment
poetry run pytest       # Run tests
make lint-backend       # Lint Python code
```

### Pre-commit Hooks

```bash
make install-pre-commit-hooks
```

---

## Deployment

### Docker (Recommended for Production)

```bash
docker compose up -d
```

### Kubernetes

See `kind/` directory for local Kubernetes manifests and `containers/dev/` for development containers.

### Production Build

```bash
cd frontend
npm run build
npx react-router-serve build/server/index.js
```

---

## Project Structure

```
Wren/
├── frontend/              # React SPA + SSR
│   ├── src/
│   │   ├── routes/        # Page components
│   │   ├── components/    # Shared UI components
│   │   ├── api/           # API client layer
│   │   ├── hooks/         # React hooks (queries, mutations)
│   │   └── stores/        # Zustand state stores
│   ├── build/             # Production build output
│   └── package.json
├── wren/                  # Python backend
│   ├── app_server/        # FastAPI application
│   ├── llm/               # LLM integration (LiteLLM)
│   └── sandbox/           # Execution sandbox
├── wren-sdk/              # Python SDK for agent development
├── wren-ui/               # Shared UI component library
├── wren-android/          # Android APK build
├── tests/                 # Backend tests
├── termux/                # Android Termux launcher
└── skills/                # Agent skill definitions
```

---

## Android Support

Wren can run on Android devices via Termux:

```bash
# On your Android phone (Termux)
pkg install git
git clone https://github.com/Daniel-debug-boop/Wren.git
cd Wren
bash termux/bootstrap.sh
bash termux/start.sh
```

See [termux/termux-setup.md](./termux/termux-setup.md) for detailed instructions.

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

---

## License

**MIT License** — see [LICENSE](./LICENSE) for details.

Copyright © 2024-2025 Daniel and contributors.

---

<p align="center">
  <sub>Built with ❤️ for developers who value privacy and control over their AI tools.</sub>
</p>
