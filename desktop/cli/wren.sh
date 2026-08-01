#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  Wren AI — Universal CLI Launcher
#  Runs the Wren AI backend and opens the web UI.
#  Works on Linux, macOS, and Windows (via WSL/Git Bash).
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

WREN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)"
FRONTEND_DIR="$WREN_DIR/frontend"
BACKEND_DIR="$WREN_DIR"
PORT="${WREN_PORT:-12000}"

# Colors
GREEN='\033[32m'
CYAN='\033[36m'
YELLOW='\033[33m'
RED='\033[31m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${CYAN}→${NC} $1"; }
ok()    { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }

show_help() {
    cat << HELP
${BOLD}Wren AI — CLI${NC}

Usage:  ./wren.sh <command>

Commands:
  serve         Start the Wren AI backend server
  build         Build the frontend for production
  start         Build + serve (full startup)
  dev           Start in development mode (frontend + backend)
  android       Open Android project in Android Studio
  help          Show this help message

Options:
  --port N      Server port (default: 12000)
  --host H      Bind host (default: 0.0.0.0)
  --api-key K   LLM API key
  --model M     LLM model name

Environment:
  WREN_PORT       Server port
  LLM_API_KEY     API key
  LLM_MODEL       Model name
  LLM_BASE_URL    Custom API base URL

Examples:
  ./wren.sh serve
  ./wren.sh start --port 8080 --api-key sk-...
  WREN_PORT=3000 LLM_API_KEY=sk-... ./wren.sh serve
HELP
}

cmd_serve() {
    info "Starting Wren AI backend on port $PORT..."
    cd "$BACKEND_DIR"
    if command -v python3 &>/dev/null; then
        python3 -m wren.server.listen --port "$PORT" 2>&1
    elif command -v docker &>/dev/null; then
        docker run -p "$PORT":12000 --rm wren-ai/server
    else
        error "Python 3 not found. Install Python 3.12+ or run via Docker."
        exit 1
    fi
}

cmd_build() {
    info "Building frontend..."
    cd "$FRONTEND_DIR"
    npm ci 2>/dev/null || npm install
    npm run build
    ok "Frontend built at frontend/build/"
}

cmd_start() {
    cmd_build
    cmd_serve
}

cmd_dev() {
    info "Starting in dev mode (backend + frontend)..."
    cd "$BACKEND_DIR"
    python3 -m wren.server.listen --port "$PORT" &
    BACKEND_PID=$!
    cd "$FRONTEND_DIR"
    npm run dev &
    FRONTEND_PID=$!
    info "Backend PID: $BACKEND_PID, Frontend PID: $FRONTEND_PID"
    info "Press Ctrl+C to stop both"
    wait
}

cmd_android() {
    ANDROID_DIR="$WREN_DIR/wren-android"
    if [ -d "$ANDROID_DIR" ]; then
        info "Opening Android project..."
        if command -v studio &>/dev/null; then
            studio "$ANDROID_DIR"
        else
            echo "Open $ANDROID_DIR in Android Studio"
        fi
    else
        error "Android directory not found at $ANDROID_DIR"
    fi
}

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        serve|build|start|dev|android|help) CMD="$1"; shift ;;
        --port) PORT="$2"; shift 2 ;;
        --host) HOST="$2"; shift 2 ;;
        --api-key) export LLM_API_KEY="$2"; shift 2 ;;
        --model) export LLM_MODEL="$2"; shift 2 ;;
        --) shift; break ;;
        -h|--help) CMD="help"; shift ;;
        *) error "Unknown option: $1"; show_help; exit 1 ;;
    esac
done

case "${CMD:-serve}" in
    serve) cmd_serve ;;
    build) cmd_build ;;
    start) cmd_start ;;
    dev)   cmd_dev ;;
    android) cmd_android ;;
    help|*) show_help ;;
esac
