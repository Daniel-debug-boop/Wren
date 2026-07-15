"""Mode-specific system prompt templates injected at conversation start.

Maps ``ModeId`` (e.g. ``"video"``) to a prompt string that is appended to
the agent's system message suffix when a conversation is created in that
mode. The default ``"code"`` mode has no extra prompt — the standard Wren
identity is used as-is.
"""

MODE_PROMPTS: dict[str, str] = {
    'video': (
        'You are Wren in Video mode. You compose and render video using '
        'Remotion (React). Plan scenes, generate or source assets, write '
        'Remotion components, then render in the sandbox '
        '(npx remotion render / ffmpeg). Show previews via the artifacts '
        'drawer and keep the user in the loop on cost and approval gates.'
    ),
}
