<div align="center">
  <picture>
    <source srcset="./assets/logo-320.webp" type="image/webp">
    <img src="./logo.png" alt="Wren" width="280" style="max-width:45%;height:auto;">
  </picture>

  <h1 align="center">Wren</h1>
  <p align="center">
    <strong>AI Engineering Platform. Self-hosted. Your models, your code.</strong>
  </p>

  <p align="center">
    <a href="#quick-start"><strong>Quick Start</strong></a> ·
    <a href="#features"><strong>Features</strong></a> ·
    <a href="#architecture"><strong>Architecture</strong></a> ·
    <a href="#docker"><strong>Docker</strong></a> ·
    <a href="#development"><strong>Development</strong></a>
  </p>

  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.12%2B-blue?logo=python" alt="Python 3.12+">
    <img src="https://img.shields.io/badge/Node-22%2B-green?logo=node.js" alt="Node 22+">
    <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT License">
    <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react" alt="React 19">
  </p>
</div>

---

## What is Wren?

Wren is a self-hosted AI engineering platform that combines an IDE, terminal, and LLM chat into a single workspace. Describe what you want to build, and Wren's AI pipeline architects, plans, writes, and reviews the code -- then writes the files to your workspace.

**Key capabilities that actually work:**

- **AI Chat** -- Real-time streaming responses from OpenAI, Anthropic, OpenRouter, or any OpenAI-compatible API
- **Code Generation Pipeline** -- 4-stage pipeline: Architect, Planner, Writer, Reviewer. Output is written as real files to your workspace
- **Interactive Terminal** -- Real PTY shell (bash/zsh) via xterm.js. Run commands, install packages, execute your code
- **Monaco Code Editor** -- Full VS Code editor with syntax highlighting for 16+ languages, IntelliSense, multi-file editing
- **File Explorer** -- Browse, read, and save files directly from the browser
- **Git Integration** -- Initialize repos, clone, commit, view status and diffs
- **Multi-LLM Support** -- Connect any OpenAI-compatible provider. Switch models per conversation
- **Self-hosted** -- Zero data leaves your infrastructure. Run locally or in Docker

## Quick Start

### Prerequisites

- **Python 3.12+** and **Poetry** for the backend
- **Node.js 22+** and **npm** for the frontend

### One-Command Setup

```bash
git clone https://github.com/Daniel-debug-boop/Wren.git
cd Wren

# Build everything (frontend + backend)
make build

# Run locally
export INSTALL_DOCKER=0 RUNTIME=local
make run FRONTEND_PORT=12000 FRONTEND_HOST=0.0.0.0 BACKEND_HOST=0.0.0.0
```

Open **http://localhost:12000** in your browser.

### Docker (Recommended)

```bash
docker compose up -d
```

Open **http://localhost:3000** -- everything runs in a single container.

## Docker

### Standalone Docker

```bash
docker build -t wren .
docker run -p 3000:3000 \
  -v $(pwd)/workspace:/workspace \
  -e WORKSPACE_BASE=/workspace \
  wren
```

### Docker Compose (Production)

```yaml
services:
  wren:
    build: .
    ports:
      - "3000:3000"
    volumes:
      - ./workspace:/workspace
    environment:
      - WORKSPACE_BASE=/workspace
      - WREN_CORS_ORIGINS=http://localhost:3000
    restart: unless-stopped
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKSPACE_BASE` | `./workspace` | Root directory for project files |
| `WREN_CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `ENABLE_DOCS` | `false` | Enable Swagger docs at `/docs` |
| `WREN_SHELL` | `/bin/bash` | Default shell for terminal |
| `PORT` | `3000` | Backend port |

## Architecture

```
Browser (React 19 + xterm.js + Monaco)
    |
    | HTTP / WebSocket
    |
Python Backend (FastAPI + Uvicorn)
    |
    +-- /ws            -> LLM streaming chat
    +-- /ws/terminal   -> Real PTY shell (xterm.js <-> pty module)
    +-- /api/v1/*      -> REST endpoints
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, TypeScript, React Router v8, Tailwind CSS 4, xterm.js 6, Monaco Editor |
| **Backend** | Python 3.12+, FastAPI, Uvicorn, Pydantic |
| **Terminal** | Python `pty` module, WebSocket, xterm.js with FitAddon |
| **Storage** | File-based JSON (`~/.wren/`) |
| **LLM** | OpenRouter API, OpenAI-compatible endpoints |
| **Testing** | Vitest (frontend), pytest (backend) |

## Features

### AI Generation Pipeline

Describe your project and Wren runs a 4-stage pipeline:

1. **Architect** -- Designs system architecture and component layout
2. **Planner** -- Creates ordered implementation steps with dependencies
3. **Writer** -- Generates production-quality code with error handling
4. **Reviewer** -- Reviews for bugs, security issues, and best practices

Generated code blocks are automatically extracted and written as real files to `workspace/generated/<task_id>/`.

### Real Interactive Terminal

Not a fake terminal -- a real pseudo-terminal (PTY) connected via WebSocket:

```bash
# These all work:
npm install react-router
python3 -m pytest tests/
git status
vim main.py
htop
```

- Window resize support (SIGWINCH)
- Full ANSI color support
- Tab completion, arrow keys, Ctrl+C
- Per-session process isolation

### Multi-LLM Provider

Connect any OpenAI-compatible API:

```bash
# Set your API key in Settings or via environment
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o
```

Supported providers: OpenAI, Anthropic (via OpenRouter), Groq, Together, Mistral, Ollama, LM Studio, vLLM, and any OpenAI-compatible endpoint.

## Configuration

### Backend Settings (via UI)

Navigate to Settings in the sidebar:

- **LLM Configuration** -- Model, API key, temperature, max tokens
- **LLM Profiles** -- Save and switch between different provider configs
- **Application** -- Language, theme, sandbox type
- **API Keys** -- Generate and manage API keys for programmatic access

### Backend Settings (via Environment)

```bash
# LLM
export LLM_API_KEY="sk-..."
export LLM_MODEL="openai/gpt-4o"
export LLM_BASE_URL=""  # Auto-detected, or set for custom providers

# Server
export BACKEND_HOST="0.0.0.0"
export BACKEND_PORT=3000
export FRONTEND_PORT=3001

# Features
export ENABLE_DOCS=false
export WREN_CORS_ORIGINS="http://localhost:3000"
```

## Development

### Commands

```bash
make build              # Build everything
make run                # Run full stack
make start-backend      # Backend only (port 3000)
make start-frontend     # Frontend only (port 5173)
make lint               # Run all linters
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev             # Dev server with hot reload
npm run build           # Production build
npm run test            # Run vitest tests
npm run typecheck       # TypeScript check
```

### Backend Development

```bash
poetry install
poetry shell
make start-backend      # Starts uvicorn on port 3000
poetry run pytest       # Run Python tests
```

### Running Tests

```bash
# Backend
poetry run pytest tests/unit/

# Frontend
cd frontend && npm run test
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/alive` | Health check |
| `GET` | `/api/v1/settings` | Get application settings |
| `POST` | `/api/v1/settings` | Update settings |
| `GET` | `/api/v1/conversations` | List conversations |
| `POST` | `/api/v1/conversations` | Create conversation |
| `POST` | `/api/v1/conversations/{id}/messages` | Send message |
| `POST` | `/api/v1/auto-generations` | Start generation pipeline |
| `GET` | `/api/v1/auto-generations/{id}/status` | Pipeline status |
| `GET` | `/api/v1/auto-generations/{id}/result` | Pipeline result |
| `POST` | `/api/v1/terminal/exec` | Execute shell command |
| `POST` | `/api/v1/terminal/run` | Run code snippet |
| `GET` | `/api/v1/workspace/tree` | File tree |
| `GET` | `/api/v1/workspace/file` | Read file |
| `PUT` | `/api/v1/workspace/file` | Write file |
| `GET` | `/api/v1/git/status` | Git status |
| `POST` | `/api/v1/git/init` | Init repo |
| `POST` | `/api/v1/git/clone` | Clone repo |
| `POST` | `/api/v1/git/commit` | Commit changes |
| `GET` | `/api/v1/skills` | List skills |
| `WS` | `/ws` | Chat WebSocket |
| `WS` | `/ws/terminal` | Terminal PTY WebSocket |

## Security Notes

- **CORS**: Restrict via `WREN_CORS_ORIGINS` in production
- **API Docs**: Disabled by default (`ENABLE_DOCS=true` to enable)
- **Terminal**: Commands are sandboxed with timeout and blocked dangerous commands
- **Workspace**: File paths are validated to prevent directory traversal
- **Error Handling**: Internal errors are not exposed to clients

## License

MIT License. See [LICENSE](LICENSE) for details.
