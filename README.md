<div align="center">
  <br/>
  <div>
    <img src="https://assets.wren.dev/logo-whitebackground.png" alt="Wren" width="280" style="margin-bottom: 0px;"/>
  </div>
  <br/>
  <h1 align="center" style="margin: 0px; font-size: 2.5rem; letter-spacing: -0.02em; animation: fadeInUp 0.8s ease-out;">
    AI Engineering Platform
  </h1>
  <p align="center" style="font-size: 1.15rem; max-width: 600px; margin: 12px auto 24px; color: #666; animation: fadeInUp 1s ease-out 0.1s both;">
    Self-host your AI coding agents. Chat, code, review, debug — all in one workspace.
    <br/>
    Bring your own LLM, own your data, own the workflow.
  </p>
  <p align="center" style="animation: fadeInUp 1.2s ease-out 0.2s both;">
    <a href="#quickstart"><img src="https://img.shields.io/badge/🚀_Quickstart-000?style=for-the-badge" alt="Quickstart"/></a>
    <a href="#features"><img src="https://img.shields.io/badge/✨_Features-000?style=for-the-badge" alt="Features"/></a>
    <a href="#architecture"><img src="https://img.shields.io/badge/🏗️_Architecture-000?style=for-the-badge" alt="Architecture"/></a>
  </p>
  <br/>
</div>

<style>
  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }
  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-6px); }
  }
  @keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }
  @media (prefers-reduced-motion: reduce) {
    * { animation: none !important; }
  }
</style>

---

<div align="center">
  <table style="animation: fadeInUp 1.4s ease-out 0.3s both;">
    <tr>
      <td align="center" style="transition: transform 0.2s; animation: float 4s ease-in-out infinite;"><strong>🧠 Multi-Agent Workspace</strong></td>
      <td align="center" style="transition: transform 0.2s; animation: float 4s ease-in-out 0.5s infinite;"><strong>💬 Conversational Coding</strong></td>
      <td align="center" style="transition: transform 0.2s; animation: float 4s ease-in-out 1s infinite;"><strong>🔧 Bring Your Own LLM</strong></td>
    </tr>
    <tr>
      <td align="center" style="transition: transform 0.2s;"><strong>📋 Plan → Code → Review → Debug</strong></td>
      <td align="center" style="transition: transform 0.2s;"><strong>🖥️ Built-in IDE & Terminal</strong></td>
      <td align="center" style="transition: transform 0.2s;"><strong>🤖 Autonomous Mode</strong></td>
    </tr>
  </table>
</div>

<br/>

---

<div align="center">
  <table>
    <tr>
      <td align="center"><strong>🧠 Multi-Agent Workspace</strong></td>
      <td align="center"><strong>💬 Conversational Coding</strong></td>
      <td align="center"><strong>🔧 Bring Your Own LLM</strong></td>
    </tr>
    <tr>
      <td align="center"><strong>📋 Plan → Code → Review → Debug</strong></td>
      <td align="center"><strong>🖥️ Built-in IDE & Terminal</strong></td>
      <td align="center"><strong>🤖 Autonomous Mode</strong></td>
    </tr>
  </table>
</div>

<br/>

**Wren** is an open-source AI engineering platform that puts you in control. Run coding agents powered by any LLM — OpenAI, Anthropic, Mistral, or your own — inside a browser-based workspace with chat, editor, terminal, review tools, and more.

No cloud lock-in. No data leaving your machine. No subscriptions tied to a single model provider. Just you, your API keys, and the most capable coding agents at your fingertips.

---

---

## <a id="quickstart"></a> ✦ Quickstart

### Prerequisites
- **Node.js** 22.12.x or later
- **Python** 3.12+ with `uv` or `poetry`
- **Docker** (optional, for sandboxed agent execution)

### One-Command Launch
```bash
git clone https://github.com/Daniel-debug-boop/Wren.git
cd Wren
make build && make run
```

Open **[http://localhost:3001](http://localhost:3001)** and start coding.

### Using the CLI
```bash
# Start the full stack
make run FRONTEND_PORT=3001 BACKEND_HOST=0.0.0.0
```

### Docker Sandbox (Isolated Execution)
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

## <a id="features"></a> ✦ Features

### 🧠 Three Core Modes

Wren is designed for non-coders. Pick a mode and let the agent handle the rest in the background.

| Mode | Purpose |
|------|---------|
| **Vibe Code** | Full agentic coding — chat, edit, run, repeat. Best for building apps from scratch. |
| **Autonomous** | Self-driving execution — agent plans, codes, and iterates with Working Memory + Lessons Learned, no hand-holding. |
| **Game** | Specialized mode for game development — scaffolding, asset wiring, and playable previews. |

> All other legacy modes (Plan, Code, Review, Debug, Ask) remain available under the hood for power users.

### 💬 Conversational Interface
- Chat with AI agents in natural language
- Real-time streaming responses via WebSocket
- Automatic mode suggestion based on your input
- Rich message bubbles with mode badges and action tags

### 🖥️ Built-in IDE Workspace (Code / Vibe Code modes)
- **TopBar** — Wren logo, version badge, active mode badge, live agent status pill (running / idle + task count + elapsed time), and a one-click **Deploy** button with an animated frosted-glass progress modal
- **FileTree** — real file explorer with tree / list views, edit & delete actions, and live updates
- **Monaco Editor** with syntax highlighting, bracket matching, and multi-cursor support
- **Inline Completions** with Tab-to-accept ghost text suggestions
- Live terminal with command history and bidirectional WebSocket communication
- Resizable panes — file tree, editor, terminal, and agent timeline

### 📋 Plan → Code → Review → Debug Pipeline
1. **Plan** — Agent analyses your request and presents a structured plan
2. **Code** — Agent implements the plan with file-by-file changes
3. **Review** — Review diffs, add comments, approve or reject changes
4. **Debug** — If errors occur, agent diagnoses and suggests fixes

### 🔧 Bring Your Own LLM
- Support for **OpenAI** (GPT-4o, o1, o3, etc.)
- Support for **Anthropic** (Claude 3.5 Sonnet, Claude 3 Opus, etc.)
- Support for **Mistral**, **Groq**, and custom endpoints
- Full control over model, temperature, max tokens, and reasoning effort

### 🤖 Skills & Automation
- **44+ Skills** — Domain-specific prompts for tasks (React, Python, Docker, Godot, etc.)
- **Auto-triggering** — Skills activate automatically based on context keywords
- **MCP Support** — Model Context Protocol for external tool integration
- **Working Memory** — Long-term context retention across sessions

### 🔐 Privacy & Control
- **Self-hosted** — All data stays on your infrastructure
- **No telemetry** — Optional, transparent analytics
- **Your API keys** — No vendor lock-in to a single model provider
- **Sandboxed execution** — Docker isolation for agent runs

---

## <a id="architecture"></a> ✦ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (React)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │   Chat   │  │  Monaco  │  │  Review  │  │ Terminal │ │
│  │ Interface│  │  Editor  │  │  Workspace│  │  Emulator│ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│                       ↕ WebSocket / REST                  │
├──────────────────────────────────────────────────────────┤
│                 Application Server (FastAPI)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Intent  │  │ Session  │  │   LLM    │  │  Skills  │ │
│  │  Router  │  │  Manager │  │  Router  │  │  Engine  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│                       ↕ Internal IPC                      │
├──────────────────────────────────────────────────────────┤
│              Agent Orchestrator (Harness)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │   Meta   │  │   Task   │  │  Working │  │  Vector  │ │
│  │Orchestr. │  │   Graph  │  │  Memory  │  │  Store   │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
├──────────────────────────────────────────────────────────┤
│              Agent Backends (Sandbox/Docker/VM)           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │  Docker  │  │   VM     │  │  Cloud   │                │
│  │ Sandbox  │  │ Backend  │  │ Backend  │                │
│  └──────────┘  └──────────┘  └──────────┘                │
└──────────────────────────────────────────────────────────┘
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

## ✦ Tech Stack

**Frontend**
- React 19.2 · TypeScript · React Router 7 · TanStack Query 5
- Tailwind CSS 4 · Framer Motion 12 · Monaco Editor 0.55
- Zustand · Socket.IO · i18next · Lucide React Icons

**Backend**
- Python 3.12 · FastAPI · WebSockets · LiteLLM
- Poetry · Ruff · Mypy · Pytest

**Infrastructure**
- Docker · Docker Compose · Kubernetes (optional)
- PostgreSQL (optional, for enterprise features)

---

## ✦ Development

```bash
# Clone the repository
git clone https://github.com/Daniel-debug-boop/Wren.git
cd Wren

# Install all dependencies (frontend + backend)
make build

# Start development servers
make run

# Run frontend only
cd frontend && npm run dev

# Run backend only
make start-backend

# Run tests
cd frontend && npm run test          # Frontend tests
poetry run pytest tests/unit/        # Backend tests

# Lint & typecheck
cd frontend && npm run lint:fix && npm run build
pre-commit run --all-files
```

See [Development.md](./Development.md) for detailed developer documentation.

---

## ✦ Project Structure

```
wren/
├── frontend/              # React SPA (TypeScript)
│   ├── src/
│   │   ├── api/          # API client layer
│   │   ├── components/   # UI components (layout, ide, ui, conversation)
│   │   ├── hooks/        # Custom React hooks (query, mutation, websocket)
│   │   ├── routes/       # React Router page components
│   │   ├── types/        # TypeScript type definitions
│   │   └── utils/        # Utility functions & verified models
│   └── __tests__/        # Vitest test suite
├── wren/                  # Python backend
│   ├── app_server/       # FastAPI application server (v1)
│   ├── server/           # Core server (orchestrator, middleware)
│   ├── harness/          # Agent orchestrator & task execution
│   ├── intent/           # NLP intent analysis & skill synthesis
│   └── agent_server/     # Agent server implementation
├── enterprise/           # Enterprise features (auth, billing, integrations)
└── skills/              # Reusable agent skill prompts
```

---

## ✦ Contributing

We welcome contributions! Please see:

- [Contributing Guidelines](./CONTRIBUTING.md)
- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [Issue Triage Guide](./ISSUE_TRIAGE.md)

Before submitting a PR, ensure:
- Pre-commit hooks pass (`make install-pre-commit-hooks`)
- TypeScript compiles (`cd frontend && npx tsc --noEmit`)
- Frontend builds (`cd frontend && npm run build`)
- Tests pass (`cd frontend && npm run test`)

---

## ✦ Community & Support

- **GitHub Issues** — Bug reports, feature requests, Q&A
- **Documentation** — Full API and usage docs
- **Discussions** — Community discussions and show-and-tell

---

## ✦ License

<div align="center">
  <p>
    <strong>Wren</strong> — MIT License
  </p>
  <p>
    Built with ❤️ by the Wren team and contributors.
  </p>
  <p>
    <sub>Enterprise features are licensed separately under the Polyform Free Trial License.</sub>
  </p>
</div>

---

<div align="center">
  <a href="#readme-top">⬆ Back to Top</a>
</div>
