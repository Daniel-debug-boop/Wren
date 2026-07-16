"""wren code — Agentic coding from the terminal.

Usage:
    wren code "build a React component"    # One-shot prompt
    wren code                               # Interactive REPL mode
    wren code --goal "refactor this" --file src/main.ts  # With context
    echo "fix the bug" | wren code          # Pipe mode
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import time
from typing import AsyncGenerator

import httpx

logger = logging.getLogger(__name__)

# ─── Terminal formatting ────────────────────────────────────────────────────
# Reuse shared helpers from main.py
from wren.cli.main import _bold, _red, _green, _yellow  # noqa: F401

# Use stdout for isatty (console output), consistent with main.py behavior
_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if not _COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def _dim(text: str) -> str:
    return _c("2", text)


def _italic(text: str) -> str:
    return _c("3", text)


def _blue(text: str) -> str:
    return _c("34", text)


def _magenta(text: str) -> str:
    return _c("35", text)


def _cyan(text: str) -> str:
    return _c("36", text)


# ─── Spinner ────────────────────────────────────────────────────────────────

_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class Spinner:
    """Simple terminal spinner."""

    def __init__(self, message: str = ""):
        self._message = message
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        if not _COLOR or not sys.stdout.isatty():
            return
        self._running = True
        self._task = asyncio.create_task(self._spin())

    async def _spin(self):
        idx = 0
        while self._running:
            frame = _SPINNER_FRAMES[idx % len(_SPINNER_FRAMES)]
            sys.stdout.write(f"\r{_cyan(frame)} {self._message} ... ")
            sys.stdout.flush()
            idx += 1
            await asyncio.sleep(0.08)

    async def stop(self, done: bool = True):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if _COLOR and sys.stdout.isatty():
            icon = _green("✓") if done else _red("✗")
            sys.stdout.write(f"\r{icon} {self._message}              \n")
            sys.stdout.flush()


# ─── Event types ────────────────────────────────────────────────────────────


class AgentEvent:
    """Parsed event from the agent backend."""

    def __init__(self, data: dict):
        self.raw = data
        self.event_type = data.get("type", "")
        self.source = data.get("source", "agent")

        # Message events
        msg = data.get("message", {})
        self.role = msg.get("role", "") if isinstance(msg, dict) else ""
        self.content = ""
        if isinstance(msg, dict):
            parts = msg.get("content", [])
            if isinstance(parts, list):
                self.content = " ".join(
                    p.get("text", "") for p in parts if isinstance(p, dict)
                )

        # Action events
        action = data.get("action", {}) or {}
        self.action_type = action.get("action_type", "") if isinstance(action, dict) else ""
        self.thought = action.get("thought", "") if isinstance(action, dict) else ""
        self.action_title = action.get("title", "") if isinstance(action, dict) else ""

        # Observation events
        obs = data.get("observation", {}) or {}
        self.observation_type = obs.get("observation_type", "") if isinstance(obs, dict) else ""
        self.obs_content = obs.get("content", "") if isinstance(obs, dict) else ""

        # Error events
        err = data.get("error", {}) or {}
        self.error_message = err.get("message", "") if isinstance(err, dict) else ""

    @property
    def is_user_message(self) -> bool:
        return self.event_type == "message" and self.role == "user"

    @property
    def is_assistant_message(self) -> bool:
        return self.event_type == "message" and self.role == "assistant"

    @property
    def is_action(self) -> bool:
        return self.event_type == "action"

    @property
    def is_observation(self) -> bool:
        return self.event_type == "observation"

    @property
    def is_error(self) -> bool:
        return self.event_type == "error"

    @property
    def display_text(self) -> str:
        if self.is_action:
            return self.thought or self.action_title or f"[{self.action_type}]"
        if self.is_assistant_message:
            return self.content
        if self.is_observation:
            return self.obs_content[:500]
        return self.content or self.obs_content or ""


# ─── API client ─────────────────────────────────────────────────────────────


class CodeSession:
    """Manages a Wren agentic coding session from the terminal."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:3000",
        goal: str = "",
        workspace: str = "",
        model: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self.goal = goal
        self.workspace = workspace or os.getcwd()
        self.model = model
        self.conversation_id: str = ""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=120.0,
            headers={"Content-Type": "application/json"},
        )
        self._last_event_id: str = ""

    async def close(self):
        await self._client.aclose()

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get("/api/v1/health", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def create_conversation(self) -> bool:
        """Create a new conversation and return success."""
        body: dict = {
            "selected_repository": self.workspace,
        }
        if self.goal:
            body["initial_message"] = {
                "role": "user",
                "content": [{"type": "text", "text": self.goal}],
            }
        if self.model:
            body["llm_model"] = self.model

        try:
            resp = await self._client.post(
                "/api/v1/app-conversations", json=body, timeout=30.0
            )
            resp.raise_for_status()
            data = resp.json()
            self.conversation_id = data.get("conversation_id") or data.get("id", "")
            return bool(self.conversation_id)
        except Exception as e:
            logger.error("Failed to create conversation: %s", e)
            return False

    async def send_message(self, message: str) -> bool:
        """Send a follow-up message."""
        if not self.conversation_id:
            return False
        body = {
            "role": "user",
            "content": [{"type": "text", "text": message}],
        }
        try:
            resp = await self._client.post(
                f"/api/v1/conversations/{self.conversation_id}/events",
                json=body,
                timeout=30.0,
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error("Failed to send message: %s", e)
            return False

    async def stream_events(
        self, poll_interval: float = 0.3
    ) -> AsyncGenerator[AgentEvent, None]:
        """Poll for new events."""
        seen_ids: set[str] = set()
        _PRUNE_THRESHOLD = 1000

        while True:
            try:
                params = {"limit": 50}
                if self._last_event_id:
                    params["after_id"] = self._last_event_id

                resp = await self._client.get(
                    f"/api/v1/conversation/{self.conversation_id}/events/search",
                    params=params,
                    timeout=10.0,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items", []) or data.get("events", [])
                    for item in items:
                        event_id = str(item.get("id", ""))
                        if event_id and event_id not in seen_ids:
                            seen_ids.add(event_id)
                            self._last_event_id = event_id
                            yield AgentEvent(item)

                # Prune seen_ids to prevent unbounded memory growth
                if len(seen_ids) > _PRUNE_THRESHOLD:
                    # Keep only the most recent 500 IDs
                    sorted_ids = sorted(seen_ids, reverse=True)
                    seen_ids = set(sorted_ids[:500])

            except Exception as e:
                logger.debug("Poll error: %s", e)

            await asyncio.sleep(poll_interval)

    async def wait_for_completion(
        self, timeout: float = 300.0
    ) -> AsyncGenerator[AgentEvent, None]:
        """Stream events until a finish/error event or timeout."""
        start = time.monotonic()
        async for event in self.stream_events():
            elapsed = time.monotonic() - start
            if elapsed > timeout:
                print(f"\n{_yellow('⚠️  Timeout reached.')}")
                break

            yield event

            # Check for terminal events
            if event.is_error:
                break
            if event.action_type == "finish":
                break


# ─── Output formatting ──────────────────────────────────────────────────────


def print_event(event: AgentEvent, show_actions: bool = True) -> None:
    """Print an agent event to stdout with formatting."""
    if event.is_user_message:
        print(f"\n{_bold(_blue('You:'))} {event.content}")
    elif event.is_assistant_message and event.content:
        # Only print if there's actual content (not empty responses)
        text = event.content.strip()
        if text:
            print(f"\n{_bold(_green('Agent:'))}")
            # Word-wrap at terminal width
            width = min(os.get_terminal_size().columns, 100) - 4
            for line in text.split("\n"):
                while len(line) > width:
                    print(f"  {line[:width]}")
                    line = line[width:]
                print(f"  {line}")
    elif event.is_action and show_actions:
        action = event.action_type
        if action == "think":
            thought = event.thought[:200]
            if thought:
                print(f"  {_dim(_italic(f'💭 {thought}'))}")
        elif action == "run":
            print(f"  {_yellow('⚡')} {event.action_title or 'Running command...'}")
        elif action == "write":
            print(f"  {_cyan('📝')} {event.action_title or 'Writing file...'}")
        elif action == "edit":
            print(f"  {_cyan('✏️')} {event.action_title or 'Editing file...'}")
        elif action == "read":
            print(f"  {_magenta('📖')} {event.action_title or 'Reading file...'}")
        elif action == "browse":
            print(f"  {_blue('🌐')} {event.action_title or 'Browsing...'}")
        elif action == "finish":
            print(f"\n{_bold(_green('✅ Done'))}")
    elif event.is_observation and show_actions:
        obs = event.observation_type
        if obs == "run":
            output = event.obs_content[:300]
            if output.strip():
                print(f"  {_dim(output)}")
        elif obs == "error":
            print(f"  {_red('❌')} {event.obs_content[:200]}")
    elif event.is_error:
        print(f"\n{_red('✗ Error:')} {event.error_message}")


# ─── Interactive REPL ───────────────────────────────────────────────────────


def _read_multiline_input(prompt: str = ">>> ") -> str:
    """Read multi-line input from terminal. Empty line with just Enter sends."""
    print()
    lines = []
    print(f"{_bold(_blue(prompt))}", end="", flush=True)
    try:
        while True:
            line = sys.stdin.readline()
            if not line:  # EOF (Ctrl+D)
                break
            line = line.rstrip("\n")
            if not line and lines:
                break
            if line:
                lines.append(line)
            print(f"{_bold(_blue('... '))}", end="", flush=True)
    except KeyboardInterrupt:
        print()
        return ""
    return "\n".join(lines)


# ─── Main command handler ───────────────────────────────────────────────────


async def cmd_code(args: argparse.Namespace) -> None:
    """Execute the `wren code` command."""
    goal = args.goal or ""
    workspace = args.workspace or os.getcwd()
    base_url = f"http://{args.host}:{args.port}"
    no_spinner = args.no_spinner

    print(f"\n  {_bold(_cyan('⚡ Wren Agentic Coding'))}")
    print(f"  {_dim('Workspace:')} {workspace}")
    if goal:
        print(f"  {_dim('Goal:')} {goal[:100]}")
    print()

    # Check backend health
    session = CodeSession(
        base_url=base_url,
        goal=goal,
        workspace=workspace,
        model=args.model or "",
    )

    spinner = Spinner("Connecting to backend")
    if not no_spinner:
        await spinner.start()

    healthy = await session.health_check()
    if not no_spinner:
        await spinner.stop(done=healthy)

    if not healthy:
        print(f"  {_red('✗ Backend not reachable at')} {base_url}")
        print(f"  {_yellow('Start it first:')} oh --port {args.port}")
        print()
        return

    print(f"  {_green('✓')} Connected to {_cyan(base_url)}")
    print()

    # Create conversation
    spinner = Spinner("Starting coding session")
    if not no_spinner:
        await spinner.start()

    created = await session.create_conversation()
    if not no_spinner:
        await spinner.stop(done=created)

    if not created:
        print(f"  {_red('✗ Failed to create conversation')}")
        await session.close()
        return

    conv_id_short = session.conversation_id[:8] if session.conversation_id else "?"
    print(f"  {_dim(f'Conversation: {conv_id_short}...')}")
    print()

    # If a goal was provided via --goal or pipe, stream results
    if goal:
        event_count = 0
        async for event in session.wait_for_completion():
            print_event(event)
            event_count += 1

        if event_count == 0:
            print(f"  {_yellow('No events received. The agent may still be starting.')}")

    # Interactive REPL mode
    else:
        print(f"  {_bold('Interactive mode')} — type your prompts, Enter to send")
        print(f"  {_dim('Ctrl+C to quit, empty line sends the message')}")
        print()

        while True:
            try:
                message = _read_multiline_input()
                if not message:
                    continue

                sent = await session.send_message(message)
                if sent:
                    async for event in session.wait_for_completion(timeout=600.0):
                        print_event(event)
                else:
                    print(f"  {_red('Failed to send message')}")

            except KeyboardInterrupt:
                print(f"\n  {_yellow('Session ended.')}")
                break
            except EOFError:
                break

    await session.close()


# ─── Parser ─────────────────────────────────────────────────────────────────


def register_code_subcommand(sub) -> None:
    """Register the `code` subcommand."""
    parser = sub.add_parser(
        "code",
        help="Start an agentic coding session in the terminal",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "goal",
        nargs="?",
        default="",
        help="The goal/prompt for the agent (omit for interactive mode)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("BACKEND_HOST", "127.0.0.1"),
        help="Backend host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("BACKEND_PORT", "3000")),
        help="Backend port (default: 3000)",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=os.getcwd(),
        help="Workspace directory (default: current dir)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="",
        help="LLM model to use (default: from settings)",
    )
    parser.add_argument(
        "--no-spinner",
        action="store_true",
        default=False,
        help="Disable the spinner animation",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Show detailed output",
    )
