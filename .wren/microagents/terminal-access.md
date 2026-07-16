---
triggers:
- terminal
- shell
- command
- bash
- run command
- exec
- npm install
- pip install
- git push
- run a command
---

# Terminal & Shell Access

Wren provides full shell terminal access through the sandbox environment. You can run any command and see its output in real-time.

## How Terminal Output Works

1. When you execute a command (via `run`, `bash`, or the terminal MCP), the output streams back as **observation events**
2. These events appear in the **Terminal panel** in the UI (both chat mode and IDE mode)
3. The output is displayed line-by-line with proper formatting
4. Command history is preserved for the session

## Running Commands

Use the built-in `run` action to execute shell commands:

```json
{
  "action": "run",
  "args": {
    "command": "npm install"
  }
}
```

The output will stream back as observation events with the command's stdout/stderr.

## Best Practices

- **Always check the terminal output** after running commands to verify success/failure
- **Long-running commands** (builds, installs, tests) stream output in real-time — watch for errors
- **Git commands** are safe to run: clone, push, commit, branch, etc.
- **File operations** (cat, cp, mv, rm) work as expected
- Use `cd` to navigate the workspace before running commands
- Use `ls`, `find`, `grep` to explore the codebase
- Use `npm test`, `pytest`, etc. to run tests
- Use `git status`, `git diff` to check the current state
