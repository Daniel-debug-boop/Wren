# Wren AI — Android Build Engine (Termux)

Turn your Android phone into a portable AI software engineering server.

## Requirements

- Android 12+ (recommended)
- 4GB+ RAM (8GB recommended)
- 4GB free storage
- [Termux](https://f-droid.org/packages/com.termux/) (install from F-Droid, **not** Play Store)
- Optional: [Termux:Widget](https://f-droid.org/packages/com.termux.widget/) for one-tap homescreen icon

## Setup (one-time, 5-10 min)

### 1. Copy files to phone

```bash
# On your computer:
cd wren
tar czf wren-termux.tar.gz termux/
# Transfer wren-termux.tar.gz to phone via USB / ShareIt / Telegram
```

Or clone directly on phone:

```bash
# In Termux:
pkg install git
git clone --depth=1 https://github.com/Daniel-debug-boop/Wren.git ~/wren
```

### 2. Run bootstrap (single command)

```bash
cd ~/wren
bash termux/bootstrap.sh
```

This installs Python, Node.js, git, tmux, Chromium, and all dependencies automatically.

### 3. Start the servers

```bash
bash termux/start.sh
```

### 4. Open the app

Open Chrome / any browser on your phone and go to:

```
http://localhost:13000
```

The app runs **entirely on your phone**. No cloud, no external server.

## One-tap start (homescreen)

1. Install `Termux:Widget` from F-Droid
2. Run once:
   ```bash
   mkdir -p ~/.shortcuts
   cp ~/wren/termux/widget.sh ~/.shortcuts/wren-start.sh
   chmod +x ~/.shortcuts/wren-start.sh
   ```
3. Add Termux:Widget to home screen (long press → Widgets → Termux:Widget)
4. Tap the widget → "Wren Start"
5. Notification appears → tap it to open the app

## PWA (app-like experience)

1. Open `http://localhost:13000` in Chrome
2. Tap the three-dot menu → "Add to Home screen"
3. Name it "Wren AI"
4. It now opens fullscreen, no browser chrome

## How it works

```
┌─────────────────────────────────────┐
│           Android Phone             │
│  ┌───────────────────────────────┐  │
│  │          Termux               │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │  Python (FastAPI)       │  │  │
│  │  │  └─ API server :12000   │  │  │
│  │  ├─────────────────────────┤  │  │
│  │  │  Node.js (Vite)         │  │  │
│  │  │  └─ UI server :13000    │  │  │
│  │  ├─────────────────────────┤  │  │
│  │  │  tmux (process mgmt)    │  │  │
│  │  └─────────────────────────┘  │  │
│  │                               │  │
│  │  Browser → localhost:13000    │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Commands reference

| Action | Command |
|---|---|
| Start both servers | `bash termux/start.sh` |
| Start in background | `bash termux/start.sh --bg` |
| Stop all servers | `bash termux/start.sh --stop` |
| View backend logs | `tmux attach -t wren-backend` |
| View frontend logs | `tmux attach -t wren-frontend` |
| Detach from tmux | `Ctrl+B, D` |
| Run Wren agent | Open browser → type a prompt |

## Battery & background tips

- Keep phone plugged in during long builds
- Enable "Keep screen on" in Developer Options while testing
- Termux runs in userspace — Android may kill it under memory pressure
- For persistent background: use `termux-wake-lock` (included in widget)

## Storage

- Wren project: ~200MB
- Python deps: ~300MB
- Node.js deps: ~200MB
- Chromium: ~200MB
- **Total: ~900MB-1GB**

## Limitations on Android

| Limitation | Impact |
|---|---|
| No Docker | Use `RUNTIME=local` |
| ARM64 CPU | Python wheels work, Chromium via `pkg install chromium` |
| RAM | 8GB phones run well, 4GB may struggle with large models |
| No GPU acceleration | LLM inference on CPU (slower) |
| Background kill | Use widget with wake-lock |

## Troubleshooting

**Port already in use:**
```bash
pkill -f "wren.server" || true
pkill -f "vite" || true
bash termux/start.sh
```

**Python import error:**
```bash
cd ~/wren && poetry install
```

**Frontend blank page:**
```bash
# Check backend is running:
curl http://127.0.0.1:12000/api/health
```
