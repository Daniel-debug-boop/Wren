<div align="center">
  <img src="https://assets.wren.dev/logo-whitebackground.png" alt="Wren" width="280"/>
  <h1 align="center">Wren — AI Engineering Platform</h1>
  <p align="center">
    Self-host your AI coding agents. Chat, code, review, debug — all in one workspace.
    <br/>
    Bring your own LLM. Own your data. Own the workflow.
  </p>
  <p>
    <a href="#quickstart"><img src="https://img.shields.io/badge/Quickstart-000?style=for-the-badge" alt="Quickstart"/></a>
    <a href="#features"><img src="https://img.shields.io/badge/Features-000?style=for-the-badge" alt="Features"/></a>
    <a href="#architecture"><img src="https://img.shields.io/badge/Architecture-000?style=for-the-badge" alt="Architecture"/></a>
  </p>
  <br/>
</div>

---

## Quickstart

### Prerequisites

- **Node.js** 22.12.x or later
- **Python** 3.12+ with `uv` or `poetry`
- **Docker** (optional, for sandboxed agent execution)

### Launch

```bash
git clone https://github.com/Daniel-debug-boop/Wren.git
cd Wren
make build && make run
```

Open **[http://localhost:3001](http://localhost:3001)**.

### CLI

```bash
make run FRONTEND_PORT=3001 BACKEND_HOST=0.0.0.0
```

### Docker Sandbox

```bash
export PROJECTS_PATH="$HOME/projects"
mkdir -p "$PROJECTS_PATH" "$HOME/.wren"

docker run -it --rm \
  -p 8000:8000 \
  -v "$HOME/.wren:/home/wren/.wren" \
  -v "${PROJECTS_PATH}:/projects" \
  ghcr.io/wren/agent-canvas:latest
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | — | Your LLM provider API key |
| `LLM_MODEL` | `gpt-4o` | Default model |
| `WORKSPACE_DIR` | `./workspace` | Project workspace path |
| `ENABLE_V1` | `true` | Enable V1 application server |
| `FRONTEND_PORT` | `3001` | Frontend dev server port |

---

## Features

### Three Core Modes

| Mode | Purpose |
|------|---------|
| **Vibe Code** | Full agentic coding — chat, edit, run, repeat. Best for building apps from scratch. |
| **Autonomous** | Self-driving execution — agent plans, codes, and iterates with Working Memory + Lessons Learned, no hand-holding. |
| **Game** | Specialized mode for game development — scaffolding, asset wiring, and playable previews. |

Legacy modes (Plan, Code, Review, Debug, Ask) remain available for power users.

### Conversational Interface

- Chat with AI agents in natural language
- Real-time streaming responses via WebSocket
- Automatic mode suggestion based on your input
- Rich message bubbles with mode badges and action tags

### Built-in IDE Workspace

- **TopBar** — Wren logo, version badge, active mode badge, live agent status, and deploy button
- **FileTree** — real file explorer with tree/list views, edit & delete actions, live updates
- **Monaco Editor** — syntax highlighting, bracket matching, multi-cursor support, inline completions
- **Terminal** — live terminal with command history and bidirectional WebSocket communication
- **Resizable panes** — file tree, editor, terminal, and agent timeline

### Plan → Code → Review → Debug Pipeline

1. **Plan** — Agent analyses your request and presents a structured plan
2. **Code** — Agent implements the plan with file-by-file changes
3. **Review** — Review diffs, add comments, approve or reject changes
4. **Debug** — If errors occur, agent diagnoses and suggests fixes

### Bring Your Own LLM

- **OpenAI** (GPT-4o, o1, o3, etc.)
- **Anthropic** (Claude 3.5 Sonnet, Claude 3 Opus, etc.)
- **Mistral**, **Groq**, and custom endpoints
- Full control over model, temperature, max tokens, and reasoning effort

### Skills & Automation

- **44+ Skills** — Domain-specific prompts for tasks (React, Python, Docker, Godot, etc.)
- **Auto-triggering** — Skills activate based on context keywords
- **MCP Support** — Model Context Protocol for external tool integration
- **Working Memory** — Long-term context retention across sessions

### Privacy & Control

- **Self-hosted** — All data stays on your infrastructure
- **No telemetry** — Optional, transparent analytics
- **Your API keys** — No vendor lock-in to a single model provider
- **Sandboxed execution** — Docker isolation for agent runs

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │   Chat   │  │  Monaco  │  │  Review  │  │  Terminal  │  │
│  │ Interface│  │  Editor  │  │  Worksp. │  │  Emulator  │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────┘  │
│                       ↕ WebSocket / REST                    │
├─────────────────────────────────────────────────────────────┤
│                 Application Server (FastAPI)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Intent  │  │ Session  │  │   LLM    │  │  Skills  │   │
│  │  Router  │  │  Manager │  │  Router  │  │  Engine  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                       ↕ Internal IPC                         │
├─────────────────────────────────────────────────────────────┤
│              Agent Orchestrator (Harness)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Meta   │  │   Task   │  │  Working │  │  Vector  │   │
│  │Orchestr. │  │   Graph  │  │  Memory  │  │  Store   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│              Agent Backends (Sandbox/Docker/VM)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │  Docker  │  │   VM     │  │  Cloud   │                   │
│  │ Sandbox  │  │ Backend  │  │ Backend  │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Stack | Purpose |
|-----------|-------|---------|
| **Frontend** | React 19, TypeScript, Tailwind CSS, Monaco Editor | User interface — chat, IDE, review, debug |
| **App Server** | FastAPI (Python) | REST + WebSocket API, session management, LLM routing |
| **Orchestrator** | Python (Harness) | Agent lifecycle, task graph execution, working memory |
| **Intent System** | Python | NLP-based intent analysis, mode selection, skill synthesis |
| **Agent Backend** | Docker/VM/Cloud | Isolated execution environment for agents |

---

## Tech Stack

**Frontend**

React 19.2 · TypeScript · React Router 7 · TanStack Query 5 · Tailwind CSS 4 · Framer Motion 12 · Monaco Editor 0.55 · Zustand · Socket.IO · i18next · Lucide

**Backend**

Python 3.12 · FastAPI · WebSockets · LiteLLM · Poetry · Ruff · Mypy · Pytest

**Infrastructure**

Docker · Docker Compose · Kubernetes (optional) · PostgreSQL (optional, enterprise)

---

## Development

```bash
git clone https://github.com/Daniel-debug-boop/Wren.git
cd Wren

make build          # Install all dependencies
make run            # Start development servers

cd frontend && npm run dev      # Frontend only
make start-backend              # Backend only

cd frontend && npm run test     # Frontend tests
poetry run pytest tests/unit/   # Backend tests

cd frontend && npm run lint:fix && npm run build   # Lint & build
pre-commit run --all-files                         # Pre-commit checks
```

See [Development.md](./Development.md) for detailed documentation.

---

## Project Structure

```
wren/
├── frontend/              # React SPA (TypeScript)
│   ├── src/
│   │   ├── api/          # API client layer
│   │   ├── components/   # UI components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── routes/       # Page components
│   │   ├── types/        # Type definitions
│   │   └── utils/        # Utilities & verified models
│   └── __tests__/        # Vitest test suite
├── wren/                  # Python backend
│   ├── app_server/       # FastAPI application server
│   ├── server/           # Core server & orchestrator
│   ├── harness/          # Agent orchestrator
│   ├── intent/           # NLP intent analysis
│   └── agent_server/     # Agent server
├── enterprise/           # Enterprise features
└── skills/              # Reusable agent skill prompts
```

---

## Contributing

We welcome contributions! Please see:

- [Contributing Guidelines](./CONTRIBUTING.md)
- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [Issue Triage Guide](./ISSUE_TRIAGE.md)

Before submitting a PR:
- Pre-commit hooks pass (`make install-pre-commit-hooks`)
- TypeScript compiles (`cd frontend && npx tsc --noEmit`)
- Frontend builds (`cd frontend && npm run build`)
- Tests pass (`cd frontend && npm run test`)

---

## License

<div align="center">
  <p><strong>Wren</strong> — MIT License</p>
  <p>Built by the Wren team and contributors.</p>
  <p><sub>Enterprise features licensed separately under the Polyform Free Trial License.</sub></p>
</div>

---

<div align="center">
  <a href="#readme-top">⬆ Back to Top</a>
</div>
