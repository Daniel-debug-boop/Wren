---
name: godot-installer
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - install godot
  - setup godot
  - godot not found
  - missing engine
  - export templates
  - godot version
  - game engine setup
  - initialize game project
---

# Godot Engine On-Demand Installer

This agent automatically downloads and installs the Godot Engine when game development context is detected.
It also provides headless background running capabilities for continuous game builds and testing.

---

## 🧠 RESPONSE PROTOCOL

When installing or setting up Godot, ALWAYS:

1. **Check first** — Run `which godot` or `godot --version` before downloading
2. **Report progress** — Every step outputs what's happening
3. **Verify after each step** — Confirm the step succeeded before moving on
4. **Handle errors gracefully** — If a download fails, suggest alternatives
5. **Report completion** — Show a summary of what was installed and the next steps

---

## 🔍 INSTALLATION CHECK — RUN THIS FIRST

```bash
# Check if Godot is already installed
if command -v godot &> /dev/null; then
    echo "✅ Godot found: $(godot --version)"
    echo "📂 Location: $(which godot)"
    # Check for export templates
    if ls ~/.local/share/godot/export_templates/*/ 2>/dev/null | head -n 1; then
        echo "✅ Export templates found"
    else
        echo "⚠️  Export templates NOT found — need to install"
    fi
else
    echo "❌ Godot not found — need to install"
fi

# Check if C# support is needed
if command -v dotnet &> /dev/null; then
    echo "✅ .NET SDK found: $(dotnet --version)"
else
    echo "⚠️ .NET SDK not found (only needed for C# projects)"
fi

# Check if Android SDK is needed
if [ -d "$ANDROID_HOME" ] || [ -d "$HOME/Android/Sdk" ]; then
    echo "✅ Android SDK found"
else
    echo "⚠️ Android SDK not found (only needed for Android exports)"
fi
```

---

## 🚀 INSTALLATION PIPELINE

### Step-by-Step Installation With Progress

```bash
echo "=== Godot Installation Pipeline ==="
echo "Target version: Godot 4.3 stable"
echo ""

STEP=1
GODOT_VERSION="4.3"
GODOT_BASE_URL="https://github.com/godotengine/godot/releases/download"

# Step 1: Download Godot editor
echo "[$STEP/5] Downloading Godot ${GODOT_VERSION} editor..."
((STEP++))
wget -q --show-progress "${GODOT_BASE_URL}/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip" -O /tmp/godot.zip
if [ $? -ne 0 ]; then
    echo "❌ Download failed. Checking alternatives..."
    # Try backup URL or different version
    echo "Trying alternative download method..."
    curl -L --progress-bar "${GODOT_BASE_URL}/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip" -o /tmp/godot.zip
fi
echo "✅ Downloaded ($(du -h /tmp/godot.zip | cut -f1))"

# Step 2: Install Godot binary
echo "[$STEP/5] Installing Godot to /usr/local/bin..."
((STEP++))
unzip -o /tmp/godot.zip -d /tmp/godot_extract
sudo mv /tmp/godot_extract/Godot_v${GODOT_VERSION}-stable_linux.x86_64/Godot_v${GODOT_VERSION}-stable_linux.x86_64 /usr/local/bin/godot
sudo chmod +x /usr/local/bin/godot
rm -rf /tmp/godot_extract /tmp/godot.zip
echo "✅ Installed"

# Step 3: Verify installation
echo "[$STEP/5] Verifying installation..."
((STEP++))
INSTALLED_VERSION=$(godot --version 2>&1)
if echo "$INSTALLED_VERSION" | grep -q "4."; then
    echo "✅ Godot $INSTALLED_VERSION is working"
else
    echo "❌ Verification failed: $INSTALLED_VERSION"
    exit 1
fi

# Step 4: Download and install export templates
echo "[$STEP/5] Installing export templates..."
((STEP++))
wget -q --show-progress "${GODOT_BASE_URL}/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_export_templates.tpz" -O /tmp/templates.tpz
mkdir -p ~/.local/share/godot/export_templates/${GODOT_VERSION}.stable
unzip -o /tmp/templates.tpz -d ~/.local/share/godot/export_templates/${GODOT_VERSION}.stable/
rm /tmp/templates.tpz
echo "✅ Export templates installed"

# Step 5: Final verification
echo "[$STEP/5] Final verification..."
((STEP++))
echo ""
echo "=== Installation Complete ==="
echo "Godot:    $(godot --version)"
echo "Templates: $(ls ~/.local/share/godot/export_templates/${GODOT_VERSION}.stable/templates/ 2>/dev/null | wc -l) templates"
echo "Location: $(which godot)"
echo ""
echo "Next steps:"
echo "1. Start Godot headless: godot --headless --path \$PWD &"
echo "2. Create a project: mkdir -p my_game/{scenes,scripts}"
echo "3. Export a build: godot --headless --export-release \"Linux/X11\" game.x86_64 --quit"
```

---

## ⚠️ ERROR RECOVERY TEMPLATES

### Error 1: Download Fails
```
❌ Download failed. Possible causes:
1. GitHub rate limiting — wait a few minutes and retry
2. Network timeout — try with larger timeout: wget -T 60 [url]
3. Version doesn't exist — check: curl -s https://api.github.com/repos/godotengine/godot/releases/latest | grep tag_name

Fix:
# Try wget with timeout
wget -T 60 "${GODOT_BASE_URL}/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip"

# Or try curl
curl -L --retry 3 --retry-delay 5 "${GODOT_BASE_URL}/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip" -o godot.zip
```

### Error 2: Permission Denied
```
❌ Permission denied when moving Godot to /usr/local/bin

Fix:
# Use sudo (requires password) OR install to user-local bin
mkdir -p ~/.local/bin
cp /tmp/godot_extract/Godot_v* ~/.local/bin/godot
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### Error 3: Export Templates Missing
```
❌ Export templates not found after installation

Fix:
# Templates must be in the exact correct directory
# Check where Godot expects them:
godot --version
# Expected: 4.3.stable (or similar)

# Reinstall with the correct version string:
GODOT_VERSION="4.3"
TEMPLATE_DIR="$HOME/.local/share/godot/export_templates/${GODOT_VERSION}.stable"
mkdir -p "$TEMPLATE_DIR"
wget "${GODOT_BASE_URL}/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_export_templates.tpz" -O /tmp/templates.tpz
unzip -o /tmp/templates.tpz -d "$TEMPLATE_DIR/"
rm /tmp/templates.tpz
```

### Error 4: C# / .NET Not Working
```
❌ dotnet command not found

Fix:
# Install .NET SDK
wget https://dot.net/v1/dotnet-install.sh -O /tmp/dotnet-install.sh
chmod +x /tmp/dotnet-install.sh
/tmp/dotnet-install.sh --channel 8.0
export PATH="$HOME/.dotnet:$PATH"
echo 'export PATH="$HOME/.dotnet:$PATH"' >> ~/.bashrc
```

### Error 5: Android SDK Missing or Wrong Version
```
❌ Gradle build failed / Android SDK not found

Fix:
# Check current setup
echo "ANDROID_HOME: $ANDROID_HOME"
echo "ANDROID_NDK_HOME: $ANDROID_NDK_HOME"

# Install command-line tools
ANDROID_SDK_ROOT="${ANDROID_HOME:-$HOME/Android/Sdk}"
mkdir -p "$ANDROID_SDK_ROOT"
cd /tmp
wget https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip -o commandlinetools-linux-*_latest.zip
yes | cmdline-tools/bin/sdkmanager --sdk_root="$ANDROID_SDK_ROOT" "platforms;android-33" "build-tools;33.0.2" "ndk;23.2.8568313"
```

### Error 6: Godot Command Not Found After Install
```
❌ bash: godot: command not found

Fix:
# The binary is installed but not in PATH
# Check where it was installed:
ls -la /usr/local/bin/godot 2>/dev/null || ls -la ~/.local/bin/godot 2>/dev/null

# If at ~/.local/bin/godot, add to PATH:
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## ✅ VERIFICATION CHECKLIST

After any installation step, run these checks:

```bash
echo "=== Godot Installation Verification ==="

echo -n "1. Godot binary: "
if command -v godot &> /dev/null; then
    echo "✅ $(which godot)"
else
    echo "❌ NOT FOUND"
fi

echo -n "2. Godot version: "
if godot --version &> /dev/null; then
    echo "✅ $(godot --version)"
else
    echo "❌ FAILED"
fi

echo -n "3. Headless mode: "
if godot --headless --version &> /dev/null; then
    echo "✅ Working"
else
    echo "❌ FAILED"
fi

echo -n "4. Export templates: "
TEMPLATES=$(ls ~/.local/share/godot/export_templates/*/templates/ 2>/dev/null | head -n 1)
if [ -n "$TEMPLATES" ]; then
    echo "✅ Found"
else
    echo "⚠️  Missing (export will fail)"
fi

echo -n "5. Android SDK: "
if [ -d "${ANDROID_HOME:-$HOME/Android/Sdk}" ]; then
    echo "✅ $ANDROID_HOME"
else
    echo "⚠️  Not configured (needed for Android builds)"
fi

echo -n "6. .NET SDK (C#): "
if command -v dotnet &> /dev/null; then
    echo "✅ $(dotnet --version)"
else
    echo "⚠️  Not installed (needed for C# projects)"
fi

echo ""
echo "Result: $([ $(command -v godot) ] && echo "✅ Ready for game development" || echo "❌ Installation incomplete")"
```

---

## 🏃 HEADLESS BACKGROUND MODE

Once Godot is installed, run it in headless mode as a background daemon:

```bash
# Use the actual project directory
PROJECT_DIR="$PWD"

# Start Godot headless in background
nohup godot --headless --path "$PROJECT_DIR" > /tmp/godot-headless.log 2>&1 &
GODOT_PID=$!
echo $GODOT_PID > /tmp/godot-headless.pid
echo "🎮 Godot headless started (PID: $GODOT_PID)"

# Verify it started successfully
sleep 2
if kill -0 $GODOT_PID 2>/dev/null; then
    echo "✅ Godot headless is running"
    echo "📝 Logs: /tmp/godot-headless.log"
else
    echo "❌ Godot failed to start. Check logs:"
    cat /tmp/godot-headless.log
fi

# Validate project opens correctly
godot --headless --path "$PROJECT_DIR" --quit 2>&1 && echo "✅ Project validates OK" || echo "⚠️ Project validation issue"

# Kill Godot when done
kill $GODOT_PID 2>/dev/null || pkill godot
echo "🎮 Godot headless stopped"
```

### Automated Build Daemon (Cross-Platform)
```bash
# Run a continuous build watcher that rebuilds on changes
PROJECT_DIR="$PWD"
PLATFORM=$(uname)

while true; do
    if [ "$PLATFORM" = "Linux" ]; then
        inotifywait -r -e modify --exclude '.godot/' "$PROJECT_DIR" 2>/dev/null
    elif [ "$PLATFORM" = "Darwin" ]; then
        fswatch -1 --exclude '.godot' "$PROJECT_DIR" 2>/dev/null
    else
        # Cross-platform polling fallback (works everywhere)
        sleep 5
    fi
    echo "🔄 Changes detected, rebuilding..."
    godot --headless --path "$PROJECT_DIR" --export-release "Linux/X11" "$PROJECT_DIR/exports/linux/game.x86_64" --quit
    echo "✅ Auto-build complete at $(date)"
done &
echo "📡 Build watcher started (PID: $!)"
```

---

## 📋 INSTALLATION SUMMARY TEMPLATE

After completing installation, produce this summary:

```
## ✅ Godot Installation Complete

### Installed Components
| Component | Status | Version | Path |
|-----------|--------|---------|------|
| Godot Editor | ✅ | [version] | [path] |
| Export Templates | ✅ | [count] templates | [path] |
| Headless Mode | ✅ | Tested | - |

### Optional Components
| Component | Status | Notes |
|-----------|--------|-------|
| C# / .NET | [✅/⚠️/❌] | [version or reason missing] |
| Android SDK | [✅/⚠️/❌] | [path or reason missing] |
| iOS Toolchain | [⚠️] | Requires macOS with Xcode |

### Next Steps
1. Create project: `godot --headless --quit --path ./my_game`
2. Start headless: `godot --headless --path ./my_game &`
3. Build export: `godot --headless --path ./my_game --export-release "Linux/X11" game.x86_64 --quit`
```

---

## 📦 INSTALLATION SCRIPTS

### Linux Installation
```bash
GODOT_VERSION="4.3"
GODOT_BASE_URL="https://github.com/godotengine/godot/releases/download"

# Download editor
wget "${GODOT_BASE_URL}/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip"
unzip -o "Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip"
sudo mv "Godot_v${GODOT_VERSION}-stable_linux.x86_64/Godot_v${GODOT_VERSION}-stable_linux.x86_64" /usr/local/bin/godot
chmod +x /usr/local/bin/godot
rm -rf "Godot_v${GODOT_VERSION}-stable_linux.x86_64" "Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip"

# Download export templates
wget "${GODOT_BASE_URL}/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_export_templates.tpz"
mkdir -p ~/.local/share/godot/export_templates/${GODOT_VERSION}.stable
unzip -o "Godot_v${GODOT_VERSION}-stable_export_templates.tpz" -d ~/.local/share/godot/export_templates/${GODOT_VERSION}.stable/
rm "Godot_v${GODOT_VERSION}-stable_export_templates.tpz"

# Verify
godot --version
```

### macOS Installation
```bash
GODOT_VERSION="4.3"
GODOT_BASE_URL="https://github.com/godotengine/godot/releases/download"
wget "${GODOT_BASE_URL}/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_macos.universal.zip"
unzip -o "Godot_v${GODOT_VERSION}-stable_macos.universal.zip"
sudo mv "Godot.app" /Applications/Godot.app
sudo ln -s /Applications/Godot.app/Contents/MacOS/Godot /usr/local/bin/godot
rm "Godot_v${GODOT_VERSION}-stable_macos.universal.zip"
wget "${GODOT_BASE_URL}/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_export_templates.tpz"
mkdir -p ~/Library/Application\ Support/Godot/export_templates/${GODOT_VERSION}.stable
unzip -o "Godot_v${GODOT_VERSION}-stable_export_templates.tpz" -d ~/Library/Application\ Support/Godot/export_templates/${GODOT_VERSION}.stable/
rm "Godot_v${GODOT_VERSION}-stable_export_templates.tpz"
godot --version
```

### Windows Installation (PowerShell)
```powershell
$GODOT_VERSION = "4.3"
$GODOT_BASE_URL = "https://github.com/godotengine/godot/releases/download"
Invoke-WebRequest -Uri "${GODOT_BASE_URL}/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_win64.exe.zip" -OutFile "godot.zip"
Expand-Archive -Path "godot.zip" -DestinationPath "C:\Godot"
[Environment]::SetEnvironmentVariable("PATH", "$env:PATH;C:\Godot", "Machine")
Invoke-WebRequest -Uri "${GODOT_BASE_URL}/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_export_templates.tpz" -OutFile "templates.zip"
New-Item -ItemType Directory -Force -Path "$env:APPDATA\Godot\export_templates\${GODOT_VERSION}.stable"
Expand-Archive -Path "templates.zip" -DestinationPath "$env:APPDATA\Godot\export_templates\${GODOT_VERSION}.stable"
godot --version
```

---

## C# / .NET Support

### Linux
```bash
wget https://dot.net/v1/dotnet-install.sh
chmod +x dotnet-install.sh
./dotnet-install.sh --channel 8.0
export PATH="$HOME/.dotnet:$PATH"
echo 'export PATH="$HOME/.dotnet:$PATH"' >> ~/.bashrc
GODOT_VERSION="4.3"
wget "https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_mono_linux_x86_64.zip"
unzip -o "Godot_v${GODOT_VERSION}-stable_mono_linux_x86_64.zip"
sudo mv "Godot_v${GODOT_VERSION}-stable_mono_linux_x86_64/Godot_v${GODOT_VERSION}-stable_mono_linux.x86_64" /usr/local/bin/godot
chmod +x /usr/local/bin/godot
rm -rf "Godot_v${GODOT_VERSION}-stable_mono_linux_x86_64" "Godot_v${GODOT_VERSION}-stable_mono_linux_x86_64.zip"
godot --version
dotnet --list-sdks
```

---

## Android SDK Setup

```bash
ANDROID_SDK_ROOT="$HOME/Android/Sdk"
mkdir -p "$ANDROID_SDK_ROOT"
wget https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip -o commandlinetools-linux-*_latest.zip -d "$ANDROID_SDK_ROOT"
yes | "$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager" --sdk_root="$ANDROID_SDK_ROOT" \
  "platforms;android-33" \
  "build-tools;33.0.2" \
  "ndk;23.2.8568313" \
  "platform-tools"
export ANDROID_HOME="$ANDROID_SDK_ROOT"
export ANDROID_NDK_HOME="$ANDROID_SDK_ROOT/ndk/23.2.8568313"
```

---

## Initialize a New Game Project

```bash
# Create the basic structure
mkdir -p my_game/{scenes,scripts,art,audio,addons}

# Create project.godot
cat > my_game/project.godot << 'EOF'
[application]
config/name="My Game"
config/description="A game built with Wren AI + Godot Engine"
run/main_scene="res://scenes/main.tscn"
config/icon="res://art/icon.png"
EOF

# Create default scene
cat > my_game/scenes/main.tscn << 'EOF'
[gd_scene format=3 uid="uid://main_scene"]
[node name="Main" type="Node"]
EOF

# Create GameManager autoload
mkdir -p my_game/scripts/managers
cat > my_game/scripts/managers/game_manager.gd << 'GDSCRIPT'
extends Node

var score: int = 0
var is_paused: bool = false

func _ready() -> void:
    process_mode = PROCESS_MODE_ALWAYS
GDSCRIPT

echo "✅ Game project created at ./my_game"
echo ""
echo "Next:"
echo "   cd my_game"
echo "   godot --headless --path . --quit  # Validate project"
```

---

## 📦 Installation Reference

| Component | Size | Required For | When |
|-----------|------|-------------|------|
| Godot Editor (standard) | ~100MB | All game development | Always needed |
| Godot Editor (.NET) | ~200MB | C# game development | Only for C# projects |
| Export Templates | ~400MB | Building for all platforms | Always for export |
| Android SDK + NDK | ~2GB | Android (APK/AAB) builds | When exporting to Android |
| .NET SDK | ~500MB | C# Godot projects | When using C# |
| iOS toolchain | ~10GB | iOS builds (macOS only) | When building for iOS |

---

## Version Management

```bash
# Get latest Godot version
curl -s https://api.github.com/repos/godotengine/godot/releases/latest | grep tag_name | cut -d'"' -f2
```

**Recommended**: Godot 4.3 (stable)
**Minimum**: Godot 4.2+
