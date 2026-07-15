"""Tests for orchestration hooks — WorkingMemoryProcessor and ReflectionProcessor.

These processors hook into the event stream. We test the utility functions
and basic logic that can be unit tested without a running event system.
"""

from wren.app_server.orchestration.hooks import _is_terminal


class TestIsTerminal:
    """Tests for the _is_terminal helper function."""

    def test_terminal_completed(self):
        assert _is_terminal('COMPLETED') is True

    def test_terminal_error(self):
        assert _is_terminal('ERROR') is True

    def test_terminal_stuck(self):
        assert _is_terminal('STUCK') is True

    def test_terminal_cancelled(self):
        assert _is_terminal('CANCELLED') is True

    def test_terminal_stopped(self):
        assert _is_terminal('STOPPED') is True

    def test_non_terminal_running(self):
        assert _is_terminal('RUNNING') is False

    def test_non_terminal_paused(self):
        assert _is_terminal('PAUSED') is False

    def test_non_terminal_awaiting_input(self):
        assert _is_terminal('AWAITING_USER_INPUT') is False

    def test_non_terminal_initializing(self):
        assert _is_terminal('INITIALIZING') is False

    def test_non_terminal_planning(self):
        assert _is_terminal('PLANNING') is False

    def test_empty_string(self):
        assert _is_terminal('') is False

    def test_lowercase(self):
        """Test that lowercase status values are also handled."""
        assert _is_terminal('completed') is True
        assert _is_terminal('error') is True
        assert _is_terminal('running') is False
