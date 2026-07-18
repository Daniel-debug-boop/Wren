<div align="center">
  <br/>
  <img src="./logo.png" alt="Wren" width="320"/>
  <br/>
  <br/>
  
  # 🚀 Wren — AI Engineering Platform
  
  [![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
  [![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178c6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
  [![React 19](https://img.shields.io/badge/React-19-61dafb?style=flat-square&logo=react&logoColor=white)](https://react.dev/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![MIT License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
  <br/>
  <br/>
  
  **Self-host your AI coding agents.** Chat, code, review, debug — all in one unified workspace.  
  _Bring your own LLM · Own your data · Own the workflow_
  
  <br/>
  
  [🌐 Website](#) · [📖 Docs](./GETTING_STARTED.md) · [💬 Discord](#) · [🐛 Issues](https://github.com/Daniel-debug-boop/Wren/issues)
  
  <br/>
</div>

---

## ✨ Key Features

<table>
  <tr>
    <td width="50%">
      <h3>🤖 Agentic AI Engineering</h3>
      <ul>
        <li>Multi-mode chat interface (Vibe Code, Autonomous, Game)</li>
        <li>Real-time WebSocket streaming</li>
        <li>Intelligent mode auto-selection</li>
        <li>Working Memory & Lessons Learned</li>
      </ul>
    </td>
    <td width="50%">
      <h3>💻 Built-in IDE Workspace</h3>
      <ul>
        <li>Monaco Editor with full syntax highlighting</li>
        <li>Live file tree with real-time updates</li>
        <li>Terminal emulator with bidirectional WebSocket</li>
        <li>Resizable panes & customizable layout</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🔧 Flexible LLM Support</h3>
      <ul>
        <li>OpenAI (GPT-4o, o1, o3)</li>
        <li>Anthropic (Claude 3.5 Sonnet, Opus)</li>
        <li>Mistral, Groq, Custom Endpoints</li>
        <li>Full model configuration control</li>
      </ul>
    </td>
    <td width="50%">
      <h3>🛡️ Privacy & Control</h3>
      <ul>
        <li>100% self-hosted on your infrastructure</li>
        <li>Zero vendor lock-in</li>
        <li>Docker-based sandboxing</li>
        <li>Optional, transparent analytics</li>
      </ul>
    </td>
  </tr>
</table>

<br/>

---

## 🚀 Quick Start

### Prerequisites

```bash
✅ Node.js 22.12.x or later
✅ Python 3.12+ with uv or poetry  
✅ Docker (optional, for sandboxed execution)
✅ Git
```

### Launch Wren (3 steps)

```bash
# 1️⃣ Clone the repository
git clone https://github.com/Daniel-debug-boop/Wren.git
cd Wren

# 2️⃣ Install dependencies & build
make build

# 3️⃣ Start the application
make run
```

Open **[http://localhost:3001](http://localhost:3001)** in your browser and start coding! 🎉

> **Need detailed setup instructions?** Check out [GETTING_STARTED.md](./GETTING_STARTED.md)

### 🐳 Run with Docker

```bash
export PROJECTS_PATH="$HOME/projects"
mkdir -p "$PROJECTS_PATH" "$HOME/.wren"

docker run -it --rm \
  -p 8000:8000 \
  -v "$HOME/.wren:/home/wren/.wren" \
  -v "${PROJECTS_PATH}:/projects" \
  ghcr.io/wren/agent-canvas:latest
```

### ⚙️ Configuration

Set environment variables to customize Wren:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | — | Your LLM provider API key |
| `LLM_MODEL` | `gpt-4o` | Default model to use |
| `WORKSPACE_DIR` | `./workspace` | Project workspace path |
| `FRONTEND_PORT` | `3001` | Frontend development port |
| `BACKEND_HOST` | `127.0.0.1` | Backend server hostname |
| `BACKEND_PORT` | `3000` | Backend server port |

<br/>

---

## 📋 Core Operating Modes

Wren offers three powerful modes to fit your workflow:

### 🎯 **Vibe Code** — Interactive Development
Full agentic coding with real-time feedback. Chat, edit, run, and iterate. Perfect for building applications from scratch with continuous human guidance.

### ⚡ **Autonomous** — Self-Driving Execution  
Agent plans, codes, and debugs independently using Working Memory and Lessons Learned. Minimal hand-holding required. Ideal for complex, multi-step tasks.

### 🎮 **Game** — Game Development Focus
Specialized scaffolding for game projects. Asset wiring, scene management, and playable previews built-in.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   🎨 Frontend (React 19)                     │
│  ┌─────────────┐  ┌──────────┐  ┌─────────┐  ┌───────────┐  │
│  │ Chat Panel  │  │ Monaco   │  │ Review  │  │ Terminal  │  │
│  │ Interface   │  │ Editor   │  │ Console │  │ Emulator  │  │
│  └─────────────┘  └──────────┘  └─────────┘  └───────────┘  │
│                    ↕ WebSocket / REST APIs                   │
├──────────────────────────────────────────────────────────────┤
│              🔌 Application Server (FastAPI)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Intent   │  │ Session  │  │   LLM    │  │ Skills   │    │
│  │ Router   │  │ Manager  │  │ Router   │  │ Engine   │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                    ↕ Internal IPC                            │
├──────────────────────────────────────────────────────────────┤
│           🎭 Agent Orchestrator (Harness Layer)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  Meta    │  │ Task     │  │Working   │  │ Vector   │    │
│  │Orchestr. │  │ Graph    │  │ Memory   │  │ Store    │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│        🔒 Agent Execution Backends (Isolated)               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ Docker   │  │   VM     │  │  Cloud   │                   │
│  │ Sandbox  │  │ Backend  │  │ Backend  │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└──────────────────────────────────────────────────────────────┘
```

### Component Stack

| Layer | Technology | Purpose |
|-------|-----------|----------|
| **Frontend** | React 19, TypeScript, TailwindCSS, Monaco Editor | User interface & IDE workspace |
| **API Server** | FastAPI, WebSockets, Python 3.12 | REST + real-time communication |
| **Orchestration** | Python Harness, Task Graph | Agent lifecycle & execution |
| **Intent System** | NLP-based analysis | Mode selection & skill synthesis |
| **Execution** | Docker / VM / Cloud | Isolated, secure agent runtime |

<br/>

---

## 🛠️ Development

### Setup Development Environment

```bash
# Install all dependencies (backend + frontend)
make build

# Install pre-commit hooks (required before committing)
make install-pre-commit-hooks
```

### Development Commands

```bash
# Start full development stack
make run

# Frontend only (on port 3001)
cd frontend && npm run dev

# Backend only (on port 3000)
make start-backend

# Run tests
cd frontend && npm run test       # Frontend tests
poetry run pytest tests/unit/     # Backend tests

# Linting & formatting
cd frontend && npm run lint:fix && npm run build
pre-commit run --all-files --config ./dev_config/python/.pre-commit-config.yaml
```

### Before Submitting a PR

```bash
# 1. Install pre-commit hooks
make install-pre-commit-hooks

# 2. Make your changes
# ... edit files ...

# 3. Lint & format (auto-fixes most issues)
cd frontend && npm run lint:fix && npm run build    # Frontend
pre-commit run --config ./dev_config/python/.pre-commit-config.yaml  # Backend

# 4. Verify TypeScript compilation
cd frontend && npx tsc --noEmit

# 5. Run tests
cd frontend && npm run test
poetry run pytest tests/unit/

# 6. Commit & push
git add <specific-files>  # Avoid git add .
git commit -m "Your message"
git push
```

All pre-commit checks **MUST** pass before merging. See [Development.md](./Development.md) for detailed setup.

<br/>

---

## 📦 Project Structure

```
Wren/
├── 🎨 frontend/                    # React SPA (TypeScript)
│   ├── src/
│   │   ├── api/                   # API client layer & data fetching
│   │   ├── components/            # Reusable UI components
│   │   ├── hooks/                 # Custom React hooks
│   │   ├── routes/                # Page components & routing
│   │   ├── types/                 # TypeScript type definitions
│   │   └── utils/                 # Utilities & verified models
│   ├── __tests__/                 # Vitest test suite
│   └── package.json               # Dependencies & scripts
│
├── 🐍 wren/                        # Python backend
│   ├── app_server/                # FastAPI application server
│   ├── server/                    # Core server & orchestrator
│   ├── harness/                   # Agent orchestrator (task graph, working memory)
│   ├── intent/                    # NLP intent analysis & mode selection
│   ├── agent_server/              # Agent runtime server
│   └── cli/                       # Command-line interface
│
├── 🎯 skills/                     # Reusable agent skill prompts (44+)
│   ├── react/                     # React skill prompts
│   ├── python/                    # Python development skills
│   ├── docker/                    # Docker/containers skills
│   ├── godot/                     # Game development (Godot)
│   └── ...                        # Domain-specific skills
│
├── 📚 docs/                       # Documentation & guides
├── 🧪 tests/                      # Pytest test suite
├── 🐳 containers/                 # Docker configuration
├── Makefile                       # Build & development commands
└── pyproject.toml                 # Python project configuration
```

<br/>

---

## 🔌 Technology Stack

### Frontend (34.7% TypeScript + HTML + CSS)
- **React** 19.2 — Modern UI framework  
- **TypeScript** 5.9 — Type-safe development  
- **React Router** 7 — Client-side routing  
- **TanStack Query** 5 — Data fetching & caching  
- **TailwindCSS** 4 — Utility-first styling  
- **Monaco Editor** 0.55 — Code editor  
- **Framer Motion** 12 — Animations  
- **Zustand** — State management  
- **Socket.IO** — Real-time communication  
- **i18next** — Internationalization  

### Backend (62.1% Python)
- **Python** 3.12+ — Core language  
- **FastAPI** — High-performance web framework  
- **WebSockets** — Real-time bidirectional communication  
- **LiteLLM** 1.84.1 — Multi-LLM provider abstraction  
- **SQLAlchemy** 2.0+ — ORM & database  
- **Pydantic** — Data validation  
- **Poetry** 2.3 — Dependency management  
- **Pytest** 9.0 — Testing framework  

### Infrastructure
- **Docker** — Containerization & sandboxing  
- **PostgreSQL** — Optional persistent storage  
- **Redis** — Caching & sessions  
- **Kubernetes** — Optional orchestration  

<br/>

---

## 🎓 Learn More

- **[🚀 Getting Started Guide](./GETTING_STARTED.md)** — Step-by-step setup and first run
- **[📖 Full Documentation](./Development.md)** — Advanced configuration and development
- **[🤖 Agent Architecture](./AGENTS.md)** — Deep dive into agent systems
- **[🛠️ Contributing Guide](./CONTRIBUTING.md)** — How to contribute to Wren
- **[📋 Issue Triage](./ISSUE_TRIAGE.md)** — How we manage issues
- **[👥 Credits](./CREDITS.md)** — Team & contributors
- **[📜 Code of Conduct](./CODE_OF_CONDUCT.md)** — Community guidelines

<br/>

---

## 🤝 Contributing

We welcome contributions of all sizes! Whether it's bug reports, feature requests, or code contributions, your help makes Wren better.

### Getting Started

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/your-feature`)
3. **Install** pre-commit hooks (`make install-pre-commit-hooks`)
4. **Make** your changes
5. **Test** thoroughly (`make test`)
6. **Lint** your code (`make lint`)
7. **Commit** with a clear message
8. **Push** and open a Pull Request

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

<br/>

---

## 📊 Language Composition

- **Python** 62.1% — Core backend logic
- **TypeScript** 34.7% — Frontend & tooling  
- **HTML** 1.2% — Structure  
- **Shell** 0.4% — Build scripts  
- **CSS** 0.4% — Styles  
- **Jinja** 0.4% — Templates  
- **Other** 0.8% — Configuration

<br/>

---

## 📜 License

**Wren** is open source and released under the **[MIT License](LICENSE)**.

Built with ❤️ by [Daniel](https://github.com/Daniel-debug-boop) and [contributors](./CREDITS.md).

<br/>

---

## 🔗 Community & Support

- 💬 **Questions?** [Open a discussion](https://github.com/Daniel-debug-boop/Wren/discussions)
- 🐛 **Found a bug?** [Report an issue](https://github.com/Daniel-debug-boop/Wren/issues)
- 💡 **Have an idea?** [Request a feature](https://github.com/Daniel-debug-boop/Wren/issues)
- 🌐 **Website:** [wren.dev](https://assets.wren.dev)

<br/>

<div align="center">
  <p>
    Made with 🚀 by AI engineers, for AI engineers
  </p>
  <p>
    <a href="#readme-top">⬆️ Back to Top</a>
  </p>
</div>
