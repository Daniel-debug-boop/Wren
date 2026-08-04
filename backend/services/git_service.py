"""Git integration service.

Provides basic git operations for the workspace:
- status, diff, log
- clone, init
- commit, branch, checkout
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from backend.services.terminal_service import exec_command

_logger = logging.getLogger(__name__)


def _is_git_repo(path: str) -> bool:
    """Check if a path is inside a git repository."""
    return (Path(path) / '.git').exists()


async def git_status(workspace_root: str) -> dict[str, Any]:
    """Get git status of the workspace."""
    if not _is_git_repo(workspace_root):
        return {'is_repo': False, 'branch': None, 'files': [], 'message': 'Not a git repository'}

    result = await exec_command(
        'git status --porcelain',
        workspace_root,
        workspace_root,
    )
    if result['exit_code'] != 0:
        return {'is_repo': True, 'error': result['stderr']}

    # Get current branch
    branch_result = await exec_command(
        'git branch --show-current',
        workspace_root,
        workspace_root,
    )
    branch = branch_result['stdout'].strip() or 'detached'

    # Parse porcelain status
    files = []
    for line in result['stdout'].strip().split('\n'):
        if len(line) >= 3:
            index_status = line[0]
            work_status = line[1]
            filepath = line[3:]
            files.append({
                'path': filepath,
                'index_status': index_status,
                'work_status': work_status,
            })

    # Get ahead/behind info
    tracking_result = await exec_command(
        'git rev-list --left-right --count HEAD...@{upstream} 2>/dev/null || echo "0 0"',
        workspace_root,
        workspace_root,
    )
    parts = tracking_result['stdout'].strip().split()
    ahead = int(parts[0]) if len(parts) > 0 else 0
    behind = int(parts[1]) if len(parts) > 1 else 0

    return {
        'is_repo': True,
        'branch': branch,
        'files': files,
        'ahead': ahead,
        'behind': behind,
        'clean': len(files) == 0,
    }


async def git_init(workspace_root: str) -> dict[str, Any]:
    """Initialize a git repository in the workspace."""
    if _is_git_repo(workspace_root):
        return {'success': True, 'message': 'Repository already initialized'}

    result = await exec_command('git init', workspace_root, workspace_root)
    if result['exit_code'] != 0:
        return {'success': False, 'error': result['stderr']}

    # Create .gitignore if it doesn't exist
    gitignore = Path(workspace_root) / '.gitignore'
    if not gitignore.exists():
        gitignore.write_text(
            '# Dependencies\nnode_modules/\n.venv/\nvenv/\n__pycache__/\n\n'
            '# Build output\ndist/\nbuild/\n*.pyc\n\n'
            '# Environment\n.env\n.env.local\n\n'
            '# IDE\n.idea/\n.vscode/\n*.swp\n\n'
            '# OS\n.DS_Store\nThumbs.db\n',
            encoding='utf-8',
        )
        await exec_command('git add .gitignore', workspace_root, workspace_root)
        await exec_command(
            'git commit -m "Initial commit: add .gitignore"',
            workspace_root, workspace_root,
        )

    return {'success': True, 'message': 'Repository initialized'}


async def git_clone(
    url: str,
    target_dir: str,
    workspace_root: str,
) -> dict[str, Any]:
    """Clone a git repository into the workspace."""
    # Validate URL format
    if not re.match(r'^https://|^git@|^ssh://', url):
        return {'success': False, 'error': 'Invalid repository URL format'}

    target_path = Path(workspace_root) / target_dir
    if target_path.exists():
        return {'success': False, 'error': f'Directory "{target_dir}" already exists'}

    result = await exec_command(
        f'git clone {url} {target_dir}',
        workspace_root,
        workspace_root,
        timeout=120,
    )
    if result['exit_code'] != 0:
        return {'success': False, 'error': result['stderr']}

    return {'success': True, 'path': target_dir, 'message': f'Cloned into {target_dir}'}


async def git_commit(
    message: str,
    workspace_root: str,
    files: list[str] | None = None,
) -> dict[str, Any]:
    """Stage files and create a commit."""
    if not _is_git_repo(workspace_root):
        return {'success': False, 'error': 'Not a git repository'}

    # Stage files
    if files:
        for f in files:
            await exec_command(
                f'git add {f}',
                workspace_root,
                workspace_root,
            )
    else:
        await exec_command('git add -A', workspace_root, workspace_root)

    # Commit
    safe_msg = message.replace('"', '\"')
    result = await exec_command(
        f'git commit -m "{safe_msg}"',
        workspace_root,
        workspace_root,
    )
    if result['exit_code'] != 0:
        return {'success': False, 'error': result['stderr'] or 'Nothing to commit'}

    # Get the commit hash
    hash_result = await exec_command(
        'git rev-parse --short HEAD',
        workspace_root,
        workspace_root,
    )

    return {
        'success': True,
        'commit': hash_result['stdout'].strip(),
        'message': message,
    }


async def git_log(
    workspace_root: str,
    limit: int = 20,
) -> list[dict[str, str]]:
    """Get recent git log."""
    if not _is_git_repo(workspace_root):
        return []

    result = await exec_command(
        f'git log --oneline -{limit} --format="%h|%s|%an|%ai"',
        workspace_root,
        workspace_root,
    )
    if result['exit_code'] != 0:
        return []

    entries = []
    for line in result['stdout'].strip().split('\n'):
        parts = line.split('|', 3)
        if len(parts) >= 3:
            entries.append({
                'hash': parts[0],
                'message': parts[1],
                'author': parts[2],
                'date': parts[3] if len(parts) > 3 else '',
            })
    return entries


async def git_branches(workspace_root: str) -> dict[str, Any]:
    """List branches and show current branch."""
    if not _is_git_repo(workspace_root):
        return {'current': None, 'branches': []}

    result = await exec_command(
        'git branch',
        workspace_root,
        workspace_root,
    )
    if result['exit_code'] != 0:
        return {'current': None, 'branches': []}

    current = None
    branches = []
    for line in result['stdout'].strip().split('\n'):
        line = line.strip()
        if line.startswith('* '):
            current = line[2:]
            branches.append(current)
        elif line:
            branches.append(line)

    return {'current': current, 'branches': branches}


async def git_diff(
    workspace_root: str,
    file_path: str | None = None,
) -> str:
    """Get git diff."""
    if not _is_git_repo(workspace_root):
        return 'Not a git repository'

    cmd = 'git diff'
    if file_path:
        cmd += f' {file_path}'

    result = await exec_command(cmd, workspace_root, workspace_root)
    return result['stdout'] or ''
