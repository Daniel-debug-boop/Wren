# Wren AI for Android

Build Wren AI as a standalone APK. One install. Type prompts. Get apps.

## How it works

```
Open app → Bootstrap screen → WebView shows Wren UI → type prompt → agent works → notification "Ready!"
                                                                              ↓
                                                                     Tap notification → see result
```

No Termux terminal ever visible. No commands to type. No technical knowledge needed.

## Features

- **One-tap install** — No terminal, no setup commands
- **Background server** — Python server runs as a foreground service
- **Auto-start** — Server starts automatically on phone boot
- **Job notifications** — Get notified when your project is ready
- **Settings UI** — Configure LLM API key, model selection, and server preferences
- **Security hardened** — Network security config, JS bridge sanitization, cleartext restrictions
- **Error recovery** — Health check polling with retry, error state UI with retry button
- **Battery optimized** — Requests battery optimization exemption for long agent runs

## Prerequisites to BUILD (done once on a computer)

- Android Studio (latest, free from developer.android.com)
- Android SDK 35 (bundled with Android Studio)
- A Linux/macOS machine (or WSL on Windows)

## Build steps

### 1. Build the Wren frontend

```bash
cd wren/frontend && npm install && npm run build
```

### 2. Copy frontend build into Android project

```bash
cp -r frontend/build wren-android/app/src/main/assets/www
```

### 3. Copy Wren backend into Android project

```bash
mkdir -p wren-android/app/src/main/assets/python/wren
cp -r wren/ wren-android/app/src/main/assets/python/wren/
```

### 4. Open in Android Studio

```bash
open wren-android/  # or File → Open in Android Studio
```

### 5. Generate Android launcher icons (optional)

Android Studio: right-click `res/` → New → Image Asset → use the foreground vector

### 6. Build APK

```
Build → Build Bundle(s) / APK(s) → Build APK(s)
```

APK will be at `app/build/outputs/apk/debug/app-debug.apk`

### 7. Install on phone

Transfer APK to phone → tap to install → open "Wren AI"
(You may need to enable "Install from unknown sources" in Settings)

## First launch

1. App shows "Setting up Wren AI..." with real progress
2. Downloads Python runtime (~20MB)
3. Installs pip packages (~30MB)
4. Starts server with health check verification
5. WebView loads — you see the Wren chat interface
6. Type a prompt → agent works → notification arrives

## Subsequent launches

- App starts in ~2 seconds
- Server auto-starts on phone boot (no tap needed)
- Tap the Wren icon → immediately in the app

## Project structure

```
wren-android/
├── app/
│   ├── build.gradle.kts              # Android + Chaquopy + signing config
│   ├── proguard-rules.pro             # ProGuard rules for release builds
│   └── src/main/
│       ├── AndroidManifest.xml        # Permissions, activities, service
│       ├── java/com/wren/android/
│       │   ├── WrenApp.kt            # Application class, notification channels
│       │   ├── MainActivity.kt       # WebView with JS bridge, error states, progress
│       │   ├── BootstrapActivity.kt  # First-launch setup with real progress
│       │   ├── ServerManager.kt      # Python server with health check + retry
│       │   ├── WrenService.kt        # Background foreground service with graceful shutdown
│       │   ├── BootReceiver.kt       # Auto-start on phone boot
│       │   ├── SettingsActivity.kt   # Settings UI for LLM config, model, server
│       │   └── WrenUtils.kt          # Battery optimization, network checks
│       ├── assets/
│       │   ├── python/
│       │   │   ├── wren_server_runner.py  # Python entry point
│       │   │   └── wren/                   # Copied from Wren backend
│       │   └── www/                         # Copied from frontend/build
│       ├── res/
│       │   ├── xml/
│       │   │   └── network_security_config.xml  # Security config
│       │   ├── drawable/              # Icons
│       │   ├── mipmap-anydpi-v26/     # Adaptive icons
│       │   └── values/                # Themes, strings
├── build.gradle.kts
├── settings.gradle.kts
└── gradle.properties
```

## Architecture

### Security
- **Network Security Config**: Cleartext HTTP only allowed for `127.0.0.1` (local server)
- **JS Bridge Sanitization**: All inputs from JavaScript are sanitized (max length, control char stripping)
- **WebView Hardening**: File access disabled, mixed content blocked, no password saving
- **ProGuard**: Release builds are minified and obfuscated

### Reliability
- **Health Check**: Server start includes polling `GET /api/health` with retry (10 attempts, 1s delay)
- **Error States**: UI shows error with retry button when server fails to start
- **Graceful Shutdown**: `onTaskRemoved()` properly stops the Python server
- **Crash Recovery**: `ServerManager.resetState()` called on app start

### UX
- **Real Progress**: Bootstrap screen shows actual server startup phases
- **Job Progress**: Agent progress updates shown as a banner overlay
- **File Downloads**: WebView download listener handles file downloads
- **Battery Optimization**: App requests exemption for long-running agent tasks

## Limitations

| Aspect | Status |
|---|---|
| ARM64 + x86_64 | Supported (real devices + emulator) |
| Python C extensions | Some may not have Android wheels. Pure Python works. |
| First build | Requires Android Studio + copying assets |
| APK size | ~150MB (Python + deps + Wren) |
| RAM usage | ~500MB for server + WebView |
| Battery | Requests optimization exemption for long runs |

## License

Same as Wren — MIT

---

Built with Chaquopy (embedded CPython for Android) + Jetpack Compose + WebView.
