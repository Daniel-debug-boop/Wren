"""Tests for mode-specific system prompt templates."""

from wren.app_server.app_conversation.mode_prompts import MODE_PROMPTS


def test_mode_prompts_has_video_key():
    """Video mode must have a prompt entry."""
    assert 'video' in MODE_PROMPTS


def test_mode_prompts_code_not_present():
    """Code mode must NOT have a prompt entry (uses default identity)."""
    assert 'code' not in MODE_PROMPTS


def test_mode_prompts_video_content():
    """Video prompt must reference Remotion and rendering."""
    prompt = MODE_PROMPTS['video']
    assert 'Remotion' in prompt
    assert 'render' in prompt or 'ffmpeg' in prompt


def test_mode_prompts_all_values_are_nonempty_strings():
    """Every mode prompt must be a non-empty string."""
    for mode_id, prompt in MODE_PROMPTS.items():
        assert isinstance(prompt, str)
        assert len(prompt) > 0
