# Wren AI for Android

Build Wren AI as a standalone APK. One install. Type prompts. Get apps.

## How it works

```
Open app → WebView shows Wren UI → type prompt → agent works hours → notification "Ready!"
                                                                       ↓
                                                              Tap notification → see result
```

No Termux terminal ever visible. No commands to type. No technical knowledge needed.

## Prerequisites to BUILD (done once on a computer)

- Android Studio (latest, free from developer.android.com)
- Android SDK 35 (bundled with Android Studio)
- A Linux/macOS machine (or WSL on Windows)

## Build steps

### 1. Build the Wren frontend

```bash
cd OpenHands-main
cd frontend && npm install && npm run build
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

1. App shows "Setting up Wren AI..." progress bar
2. Downloads Python runtime (~20MB)
3. Installs pip packages (~30MB)
4. Starts server
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
│   ├── build.gradle.kts          # Android + Chaquopy configuration
│   └── src/main/
│       ├── AndroidManifest.xml    # Permissions, activities, service
│       ├── java/com/wren/android/
│       │   ├── WrenApp.kt        # Application class, notification channels
│       │   ├── MainActivity.kt   # WebView with JavaScript bridge
│       │   ├── BootstrapActivity.kt # First-launch setup screen
│       │   ├── ServerManager.kt  # Python server start/stop
│       │   ├── WrenService.kt    # Background foreground service
│       │   ├── BootReceiver.kt   # Auto-start on phone boot
│       │   └── WrenApp.kt        # App class + channels + first-run prefs
│       ├── assets/
│       │   ├── python/
│       │   │   ├── wren_server_runner.py  # Python entry point
│       │   │   └── wren/                   # Copied from Wren backend
│       │   └── www/                         # Copied from frontend/build
│       └── res/                              # Icons, themes, strings
├── build.gradle.kts
├── settings.gradle.kts
└── gradle.properties
```

## Limitations

| Aspect | Status |
|---|---|
| ARM64 only | Yes — x86 phones not supported |
| Python C extensions | Some may not have Android wheels. Pure Python works. |
| First build | Requires Android Studio + copying assets |
| APK size | ~150MB (Python + deps + Wren) |
| RAM usage | ~500MB for server + WebView |
| Battery | Significant drain during long agent runs |

## License

Same as Wren — MIT

---

Built with Chaquopy (embedded CPython for Android) + Jetpack Compose + WebView.
