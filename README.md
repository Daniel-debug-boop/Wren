# Wren

A professional, self-hosted AI engineering platform — a unified workspace for agentic coding, review, and execution.

<p align="center">
  <a href="./">
    <picture>
      <!-- prefer WebP for browsers that support it -->
      <source srcset="./assets/logo-320.webp" type="image/webp">
      <img src="./logo.png" alt="Wren" width="320" style="width:320px;max-width:45%;height:auto;display:block;margin:0 auto;">
    </picture>
  </a>

  <strong>Run AI coding agents locally or in your infrastructure. Own your data. Control your models.</strong>
</p>

---

## Quick start

1. Clone
```bash
git clone https://github.com/Daniel-debug-boop/Wren.git
cd Wren
```

2. Build
```bash
make build
```

3. Run (local)
```bash
export INSTALL_DOCKER=0 RUNTIME=local
make run FRONTEND_PORT=12000 FRONTEND_HOST=0.0.0.0 BACKEND_HOST=0.0.0.0
```

Open http://localhost:12000 (adjust port as needed).

---

## Core ideas

- Agentic workflows: human-in-the-loop or autonomous agents for coding, testing, and debugging.
- Built-in IDE: Monaco-based editor, file tree, terminal emulator and review tooling.
- Multi-LLM support: configurable providers and models.
- Secure execution: Docker/VM sandboxing and optional orchestration.
- Minimal ops: simple env-based configuration and Docker images for production.

---

## Minimal configuration

Set these environment variables for a typical local run:

- LLM_API_KEY — API key for your LLM provider
- LLM_MODEL — Default model (e.g. gpt-4o)
- WORKSPACE_DIR — Path for agent projects (default: ./workspace)
- FRONTEND_PORT — Frontend port (default: 3001)
- BACKEND_HOST, BACKEND_PORT — Backend host/port

Example:
```bash
export LLM_API_KEY="XXX"
export LLM_MODEL="gpt-4o"
export WORKSPACE_DIR="$HOME/projects/wren-workspace"
```

---

## Running in Docker

Quick demo (development):
```bash
docker run --rm -it \
  -p 8000:8000 \
  -v "$HOME/.wren:/home/wren/.wren" \
  -v "$HOME/projects:/projects" \
  ghcr.io/wren/agent-canvas:latest
```

---

## Animations & demos

To include subtle motion or interactive previews in this README:

- Use a small GIF (recommended < 1MB) placed under `assets/`:
  ```md
  ![Quick demo](./assets/demo.gif)
  ```
- Or add a hosted Lottie animation (linked) — note Lottie requires an external player and may not display in all viewers.

This repository's frontend uses Framer Motion for micro-interactions; keep README animations small, focused, and respectful of users' prefers-reduced-motion setting.

> Note: I have the new logo image you uploaded in this chat, but I cannot access binary image data directly to write files into the repo from the chat environment. To complete the branding update I can either:
> 1) Commit the image files for you if you paste the image as a base64 string here, or
> 2) You can upload the following files to the repository (assets/logo-320.png, assets/logo-160.png, assets/logo-64.png, assets/logo-320.webp, and replace ./logo.png) and I will finish any further README or reference edits on main.  
>
> If you prefer, I can provide a small script and ImageMagick commands to generate optimized variants locally and push them.

---

## Features (short)

- Real-time chat & streaming
- Workspace with live editing and terminal
- Agent orchestration and working memory
- Pluggable model providers
- Docker/VM execution backends

---

## Development (short)

- Build all: `make build`
- Run all: `make run`
- Frontend dev: `cd frontend && npm run dev`
- Backend dev: `make start-backend`
- Tests: frontend: `npm run test`; backend: `poetry run pytest tests/unit/`

Before committing:
```bash
make install-pre-commit-hooks
# Frontend
cd frontend && npm run lint:fix && npm run build
# Backend
pre-commit run --config ./dev_config/python/.pre-commit-config.yaml
```

---

## Contributing

1. Fork, create a feature branch.
2. Run pre-commit hooks and tests locally.
3. Keep changes focused and commit with clear messages.
4. Open a PR describing the change and the rationale.

See CONTRIBUTING.md for detailed guidelines.

---

## License & contact

MIT License — see LICENSE.

Maintained by Daniel and contributors — open issues and PRs are welcome:
https://github.com/Daniel-debug-boop/Wren/issues

---
