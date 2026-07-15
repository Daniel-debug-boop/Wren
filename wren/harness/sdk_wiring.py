"""SDK wiring — connects Wren SDK components to the harness layer.

Initializes ToolRegistry, CapabilityManifest, and GuardrailEnforcer,
then registers existing tools with intelligence metadata.

Usage:
    from wren.harness.sdk_wiring import get_sdk_context

    ctx = get_sdk_context()
    # ctx.registry  — ToolRegistry with all tools
    # ctx.manifest  — CapabilityManifest for system prompts
    # ctx.enforcer  — GuardrailEnforcer for safety checks
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from wren.tool.base import ToolDef, ToolCategory, ToolSafety
from wren.tool.registry import ToolRegistry
from wren.tool.manifest import CapabilityManifest
from wren.tool.guardrail import GuardrailEnforcer

_logger = logging.getLogger(__name__)

# ── Singleton SDK context ────────────────────────────────────────

_sdk_context: SDKContext | None = None


@dataclass
class SDKContext:
    """Holds all SDK components for harness integration."""

    registry: ToolRegistry
    manifest: CapabilityManifest
    enforcer: GuardrailEnforcer
    system_prompt_addendum: str = ''


def get_sdk_context() -> SDKContext:
    """Get or create the singleton SDK context."""
    global _sdk_context
    if _sdk_context is None:
        _sdk_context = _build_sdk_context()
    return _sdk_context


def _build_sdk_context() -> SDKContext:
    """Build the SDK context with all tools registered."""
    registry = ToolRegistry()
    enforcer = GuardrailEnforcer.default()

    # ── Register core tools with intelligence metadata ───────────

    # File operations
    registry.register_def(
        ToolDef(
            name='read_file',
            description='Read the contents of a file from the workspace.',
            parameters={
                'type': 'object',
                'properties': {
                    'path': {
                        'type': 'string',
                        'description': 'File path relative to workspace root',
                    },
                    'start_line': {
                        'type': 'integer',
                        'description': '1-indexed start line (optional)',
                    },
                    'end_line': {
                        'type': 'integer',
                        'description': 'Inclusive end line (optional)',
                    },
                },
                'required': ['path'],
            },
            category=ToolCategory.FILE,
            safety=ToolSafety.SAFE,
            best_for=['reading code', 'inspecting files', 'viewing configuration'],
            worse_for=['large binary files', 'directories'],
            prefer_over=['bash cat', 'bash head', 'bash tail'],
            tags=['file', 'read', 'inspect'],
        )
    )

    registry.register_def(
        ToolDef(
            name='write_file',
            description='Write content to a file in the workspace. Creates or overwrites.',
            parameters={
                'type': 'object',
                'properties': {
                    'path': {
                        'type': 'string',
                        'description': 'File path relative to workspace root',
                    },
                    'content': {
                        'type': 'string',
                        'description': 'File content to write',
                    },
                },
                'required': ['path', 'content'],
            },
            category=ToolCategory.FILE,
            safety=ToolSafety.MODERATE,
            best_for=['creating files', 'rewriting entire files'],
            worse_for=['small edits to existing files'],
            prefer_over=['bash echo', 'bash tee'],
            tags=['file', 'write', 'create'],
        )
    )

    registry.register_def(
        ToolDef(
            name='edit_file',
            description='Apply a targeted string replacement edit to a file.',
            parameters={
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'File path'},
                    'old_string': {
                        'type': 'string',
                        'description': 'Exact string to replace',
                    },
                    'new_string': {
                        'type': 'string',
                        'description': 'Replacement string',
                    },
                },
                'required': ['path', 'old_string', 'new_string'],
            },
            category=ToolCategory.FILE,
            safety=ToolSafety.MODERATE,
            best_for=['small edits', 'refactoring', 'fixing specific lines'],
            worse_for=['creating new files', 'rewriting entire files'],
            prefer_over=['bash sed', 'bash awk'],
            tags=['file', 'edit', 'modify'],
        )
    )

    registry.register_def(
        ToolDef(
            name='list_directory',
            description='List files and directories at a given path.',
            parameters={
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'Directory path'},
                },
                'required': ['path'],
            },
            category=ToolCategory.FILE,
            safety=ToolSafety.SAFE,
            best_for=['browsing directories', 'finding files'],
            worse_for=['deep recursive searches'],
            prefer_over=['bash ls', 'bash find'],
            tags=['file', 'list', 'browse'],
        )
    )

    registry.register_def(
        ToolDef(
            name='glob',
            description='Find files matching a glob pattern.',
            parameters={
                'type': 'object',
                'properties': {
                    'pattern': {
                        'type': 'string',
                        'description': 'Glob pattern (e.g. **/*.py)',
                    },
                    'path': {
                        'type': 'string',
                        'description': 'Root directory to search from',
                    },
                },
                'required': ['pattern'],
            },
            category=ToolCategory.FILE,
            safety=ToolSafety.SAFE,
            best_for=['finding files by pattern', 'discovering project structure'],
            worse_for=['searching file contents'],
            prefer_over=['bash find', 'bash glob'],
            tags=['file', 'find', 'glob', 'search'],
        )
    )

    registry.register_def(
        ToolDef(
            name='grep',
            description='Search file contents for a regex pattern.',
            parameters={
                'type': 'object',
                'properties': {
                    'pattern': {
                        'type': 'string',
                        'description': 'Regex pattern to search for',
                    },
                    'path': {'type': 'string', 'description': 'Directory to search in'},
                    'include': {
                        'type': 'string',
                        'description': 'File glob filter (e.g. *.py)',
                    },
                },
                'required': ['pattern'],
            },
            category=ToolCategory.FILE,
            safety=ToolSafety.SAFE,
            best_for=['searching code', 'finding usages', 'locating definitions'],
            worse_for=['binary files', 'very large files'],
            prefer_over=['bash grep', 'bash rg'],
            tags=['file', 'search', 'content', 'grep'],
        )
    )

    # Terminal
    registry.register_def(
        ToolDef(
            name='bash',
            description='Execute a shell command in the workspace. Use as last resort for file/git/web ops.',
            parameters={
                'type': 'object',
                'properties': {
                    'command': {
                        'type': 'string',
                        'description': 'Shell command to execute',
                    },
                    'timeout': {
                        'type': 'integer',
                        'description': 'Timeout in seconds (default 120)',
                    },
                },
                'required': ['command'],
            },
            category=ToolCategory.TERMINAL,
            safety=ToolSafety.DANGEROUS,
            best_for=[
                'running tests',
                'installing packages',
                'build commands',
                'system operations',
            ],
            worse_for=[
                'reading files',
                'writing files',
                'searching code',
                'git operations',
            ],
            prefer_over=[],  # Nothing — bash is the fallback
            tags=['terminal', 'shell', 'command', 'bash'],
        )
    )

    # GitHub operations
    for gh_tool, desc, best_for, tags in [
        (
            'github_create_issue',
            'Create a GitHub issue',
            ['creating issues', 'bug reports'],
            ['github', 'issue'],
        ),
        (
            'github_create_pull_request',
            'Create a GitHub pull request',
            ['creating PRs', 'code review'],
            ['github', 'pr'],
        ),
        (
            'github_list_pull_requests',
            'List pull requests in a repository',
            ['browsing PRs', 'review queue'],
            ['github', 'pr', 'list'],
        ),
        (
            'github_merge_pull_request',
            'Merge a pull request',
            ['merging PRs', 'deploying'],
            ['github', 'pr', 'merge'],
        ),
        (
            'github_get_issue',
            'Get details of a specific issue',
            ['reading issues', 'triaging'],
            ['github', 'issue', 'read'],
        ),
        (
            'github_list_issues',
            'List issues with filtering',
            ['browsing issues', 'backlog'],
            ['github', 'issue', 'list'],
        ),
        (
            'github_add_issue_comment',
            'Add a comment to an issue',
            ['discussing issues', 'updates'],
            ['github', 'issue', 'comment'],
        ),
        (
            'github_get_pull_request',
            'Get details of a pull request',
            ['reading PRs', 'reviewing'],
            ['github', 'pr', 'read'],
        ),
        (
            'github_get_pull_request_files',
            'Get files changed in a PR',
            ['reviewing diffs', 'PR analysis'],
            ['github', 'pr', 'diff'],
        ),
        (
            'github_create_pull_request_review',
            'Create a review on a PR',
            ['code review', 'feedback'],
            ['github', 'pr', 'review'],
        ),
    ]:
        registry.register_def(
            ToolDef(
                name=gh_tool,
                description=desc,
                parameters={'type': 'object', 'properties': {}, 'required': []},
                category=ToolCategory.GITHUB,
                safety=ToolSafety.MODERATE,
                best_for=best_for,
                worse_for=['use bash curl as last resort'],
                prefer_over=['bash curl', 'bash gh'],
                tags=tags,
            )
        )

    # Build manifest and system prompt
    manifest = CapabilityManifest(registry)
    system_prompt_addendum = manifest.to_prompt()

    _logger.info(
        'SDK wiring initialized: %d tools, %d guardrails',
        len(registry.list_all()),
        len(enforcer._guardrails),
    )

    return SDKContext(
        registry=registry,
        manifest=manifest,
        enforcer=enforcer,
        system_prompt_addendum=system_prompt_addendum,
    )
