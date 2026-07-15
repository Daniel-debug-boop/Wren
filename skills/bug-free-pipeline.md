---
name: bug-free-pipeline
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - /fix-mode
  - bug fix
  - bug free
  - no bugs
  - fix errors
  - code broken
  - not working
  - error message
  - crash
  - debug this
  - code review
  - quality check
  - safe code
  - too many bugs
  - check for bugs
---

# 🛡️ Bug-Free Code Pipeline — For Non-Coders

This skill ensures every piece of code Wren produces is as bug-free as possible using automated quality checks.

---

## 🔄 THE BUG-FREE PIPELINE

Every time Wren writes code, it goes through this pipeline **automatically**:

```
WRITE CODE ──► LINT ──► TYPE CHECK ──► TEST ──► VERIFY ──► DELIVER
     ▲                                               │
     └────────────── FIX & RE-TEST ──────────────────┘
```

### Step 1: Write Code
Wren writes the code based on your description.

### Step 2: Lint (Style & Common Mistakes)
```bash
# Python
ruff check . --fix
# JavaScript/TypeScript
npm run lint -- --fix
# GDScript (Godot)
godot --headless --path . --script tests/lint_check.gd --quit
```

### Step 3: Type Check (Logic Errors)
```bash
# Python
mypy . --strict
# TypeScript
tsc --noEmit --strict
# C# (Godot)
dotnet build --no-restore 2>&1
```

### Step 4: Run Tests (Behavior Verification)
```bash
# Python
pytest tests/ -v --tb=short
# JavaScript
npm test
# GDScript (Godot via GUT)
godot --headless --path . --script addons/gut/gut_cmdln.gd --quit
```

### Step 5: Fix & Re-Test
If any step fails:
1. Read the error message
2. Fix the issue
3. Re-run the failed step
4. Repeat until ALL steps pass

### Step 6: Deliver
Only when ALL checks pass, the code is delivered to you.

---

## 🎯 FOR NON-CODERS: WHAT YOU SEE

You don't need to understand the technical details. Here's what you'll see:

```
✅ Writing code... done
✅ Checking for mistakes... done (0 errors)
✅ Running tests... done (12/12 passed)
✅ Verifying... all good
✅ Code is ready!
```

If something goes wrong:
```
⚠️ Found an issue: [simple explanation]
⚡ Fixing automatically... fixed!
✅ Re-checking... all good now
```

### What Each Check Means (Plain English)

| Check | What It Does | If It Fails |
|-------|-------------|-------------|
| **Lint** | Checks for typos, formatting issues, and common mistakes you'd make by accident | Wren fixes it automatically |
| **Type Check** | Makes sure values are the right type (e.g., "health" is a number, not text) | Wren fixes the mismatch |
| **Tests** | Runs automated checks that every feature works as expected | Wren fixes the broken feature and re-tests |
| **Verify** | Final confirmation everything works together | Wren re-checks from the top |

---

## 🧪 WHAT TESTS WREN RUNS (Automatically)

### For Web Apps
```
Unit Tests: Each function works correctly
Integration Tests: Components work together  
E2E Tests: The full user flow works (login → use feature → logout)
```

### For Mobile Apps
```
Widget Tests: Each screen renders correctly
Integration Tests: Navigation and state management work
Build Test: The app compiles without errors
```

### For Game Apps (Godot)
```
Scene Tests: Each scene loads without errors
Unit Tests: Game systems work (health, damage, scoring)
Export Test: The project exports successfully (headless)
Play Test: Core loop runs without crashes
```

---

## 🔧 FIXING BUGS — THE AUTOMATED PROCESS

### When You Report a Bug
Just tell Wren what's wrong in plain English:

> "The player falls through the floor when jumping"

Wren will:
1. **Find the bug** — Searches the code for the relevant section
2. **Understand the issue** — Reads the code to understand why
3. **Fix it** — Writes the corrected code
4. **Test the fix** — Runs tests to confirm the bug is gone
5. **Check nothing else broke** — Runs ALL tests again
6. **Deliver** — Shows you what was fixed

### Types of Bugs Wren Automatically Prevents

| Bug Type | How Wren Prevents It |
|----------|---------------------|
| Null reference | Type checking catches it before code runs |
| Wrong variable name | Linter catches typos immediately |
| Missing function arguments | Type checking enforces correct parameters |
| Infinite loops | Tests catch unexpected behavior |
| Memory leaks | Godot's built-in detector + manual checks |
| Broken exports | Headless export test verifies builds work |
| Platform differences | Cross-platform testing in CI |
| Edge cases | Unit tests cover boundary conditions |

---

## 📋 QUALITY GUARANTEE CHECKLIST

Before delivering ANY code, Wren automatically verifies:

- [ ] **Lint**: Zero style/formatting errors
- [ ] **Types**: All values match expected types
- [ ] **Tests**: 100% of existing tests pass
- [ ] **No regressions**: New code doesn't break old features
- [ ] **Builds**: The project compiles/export successfully
- [ ] **Edge cases**: Input validation handles bad data
- [ ] **Error messages**: Clear, helpful error messages for failures

---

## 🧠 BEST PRACTICES WREN FOLLOWS

Even if you don't understand the code, Wren follows these rules:

1. **Never hardcode values** — Everything configurable uses `@export` or config files
2. **One responsibility per file** — Easy to find and fix issues
3. **Descriptive names** — Function and variable names explain what they do
4. **Defensive coding** — Always check for null, empty, and edge cases
5. **Logging** — If something goes wrong, there's a log message to help debug
6. **Graceful failure** — Never crash; show a friendly error instead
7. **Version control** — Every change is tracked in Git (you can undo anything)

---

## 🔄 WHAT TO DO IF CODE HAS A BUG

Just tell Wren one of these and it handles the rest:

| You Say | Wren Does |
|---------|-----------|
| "This doesn't work" | Runs full pipeline: find → fix → test → verify |
| "I get an error when I click the button" | Traces the button handler, finds the bug, fixes it |
| "The game crashes when I die" | Reads the death handler, finds the null reference, fixes it |
| "The export failed" | Checks the export config, fixes the issue, re-exports |
| "Can you check for bugs?" | Runs the full lint + type check + test suite |

---

## 🎮 Game-Specific: How Wren Tests Your Game

Since Godot games can't be visually tested in the sandbox, Wren uses:

1. **GUT framework** (GDScript unit testing):
   ```
   test_health_component.gd:
   ─ Player starts with 100 health ✅
   ─ Taking 20 damage reduces to 80 ✅
   ─ Heal restores health ✅
   ─ Can't exceed max health ✅
   ─ Death triggers when health reaches 0 ✅
   ```

2. **Headless scene loading** - Every scene is loaded headless to verify no errors

3. **Export verification** - Every export preset is tested headless before delivery

4. **Signal wiring check** - Verifies all connected signals match their targets
