# Contributing to Wren

Thanks for your interest in contributing! Wren is an open-source AI software engineer tool.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/your-org/wren.git
cd wren

# Install Python dependencies
poetry install

# Install frontend dependencies
cd frontend && npm install && cd ..

# Install pre-commit hooks
make install-pre-commit-hooks
```

## Running Locally

```bash
# Start the full app
export INSTALL_DOCKER=0
export RUNTIME=local
make build && make run FRONTEND_PORT=12000
```

## Running Tests

```bash
# Python tests
poetry run pytest tests/unit/ -q

# Frontend tests
cd frontend && npm run test

# Linting
pre-commit run --config ./dev_config/python/.pre-commit-config.yaml
cd frontend && npm run lint:fix
```

## Project Structure

```
wren/
├── wren/          # Python backend
│   ├── app_server/     # FastAPI routes
│   ├── cli/            # oh CLI
│   ├── harness/        # Runtime harness
│   └── intent/         # Intent understanding
├── frontend/           # React frontend
│   └── src/
│       ├── components/ # UI components
│       ├── hooks/      # React hooks
│       └── api/        # API client
├── skills/             # Knowledge skills (MCP)
├── tests/              # Test suite
└── docs/               # Documentation
```

## Code Style

- Python: Ruff (linting + formatting)
- TypeScript: ESLint + Prettier
- Commits: Conventional Commits format

## Pull Requests

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a PR

## Questions?

Open an issue or join our Slack community.
