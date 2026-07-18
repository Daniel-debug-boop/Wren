---
name: easy-update-pipeline
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - /update-mode
  - update my app
  - update my game
  - want to add a feature
  - can you change my game
  - can you change my app
  - release a new version
  - add a new feature to my game
  - add a new feature to my app
  - upgrade my game
  - upgrade my app
  - patch my game
  - patch my app
---

# 🔄 Easy Update Pipeline — For Non-Coders

This skill makes updating your app or game as simple as describing what you want changed.

---

## 🎯 THE PROMISE

**No coding required.** You say what you want to add, change, or fix — Wren handles everything automatically:

1. Reads your current code
2. Understands what needs to change
3. Makes the changes
4. Tests everything still works
5. Prepares the updated export
6. Gives you the new version

---

## 📦 HOW UPDATES WORK

### Everything Uses Git (Version Control)

Every project Wren creates uses Git — this means:

```
┌──────────────────────────────────────────┐
│  Git Repository                           │
│                                           │
│  v1.0 ──► v1.1 ──► v1.2 ──► v2.0       │
│   ↑         ↑         ↑         ↑        │
│  Original  Bug fix  New feat  Major      │
│  release                      update     │
└──────────────────────────────────────────┘
```

**What this means for you:**
- ✅ **Undo any change** — If an update breaks something, go back to the previous version
- ✅ **Track what changed** — See exactly what was modified in each update
- ✅ **Safe updates** — Changes are recorded, nothing is lost

---

## 📋 HOW TO REQUEST AN UPDATE

### For Non-Coders: Just Say It in English

| You Say | Wren Does |
|---------|-----------|
| "Add a pause menu" | Reads current code → adds pause menu → tests → gives you updated build |
| "Change the player speed to be faster" | Finds speed variable → changes it → tests → gives you new build |
| "Fix the jumping, it feels floaty" | Finds jump physics → adjusts gravity/jump force → tests → new build |
| "Add a new level" | Reads level system → creates new level → integrates → tests → new build |
| "Change the color scheme to blue" | Reads theme/settings → changes colors → verifies → new build |
| "Make it work on iPhone too" | Checks iOS requirements → adds iOS export config → tests export → new build |

### No Technical Knowledge Needed

You don't need to know:
- What files to change
- What code to write
- How to rebuild
- How to test

Wren handles all of that automatically.

---

## 🔄 THE UPDATE PIPELINE

```
STEP 1: UNDERSTAND ──► You say what you want to change
         ↓
STEP 2: READ ────────► Wren reads your current code
         ↓
STEP 3: PLAN ────────► Wren describes what it will change (you approve)
         ↓
STEP 4: IMPLEMENT ───► Wren makes the changes
         ↓
STEP 5: TEST ────────► Wren runs all tests (nothing breaks!)
         ↓
STEP 6: EXPORT ──────► Wren builds the new version
         ↓
STEP 7: DELIVER ─────► You get the updated app/game
```

### Step-by-Step Example

```
You: "Add a high score system to my game"

Wren: 
📖 Reading your game code... done
📋 I'll add:
   1. Score tracking in GameManager
   2. High score save/load with SaveManager
   3. High score display on Game Over screen
   4. Reset high score option in settings
   Approve? (yes/no)

You: "Yes"

Wren:
✏️ Creating score system... done
✏️ Adding save/load... done
✏️ Updating Game Over screen... done
✏️ Adding settings option... done
🧪 Running tests... all 15/15 pass ✅
📦 Exporting new build... done
✅ Update complete! Your new build is at exports/android/game.aab
```

---

## 📊 VERSION TRACKING (Automatic)

Wren automatically tracks versions so you always know what changed:

```
📄 CHANGELOG.md

## v1.1.0 (2026-07-13)
### Added
- High score system with persistent save
- Reset high score option in settings
- New Game Over screen layout

## v1.0.0 (2026-07-10)
### Added
- Initial release
- Player movement and jumping
- 10 levels with increasing difficulty
- Save/load system
```

---

## 🧪 SAFETY — Updates Never Break Existing Features

Before every update is delivered, Wren:

1. **Backs up the current version** in Git (always revertible)
2. **Tests the new code** — all existing features still work
3. **Tests nothing else broke** — full test suite run
4. **Exports successfully** — new build compiles clean
5. **Only then** — delivers the update

If ANY test fails:
```
⚠️ Test failed: "level_3_completion_test"
⚡ Investigating... found the issue
⚡ Fixing... done
🧪 Re-testing... all 16/16 pass ✅
✅ Update is safe!
```

---

## 🚀 PUBLISHING UPDATES TO STORES

### For Web Apps
```bash
# Wren handles the full update:
1. Merge changes to main branch
2. Build new version
3. Deploy to your hosting (you provide credentials)
4. Verify deployment is live
```

### For Mobile Apps (Google Play / App Store)
```bash
# Wren prepares everything, you submit:
1. Increment version number automatically
2. Build new APK/AAB/IPA
3. Generate release notes
4. Package for store submission
5. → You upload to Play Console / App Store Connect
```

### For Games (Steam / Itch.io)
```bash
# Wren prepares the update:
1. Build new version for all platforms
2. Generate patch notes
3. Package builds
4. → You upload to Steam / Itch.io dashboard
```

---

## 🗂️ WHAT WREN TRACKS (So Updates Are Safe)

| What Wren Tracks | Why |
|-----------------|-----|
| Every version in Git | You can go back to any previous version |
| Export configurations | Updates don't break build settings |
| Dependencies/packages | Updates don't break library versions |
| Test results | Every update is verified |
| Change log | Automatic release notes |
| Export artifacts | Previous builds are archived |

---

## 💡 REAL-WORLD UPDATE SCENARIOS

### Scenario 1: "My game needs a new level"
```
You: "Add level 11, make it harder with more enemies"

Wren:
1. Reads your existing levels (1-10)
2. Creates level 11 following the same pattern
3. Adds more enemies than level 10
4. Links it to the level select screen
5. Tests that level 1-10 still work
6. Exports new build
✅ Done! Level 11 is ready to play
```

### Scenario 2: "Change the app's color theme"
```
You: "Make my app dark mode"

Wren:
1. Reads your current theme/styling
2. Creates a dark color palette
3. Applies it to all screens
4. Adds a light/dark toggle if you want
5. Tests all screens render correctly
6. Exports new build
✅ Done! Dark mode is ready
```

### Scenario 3: "Fix the crash when I press start"
```
You: "The game crashes when I tap Start on Android"

Wren:
1. Reads the Start button handler
2. Traces the crash in the Android export
3. Finds the null reference issue
4. Fixes the code
5. Exports for Android and tests
6. Confirms the fix works
✅ Done! Crash is fixed
```

---

## 🔧 SUMMARY: Non-Coder's Guide to Updates

| Step | What You Do | What Wren Does |
|------|------------|----------------|
| 1 | "I want to add X" | Reads your entire project |
| 2 | — | Plans the changes and shows you |
| 3 | "Yes, do it" | Makes all changes |
| 4 | — | Tests everything still works |
| 5 | — | Builds the new version |
| 6 | Get the new files | Delivers the update |

**You never need to:**
- Open a code editor
- Write a single line of code
- Understand file structures
- Run build commands
- Fix broken things after updates

Wren does ALL of that automatically.
