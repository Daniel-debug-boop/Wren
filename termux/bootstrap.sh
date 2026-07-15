#!/bin/bash
# ════════════════════════════════════════════════════════════════
#  WREN — TERMUX AUTO-BOOTSTRAP
#  One-command setup. Shows loading screen. Downloads everything.
#  Run: curl -fsSL https://wren.ai/termux | bash
# ════════════════════════════════════════════════════════════════

set -e

# ─── Configuration ─────────────────────────────────────────────
GODOT_VERSION="4.3"
WREN_VERSION="1.0.0"
TERMUX_PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
LOG_FILE="/tmp/wren-bootstrap.log"

# ─── Loading Screen ────────────────────────────────────────────

show_loading() {
    clear
    echo ""
    echo "  ╔═══════════════════════════════════════════════╗"
    echo "  ║                                               ║"
    echo "  ║               WREN                            ║"
    echo "  ║        AI Game & App Studio                   ║"
    echo "  ║                                               ║"
    echo "  ║     Loading... Please wait                    ║"
    echo "  ║                                               ║"
    echo "  ╚═══════════════════════════════════════════════╝"
    echo ""
    echo "  Initializing environment..."
    echo "  Log: $LOG_FILE"
    echo ""
}

# ─── Progress Bar ──────────────────────────────────────────────

progress() {
    local current=$1
    local total=$2
    local label=$3
    local percent=$((current * 100 / total))
    local filled=$((percent / 2))
    local empty=$((50 - filled))
    printf "\r  ["
    printf "%0.s#" $(seq 1 $filled)
    printf "%0.s." $(seq 1 $empty)
    printf "] %d%% — %s" "$percent" "$label"
}

# ─── Step Tracking ─────────────────────────────────────────────

STEPS=8
CURRENT_STEP=0

next_step() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    echo ""
    echo ""
    echo "  [$CURRENT_STEP/$STEPS] $1"
    echo "  ───────────────────────────────────────────────"
}

# ─── Main Installation ─────────────────────────────────────────

main() {
    show_loading
    sleep 2  # Show loading screen briefly
    exec 2>"$LOG_FILE"
    
    # Acquire wake lock to prevent Android from killing the download
    if command -v termux-wake-lock &>/dev/null; then
        termux-wake-lock
    fi
    
    # Error trap — show what failed
    trap 'echo "❌ Failed at step $CURRENT_STEP. Check: $LOG_FILE"; head -20 "$LOG_FILE"' ERR

    # ── Step 1: Update Termux ──────────────────────────────
    next_step "Updating Termux packages..."
    pkg update -y 2>/dev/null || true
    pkg upgrade -y 2>/dev/null || true
    progress 1 "$STEPS" "Packages updated"

    # ── Step 2: Install Core Dependencies ───────────────────
    next_step "Installing core dependencies..."
    pkg install -y \
        wget curl unzip git \
        python python-pip \
        nodejs-lts \
        build-essential \
        openssh \
        ripgrep \
        termux-exec \
        2>/dev/null
    progress 2 "$STEPS" "Core dependencies installed"

    # ── Step 3: Install Godot Engine ────────────────────────
    next_step "Downloading Godot Engine ${GODOT_VERSION}..."
    GODOT_URL="https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}-stable"
    
    # Detect architecture
    ARCH=$(uname -m)
    case "$ARCH" in
        aarch64) GODOT_BIN="Godot_v${GODOT_VERSION}-stable_linux.arm64.zip" ;;
        armv7l)  GODOT_BIN="Godot_v${GODOT_VERSION}-stable_linux.arm32.zip" ;;
        x86_64)  GODOT_BIN="Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip" ;;
        *)       echo "Unsupported architecture: $ARCH"; exit 1 ;;
    esac
    
    wget -q --show-progress "${GODOT_URL}/${GODOT_BIN}" -O "/tmp/godot.zip"
    unzip -qo "/tmp/godot.zip" -d "/tmp/godot_extract"
    # Find and install the Godot binary
    GODOT_BINARY=$(find /tmp/godot_extract -name "godot*" -type f 2>/dev/null | head -1)
    if [ -z "$GODOT_BINARY" ]; then
        GODOT_BINARY=$(find /tmp/godot_extract -name "Godot*" -type f 2>/dev/null | head -1)
    fi
    # Case-insensitive binary search
    GODOT_BINARY=$(find /tmp/godot_extract -type f \( -name "godot*" -o -name "Godot*" \) 2>/dev/null | head -1)
    if [ -z "$GODOT_BINARY" ]; then
        echo "⚠️  Could not find Godot binary after extraction"
        ls -la /tmp/godot_extract/
    else
        cp "$GODOT_BINARY" "$TERMUX_PREFIX/bin/godot"
        chmod +x "$TERMUX_PREFIX/bin/godot"
    fi
    rm -rf "/tmp/godot.zip" "/tmp/godot_extract"
    progress 3 "$STEPS" "Godot $GODOT_VERSION installed"

    # ── Step 4: Install Export Templates ────────────────────
    next_step "Downloading export templates..."
    TEMPLATES_DIR="$HOME/.local/share/godot/export_templates/${GODOT_VERSION}.stable"
    mkdir -p "$TEMPLATES_DIR"
    wget -q --show-progress "${GODOT_URL}/Godot_v${GODOT_VERSION}-stable_export_templates.tpz" \
        -O "/tmp/templates.tpz"
    unzip -qo "/tmp/templates.tpz" -d "$TEMPLATES_DIR/"
    rm "/tmp/templates.tpz"
    progress 4 "$STEPS" "Export templates installed"

    # ── Step 5: Install Python Dependencies ─────────────────
    next_step "Installing Python packages..."
    pip install --quiet --upgrade pip
    pip install --quiet \
        requests \
        pillow \
        numpy \
        2>/dev/null || true
    progress 5 "$STEPS" "Python packages installed"

    # ── Step 6: Install Node.js MCP Servers ─────────────────
    next_step "Installing MCP servers..."
    npm install -g --silent \
        tripo-ai-mcp-server \
        @meshy-ai/meshy-mcp-server \
        @modelcontextprotocol/server-filesystem \
        2>/dev/null || true
    progress 6 "$STEPS" "MCP servers installed"

    # ── Step 7: Set Up Git + Clone Skills ───────────────────
    next_step "Setting up skills repository..."
    git config --global user.name "Wren User"
    git config --global user.email "user@wren.ai"
    progress 7 "$STEPS" "Git configured"

    # ── Step 8: Verify Everything ────────────────────────────
    next_step "Verifying installation..."
    
    echo ""
    echo "  Checking components:"
    
    VERIFY_PASS=true
    
    printf "  ▸ Godot Engine:        "
    if command -v godot &> /dev/null; then
        echo "✅ $(godot --version 2>&1 | head -1)"
    else
        echo "❌ Not found"
        VERIFY_PASS=false
    fi
    
    printf "  ▸ Python:              "
    echo "✅ $(python3 --version 2>&1)"
    
    printf "  ▸ Node.js:             "
    echo "✅ $(node --version 2>&1)"
    
    printf "  ▸ npm:                 "
    echo "✅ $(npm --version 2>&1)"
    
    printf "  ▸ Git:                 "
    echo "✅ $(git --version 2>&1)"
    
    printf "  ▸ Export Templates:    "
    TEMPLATE_COUNT=$(ls "$TEMPLATES_DIR/templates/" 2>/dev/null | wc -l)
    if [ "$TEMPLATE_COUNT" -gt 0 ]; then
        echo "✅ $TEMPLATE_COUNT templates"
    else
        echo "⚠️  Missing (export may fail)"
    fi
    
    echo ""
    echo "  ───────────────────────────────────────────────"
    echo ""
    
    # Release wake lock
    if command -v termux-wake-unlock &>/dev/null; then
        termux-wake-unlock
    fi
    
    if $VERIFY_PASS; then
        echo "  ✅ WREN is ready!"
        echo ""
        echo "  Next steps:"
        echo "  1. Start building:  wren"
        echo "  2. Game mode:       /game-mode"
        echo "  3. API keys (optional):"
        echo "     - TRIPO_API_SECRET (for 3D models)"
        echo "     - MESHY_API_KEY (for 3D animations)"
        echo ""
    else
        echo "  ⚠️  Installation incomplete. Check: $LOG_FILE"
    fi
    
    echo ""
    echo "  Log saved to: $LOG_FILE"
}

# ─── Run ───────────────────────────────────────────────────────

main "$@"
