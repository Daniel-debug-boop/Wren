# Wren — Code Less, Make More

Wren is an open-source AI software engineer. It writes code, fixes bugs, and handles dev tasks so you can focus on what matters.

## Quick Start

```bash
# Install
pip install wren-ai
# or
poetry install

# Check your setup
oh doctor

# Start
oh
```

Open `http://localhost:3000` — Wren is ready.

## What Wren Does

- **Write code** — from natural language descriptions
- **Fix bugs** — with root cause analysis
- **Run commands** — shell, Python, whatever you need
- **Browse the web** — with anti-bot bypass built in
- **Multi-file edits** — surgical changes across your codebase
- **Git integration** — commits, PRs, branches

## Commands

| Command | What it does |
|---------|-------------|
| `oh` | Start the server |
| `oh doctor` | Check all dependencies |
| `oh health` | Check if server is running |
| `oh --port 8080` | Custom port |
| `oh --no-browser` | Skip browser auto-open |

## Architecture

```
Wren
├── oh CLI                    → start, doctor, health
├── Python backend (FastAPI)  → 123 API routes, sandbox runtime
├── React frontend            → chat, code editor, terminal, planner
├── Skills system             → 44+ skills, auto-triggered
├── MCP tools                 → 5 native servers (no config needed)
└── Intent understanding      → psychology-first planning
```

## Skills

Wren comes with 44+ skills that auto-activate based on context:

| Category | Skills |
|----------|--------|
| Security | vibesec, cso |
| Design | emil-design-eng, animation-vocabulary, penpot |
| Product | product-guardrails, ponytail |
| Scraping | scrapling, scrapling-official |
| Planning | investigate, gstack, plan-ceo-review |

## MCP Tools

| Server | Purpose |
|--------|---------|
| `fetch` | HTTP requests |
| `filesystem` | File operations |
| `chrome-devtools` | Browser automation |
| `scrapling` | Anti-bot scraping |
| `ponytail` | Lazy senior dev patterns |

All native — no user configuration required.

## Development

```bash
# Backend
poetry install
oh

# Frontend
cd frontend && npm install && npm run dev

# Tests
poetry run pytest tests/unit/
```

## License

MIT
