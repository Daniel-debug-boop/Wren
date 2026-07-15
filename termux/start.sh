#!/data/data/com.termux/files/usr/bin/bash
set -e

# ──────────────────────────────────────────────
# Wren AI — Termux Start
# Launches backend + frontend servers.
# Run after bootstrap.sh completes.
#
# Usage:
#   bash termux/start.sh          # start both servers
#   bash termux/start.sh --bg     # start in background (tmux)
#   bash termux/start.sh --stop   # stop all servers
# ──────────────────────────────────────────────

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
DIM='\033[2m'
NC='\033[0m'

PROJECT_DIR="$HOME/wren"
BACKEND_PORT=12000
FRONTEND_PORT=13000

cd "$PROJECT_DIR"

# ── Stop ──
if [ "${1:-}" = "--stop" ]; then
  echo -e "${YELLOW}Stopping Wren servers...${NC}"
  tmux kill-session -t wren-backend 2>/dev/null || true
  tmux kill-session -t wren-frontend 2>/dev/null || true
  echo -e "${GREEN}✓ Stopped${NC}"
  exit 0
fi

# ── Kill existing sessions if any ──
tmux kill-session -t wren-backend 2>/dev/null || true
tmux kill-session -t wren-frontend 2>/dev/null || true

# ── Export env ──
export INSTALL_DOCKER=0
export RUNTIME=local
export TERMUX=1

echo -e "${BOLD}┌─────────────────────────────────────┐"
echo -e "│  Wren AI — Starting...               │"
echo -e "└─────────────────────────────────────┘${NC}"
echo ""

# ── Backend ──
echo -e "${YELLOW}[1/2] Starting backend...${NC}"
if [ "${1:-}" = "--bg" ]; then
  tmux new-session -d -s wren-backend "
    cd $PROJECT_DIR
    export INSTALL_DOCKER=0 RUNTIME=local TERMUX=1
    poetry run python -m wren.server.listen --port $BACKEND_PORT --host 127.0.0.1
  " 2>&1
else
  tmux new-session -d -s wren-backend 2>&1
  tmux send-keys -t wren-backend "
    cd $PROJECT_DIR
    export INSTALL_DOCKER=0 RUNTIME=local TERMUX=1
    poetry run python -m wren.server.listen --port $BACKEND_PORT --host 127.0.0.1
  " Enter
fi
sleep 3
echo -e "${GREEN}  ✓ Backend running on port $BACKEND_PORT${NC}"

# ── Frontend ──
echo -e "${YELLOW}[2/2] Starting frontend...${NC}"
if [ "${1:-}" = "--bg" ]; then
  tmux new-session -d -s wren-frontend "
    cd $PROJECT_DIR/frontend
    VITE_BACKEND_HOST=http://127.0.0.1:$BACKEND_PORT npm run dev -- --port $FRONTEND_PORT --host 127.0.0.1
  " 2>&1
else
  tmux send-keys -t wren-frontend "
    cd $PROJECT_DIR/frontend
    VITE_BACKEND_HOST=http://127.0.0.1:$BACKEND_PORT npm run dev -- --port $FRONTEND_PORT --host 127.0.0.1
  " Enter
fi
sleep 2

echo ""
echo -e "${GREEN}${BOLD}✓ Wren AI is running!${NC}"
echo ""
echo -e "  ${DIM}Open in browser:${NC}  ${BOLD}http://localhost:${FRONTEND_PORT}${NC}"
echo -e "  ${DIM}Backend API:${NC}      http://127.0.0.1:${BACKEND_PORT}"
echo -e "  ${DIM}Stop servers:${NC}     ${BOLD}bash termux/start.sh --stop${NC}"
echo ""
