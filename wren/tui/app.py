"""Wren TUI - Terminal User Interface for Wren Agent Canvas."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Static,
)

from .api import Event, WrenAPIClient

logger = logging.getLogger(__name__)


class StatusBar(Static):
    """Status bar showing connection and conversation info."""

    status_text = reactive('Disconnected')
    conversation_id = reactive('-')
    event_count = reactive(0)

    def render(self) -> str:
        return (
            f'  Status: {self.status_text}  |  '
            f'Conversation: {self.conversation_id}  |  '
            f'Events: {self.event_count}  |  '
            f'{datetime.now().strftime("%H:%M:%S")}'
        )


class ChatPanel(VerticalScroll):
    """Chat message display panel."""

    def compose(self) -> ComposeResult:
        yield RichLog(
            id='chat-log',
            highlight=True,
            markup=True,
            wrap=True,
        )

    def add_user_message(self, message: str) -> None:
        log = self.query_one('#chat-log', RichLog)
        log.write(f'[bold blue]You:[/bold blue] {message}')

    def add_agent_message(self, message: str) -> None:
        log = self.query_one('#chat-log', RichLog)
        log.write(f'[bold green]Agent:[/bold green] {message}')

    def add_action(self, event: Event) -> None:
        log = self.query_one('#chat-log', RichLog)
        action = event.action or 'unknown'
        args = event.args

        if action == 'run':
            cmd = args.get('command', '')
            log.write(f'[bold yellow]⚡ Run:[/bold yellow] {cmd}')
        elif action == 'write':
            path = args.get('path', '')
            log.write(f'[bold cyan]📝 Write:[/bold cyan] {path}')
        elif action == 'edit':
            path = args.get('path', '')
            log.write(f'[bold cyan]✏️  Edit:[/bold cyan] {path}')
        elif action == 'read':
            path = args.get('path', '')
            log.write(f'[bold magenta]📖 Read:[/bold magenta] {path}')
        elif action == 'think':
            thought = args.get('thought', event.message)
            log.write(f'[dim italic]💭 Think:[/dim italic] {thought[:200]}')
        elif action == 'message':
            content = args.get('content', event.message)
            log.write(f'[bold green]Agent:[/bold green] {content}')
        elif action == 'finish':
            log.write('[bold bright_green]✅ Task finished[/bold bright_green]')
        elif action == 'error':
            log.write(f'[bold red]❌ Error:[/bold red] {event.message}')
        else:
            log.write(f'[dim]⚡ {action}:[/dim] {event.message[:200]}')

    def add_observation(self, event: Event) -> None:
        log = self.query_one('#chat-log', RichLog)
        obs = event.observation or 'unknown'

        if obs == 'run':
            output = event.content or ''
            if len(output) > 500:
                output = output[:500] + '\n... (truncated)'
            log.write(f'[dim]📤 Output:[/dim]\n{output}')
        elif obs == 'error':
            log.write(f'[bold red]❌ Error:[/bold red] {event.content}')
        else:
            content = event.content or event.message
            if len(content) > 300:
                content = content[:300] + '... (truncated)'
            log.write(f'[dim]📋 {obs}:[/dim] {content}')

    def add_system_message(self, message: str) -> None:
        log = self.query_one('#chat-log', RichLog)
        log.write(f'[dim bright_black]ℹ️  {message}[/dim bright_black]')


class InputArea(Horizontal):
    """Message input area."""

    def compose(self) -> ComposeResult:
        yield Input(
            id='input',
            placeholder='Type a message... (Enter to send)',
        )


class WrenTUI(App):
    """Wren Terminal User Interface."""

    TITLE = 'Wren TUI'
    SUB_TITLE = 'Agent Canvas Terminal'
    CSS = """
    Screen {
        layout: vertical;
    }
    #main-container {
        height: 1fr;
    }
    #chat-panel {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
        padding: 0 1;
    }
    #input-container {
        height: auto;
        max-height: 8;
        border: solid $accent;
        padding: 0 1;
    }
    #input {
        height: auto;
        min-height: 1;
    }
    #status-bar {
        height: 1;
        background: $primary-background-darken-1;
        color: $text;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding('ctrl+c', 'quit', 'Quit'),
        Binding('ctrl+enter', 'send_message', 'Send'),
        Binding('ctrl+n', 'new_conversation', 'New Conversation'),
        Binding('ctrl+l', 'clear_chat', 'Clear Chat'),
        Binding('ctrl+h', 'help', 'Help'),
    ]

    def __init__(self, base_url: str = 'http://localhost:3000', **kwargs):
        super().__init__(**kwargs)
        self.api = WrenAPIClient(base_url=base_url)
        self._stream_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id='main-container'):
            yield ChatPanel(id='chat-panel')
            yield InputArea(id='input-container')
        yield StatusBar(id='status-bar')
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize on mount."""
        self.title = 'Wren TUI'
        self.sub_title = 'Connecting...'

        # Check backend connection
        connected = await self.api.health_check()
        if connected:
            self.query_one(
                '#status-bar', StatusBar
            ).status_text = '[green]Connected[/green]'
            self.sub_title = 'Ready'
            self.notify('Connected to Wren backend', severity='information')
        else:
            self.query_one(
                '#status-bar', StatusBar
            ).status_text = '[red]Disconnected[/red]'
            self.sub_title = 'Backend not running'
            self.notify(
                'Cannot connect to Wren backend. Start with: oh',
                severity='error',
                timeout=10,
            )

    @on(Input.Submitted, '#input')
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input."""
        await self.send_message()

    async def action_send_message(self) -> None:
        """Send the current message."""
        await self.send_message()

    async def send_message(self) -> None:
        """Send message from input area."""
        input_widget = self.query_one('#input', Input)
        message = input_widget.value.strip()
        if not message:
            return

        # Clear input
        input_widget.value = ''

        # Show user message
        chat = self.query_one('#chat-panel', ChatPanel)
        chat.add_user_message(message)

        # Create conversation if needed
        if not self.api.conversation_id:
            chat.add_system_message('Creating conversation...')
            try:
                await self.api.create_conversation(initial_message=message)
                self.query_one('#status-bar', StatusBar).conversation_id = (
                    self.api.conversation_id[:8] + '...'
                )
                chat.add_system_message(
                    f'Conversation created: {self.api.conversation_id[:8]}...'
                )
                # Start streaming events
                self._start_streaming()
                return  # Message sent via create_conversation
            except Exception as e:
                chat.add_system_message(f'Failed to create conversation: {e}')
                return

        # Send message
        try:
            await self.api.send_message(message)
        except Exception as e:
            chat.add_system_message(f'Failed to send: {e}')

    def _start_streaming(self) -> None:
        """Start streaming events in background."""
        if self._stream_task and not self._stream_task.done():
            return
        self._stream_task = asyncio.create_task(self._stream_events())

    async def _stream_events(self) -> None:
        """Continuously poll for new events."""
        chat = self.query_one('#chat-panel', ChatPanel)
        status = self.query_one('#status-bar', StatusBar)

        async for event in self.api.stream_events(poll_interval=0.5):
            try:
                if event.is_action:
                    chat.add_action(event)
                elif event.is_observation:
                    chat.add_observation(event)
                elif event.message:
                    chat.add_agent_message(event.display_text)

                status.event_count = self.api._last_event_id

                if event.action == 'finish':
                    chat.add_system_message('Task completed')
                    break
            except Exception as e:
                logger.debug(f'Error processing event: {e}')

    async def action_new_conversation(self) -> None:
        """Start a new conversation."""
        self.api.conversation_id = None
        self.api._last_event_id = 0
        if self._stream_task:
            self._stream_task.cancel()
        self.query_one('#status-bar', StatusBar).conversation_id = '-'
        self.query_one('#status-bar', StatusBar).event_count = 0
        self.query_one('#chat-panel', ChatPanel).add_system_message(
            'New conversation started'
        )

    def action_clear_chat(self) -> None:
        """Clear the chat log."""
        log = self.query_one('#chat-log', RichLog)
        log.clear()

    def action_help(self) -> None:
        """Show help."""
        chat = self.query_one('#chat-panel', ChatPanel)
        chat.add_system_message(
            'Keyboard shortcuts:\n'
            '  Enter/Ctrl+Enter - Send message\n'
            '  Ctrl+N - New conversation\n'
            '  Ctrl+L - Clear chat\n'
            '  Ctrl+C - Quit'
        )


def main():
    """Entry point for the TUI."""
    import argparse

    parser = argparse.ArgumentParser(description='Wren TUI')
    parser.add_argument(
        '--url',
        default='http://localhost:3000',
        help='Wren backend URL (default: http://localhost:3000)',
    )
    args = parser.parse_args()

    app = WrenTUI(base_url=args.url)
    app.run()


if __name__ == '__main__':
    main()
