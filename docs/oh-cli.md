# oh CLI — Wren Entry Point

`oh` is the lightweight CLI for running Wren in solo mode (no team features, no billing, no auth).

## Quick Start

```bash
# Install dependencies
poetry install

# Run with defaults (port 3000, auto-opens browser)
oh

# Custom port
oh --port 8080

# Skip browser auto-open
oh --no-browser

# Verbose logging
oh --verbose
```

## Commands

| Command | Description |
|---------|-------------|
| `oh` | Start the server (default) |
| `oh doctor` | Check all dependencies and diagnose issues |
| `oh health` | Check if a running server is healthy |

### Server Flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--port` | `-p` | `3000` | Backend port |
| `--host` | | `127.0.0.1` | Bind address |
| `--no-browser` | | `false` | Skip browser auto-open |
| `--verbose` | `-v` | `false` | Enable debug logging |
| `--help` | `-h` | | Show help |
| `--version` | | | Show version |

### Health Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `127.0.0.1` | Server host to check |
| `--port` | `3000` | Server port to check |

## `oh doctor`

Check all dependencies and print a diagnostic report:

```
$ oh doctor

Wren Doctor

  ✓ Python: 3.12.3
  ✓ uvicorn: v0.30.1
  ✓ fastapi: v0.111.0
  ✓ pydantic: v2.7.0
  ✓ Node.js: v20.12.0
  ✓ npm: v10.5.0
  ✓ Playwright browsers: chromium
  ✓ Port 3000: available
  ✓ Frontend build: dist/index.html exists

  All 9 checks passed. You're good to go.
```

If something fails, it shows the fix:

```
  ✗ Node.js: not found
    fix: Install from https://nodejs.org
  ✗ Playwright browsers: not found
    fix: Run: playwright install chromium
```

## `oh health`

Check if a running server is responding:

```
$ oh health

Checking http://127.0.0.1:3000...

  ✓ Server is healthy (HTTP 200)
  ✓ Root endpoint responding (HTTP 200)
```

## What It Does

1. Sets `APP_MODE=oss`, `ENABLE_BILLING=false` automatically
2. First-run welcome message (one-time)
3. Checks port availability (with process identification if in use)
4. Verifies Python dependencies (uvicorn, fastapi)
5. Starts the backend server
6. Opens browser after 2s delay (unless `--no-browser`)
7. Graceful shutdown on Ctrl+C

## Error Handling

- **Port in use**: Shows which process is using the port, suggests alternative
- **Port < 1024**: Permission denied with helpful message
- **Missing deps**: Lists which packages to install
- **Server crash**: Catches and displays the error cleanly

## Architecture

```
oh CLI
├── oh doctor           → check all deps
├── oh health           → check running server
├── oh (default)        → start server
│   ├── sets solo mode env vars
│   ├── first-run welcome
│   ├── checks port availability
│   ├── checks Python dependencies
│   ├── starts uvicorn server
│   ├── auto-opens browser (optional)
│   └── handles SIGINT/SIGTERM gracefully
```

## vs `make run`

| Feature | `oh` | `make run` |
|---------|------|------------|
| `doctor` check | ✅ | ❌ |
| `health` check | ✅ | ❌ |
| Port check | ✅ with process ID | ❌ |
| Dependency check | ✅ | ❌ |
| Graceful shutdown | ✅ | basic |
| Browser auto-open | ✅ | ✅ |
| Verbose flag | ✅ | via env vars |
| Docker support | ❌ | ✅ |

Use `oh` for local development. Use `make run` for Docker/production.
