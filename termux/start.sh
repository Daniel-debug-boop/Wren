#!/data/data/com.termux/files/usr/bin/bash
set -e

# ═══════════════════════════════════════════════════════
#  Wren AI — Termux Native Start
#  Lightweight Android / ARM-optimized launcher.
#
#  Clever tricks for mobile:
#    - ARM64 detection → uses platform-optimized deps
#    - Memory budget auto-detection → limits workers
#    -- No Docker (installs locally via pip)
#    - Production build (not dev server)
#    - Tmux for persistence across sessions
#
#  Usage:
#    bash termux/start.sh           # start both servers
#    bash termux/start.sh --bg      # start in background
#    bash termux/start.sh --stop    # stop all servers
#    bash termux/start.sh --status  # check running status
# ═══════════════════════════════════════════════════════

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
DIM='\033[2m'
NC='\033[0m'

PROJECT_DIR="$HOME/wren"
BACKEND_PORT=12000
FRONTEND_PORT=13000
MEM_TOTAL_KB=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "0")

# ── Android clever tricks ────────────────────────────
detect_architecture() {
  local arch
  arch=$(uname -m)
  case "$arch" in
    aarch64|arm64) echo "arm64" ;;
    armv7l|armhf)  echo "arm32" ;;
    x86_64|amd64)  echo "x86_64" ;;
    *)             echo "$arch" ;;
  esac
}

detect_memory_budget() {
  # Memory-based worker count for Android
  local mem_mb=$((MEM_TOTAL_KB / 1024))
  if [ "$mem_mb" -lt 1024 ]; then
    echo "low"     # < 1GB: ultra-light
  elif [ "$mem_mb" -lt 3072 ]; then
    echo "medium"  # 1-3GB: normal
  else
    echo "high"    # > 3GB: full power
  fi
}

ARCH=$(detect_architecture)
MEM_BUDGET=$(detect_memory_budget)

echo -e "${CYAN}${BOLD}"
echo "  ╭──────────────────────────────────────╮"
echo "  │  Wren AI for Android                 │"
echo "  │  ${DIM}${ARCH} · ${MEM_BUDGET} memory budget${CYAN}         │"
echo "  ╰──────────────────────────────────────╯"
echo -e "${NC}"

# ── Memory-optimized settings ───────────────────────
case "$MEM_BUDGET" in
  low)
    MAX_WORKERS=1
    NODE_OPTIONS="--max-old-space-size=256"
    ;;
  medium)
    MAX_WORKERS=2
    NODE_OPTIONS="--max-old-space-size=512"
    ;;
  high)
    MAX_WORKERS=4
    NODE_OPTIONS="--max-old-space-size=1024"
    ;;
esac

export MAX_WORKERS
export NODE_OPTIONS
export NODE_ENV=production
export INSTALL_DOCKER=0
export RUNTIME=local
export TERMUX=1
export PYTHONOPTIMIZE=1  # Enable Python bytecode optimization
export PYTHONHASHSEED=0   # Consistent hashing (minor perf gain)

# ── Command handler ─────────────────────────────────
cd "$PROJECT_DIR"

case "${1:-}" in
  --stop)
    echo -e "${YELLOW}Stopping Wren...${NC}"
    tmux kill-session -t wren-backend 2>/dev/null || true
    tmux kill-session -t wren-frontend 2>/dev/null || true
    echo -e "${GREEN}✓ Stopped${NC}"
    exit 0
    ;;
  --status)
    echo -e "${DIM}Backend:${NC}"
    tmux has-session -t wren-backend 2>/dev/null && echo -e "  ${GREEN}✓ Running${NC}" || echo -e "  ${RED}✗ Stopped${NC}"
    echo -e "${DIM}Frontend:${NC}"
    tmux has-session -t wren-frontend 2>/dev/null && echo -e "  ${GREEN}✓ Running${NC}" || echo -e "  ${RED}✗ Stopped${NC}"
    echo -e "${DIM}Memory:${NC}  ${MEM_BUDGET} budget (${MEM_TOTAL_KB} KB total)"
    echo -e "${DIM}Arch:${NC}    ${ARCH}"
    exit 0
    ;;
esac

# ── Kill existing sessions ──────────────────────────
tmux kill-session -t wren-backend 2>/dev/null || true
tmux kill-session -t wren-frontend 2>/dev/null || true

# ── Ensure dependencies ─────────────────────────────
if [ ! -f "$PROJECT_DIR/.venv/bin/python" ]; then
  echo -e "${YELLOW}Setting up Python virtualenv...${NC}"
  cd "$PROJECT_DIR"
  pip install poetry
  poetry install --only main --no-interaction
fi

if [ ! -d "$PROJECT_DIR/frontend/node_modules" ]; then
  echo -e "${YELLOW}Installing frontend dependencies...${NC}"
  cd "$PROJECT_DIR/frontend"
  npm ci --production --no-optional
fi

# ── Build frontend if needed ────────────────────────
if [ ! -d "$PROJECT_DIR/frontend/build" ]; then
  echo -e "${YELLOW}Building frontend (production)...${NC}"
  cd "$PROJECT_DIR/frontend"
  NODE_ENV=production npm run build
fi

# ── Start backend ───────────────────────────────────
echo -e "${YELLOW}[1/2] Starting backend (${MEM_BUDGET} mode, ${ARCH})...${NC}"
tmux new-session -d -s wren-backend 2>&1
tmux send-keys -t wren-backend "
  cd $PROJECT_DIR
  export INSTALL_DOCKER=0 RUNTIME=local TERMUX=1
  export PYTHONOPTIMIZE=1
  poetry run uvicorn wren.server.listen:app --host 127.0.0.1 --port $BACKEND_PORT --workers $MAX_WORKERS --loop uvloop --http h11
" Enter
sleep 4
echo -e "${GREEN}  ✓ Backend on port $BACKEND_PORT${NC}"

# ── Start frontend (serving production build) ───────
echo -e "${YELLOW}[2/2] Starting frontend (production build)...${NC}"
tmux new-session -d -s wren-frontend 2>&1
tmux send-keys -t wren-frontend "
  cd $PROJECT_DIR/frontend
  NODE_ENV=production VITE_BACKEND_HOST=http://127.0.0.1:$BACKEND_PORT npx serve -s build -l $FRONTEND_PORT --no-clipboard
" Enter
sleep 2

echo ""
echo -e "${GREEN}${BOLD}✓ Wren AI is running!${NC}"
echo ""
echo -e "  ${DIM}Open in browser:${NC}  ${BOLD}http://localhost:${FRONTEND_PORT}${NC}"
echo -e "  ${DIM}Backend:${NC}          http://127.0.0.1:${BACKEND_PORT}"
echo -e "  ${DIM}Mode:${NC}             Production · ${MEM_BUDGET} budget"
echo -e "  ${DIM}Workers:${NC}          ${MAX_WORKERS}"
echo -e "  ${DIM}Stop:${NC}             ${BOLD}bash termux/start.sh --stop${NC}"
echo ""
