#!/data/data/com.termux/files/usr/bin/bash
# ──────────────────────────────────────────────
# Wren AI — Termux:Widget one-tap launcher
#
# Install:
#   1. pkg install termux-widget
#   2. mkdir -p ~/.shortcuts
#   3. cp termux/widget.sh ~/.shortcuts/wren-start.sh
#   4. Add Termux:Widget to home screen
#   5. Tap icon → Wren starts
# ──────────────────────────────────────────────

# Wake lock so Android doesn't kill the process
termux-wake-lock

# Start servers in background
bash "$HOME/wren/termux/start.sh" --bg

# Notification with URL
termux-notification \
  --id wren \
  --title "Wren AI" \
  --content "Running on http://localhost:13000" \
  --action "am start -a android.intent.action.VIEW -d http://localhost:13000" \
  --button1 "Stop" \
  --button1-action "bash $HOME/wren/termux/start.sh --stop; termux-wake-unlock" \
  --priority high \
  --ongoing

# Vibrate once to confirm
termux-vibrate -d 100
