"""GitHub Issue → PR workflow router for V1 API.

Provides endpoints to:
- Fetch issue details from a GitHub repository
- Start the Issue→PR workflow: fetch issue, generate branch name, return
  instructions for the agent to implement and create the PR

Endpoints:
    GET  /api/v1/github/issue/{owner}/{repo}/{number}  — Fetch issue details
    POST /api/v1/github/issue-to-pr                     — Start the workflow
"""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from wren.app_server.config import depends_user_context
from wren.app_server.integrations.github.github_service import GithubServiceImpl
from wren.app_server.integrations.service_types import ProviderType
from wren.app_server.user.user_context import UserContext
from wren.app_server.utils.dependencies import get_dependencies

router = APIRouter(
    prefix='/github',
    tags=['GitHub'],
    dependencies=get_dependencies(),
)
user_context_dependency = depends_user_context()


# ─── Models ──────────────────────────────────────────────────────────────────


class IssueDetail(BaseModel):
    """Details of a GitHub issue fetched from the API."""

    number: int
    title: str
    body: str
    state: str = 'open'
    repository: str
    author: str = ''
    labels: list[str] = Field(default_factory=list)
    assignees: list[str] = Field(default_factory=list)
    is_pull_request: bool = False


class IssueToPRRequest(BaseModel):
    """Request body for starting the Issue→PR workflow."""

    repository: str = Field(
        ..., description='Repository name in format owner/repo'
    )
    issue_number: int = Field(
        ..., description='Issue number to create a PR for', gt=0
    )
    target_branch: str = Field(
        default='main',
        description='Target branch for the PR (default: main)',
    )
    draft: bool = Field(
        default=False,
        description='Create PR as draft (default: false)',
    )


class IssueToPRResponse(BaseModel):
    """Response from starting the Issue→PR workflow."""

    issue: IssueDetail
    branch_name: str
    instructions: str = ''


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _sanitize_branch_name(title: str) -> str:
    """Convert an issue title into a valid git branch name.

    Examples:
        'Fix login bug' → 'fix-login-bug'
        '[BUG] Crash on startup!' → 'bug-crash-on-startup'
    """
    name = title.lower()
    name = re.sub(r'[^a-z0-9_-]', '-', name)
    name = re.sub(r'-{2,}', '-', name)
    name = name.strip('-')
    return name[:100]


async def _get_github_service(user_context: UserContext) -> GithubServiceImpl:
    """Get a GitHub service instance from the user context."""
    provider_tokens = await user_context.get_provider_tokens()
    if not provider_tokens or ProviderType.GITHUB not in provider_tokens:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='GitHub token required. Connect a GitHub account in Settings.',
        )
    token = provider_tokens[ProviderType.GITHUB]
    return GithubServiceImpl(
        user_id=token.user_id,
        token=token.token,
        base_domain=token.host,
    )


async def _fetch_issue_details(
    service: GithubServiceImpl,
    repository: str,
    issue_number: int,
) -> IssueDetail:
    """Fetch issue details using a single REST API call."""
    # Use the issue REST API directly: /repos/{repo}/issues/{number}
    # Returns title, body, labels, assignees, state, user, pull_request in one call.
    url = f'{service.BASE_URL}/repos/{repository}/issues/{issue_number}'
    try:
        raw, _ = await service._make_request(url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f'Failed to fetch issue #{issue_number}: {e}',
        )

    labels = []
    for label in raw.get('labels', []):
        if isinstance(label, dict):
            labels.append(label.get('name', ''))

    assignees = []
    for assignee in raw.get('assignees', []):
        if isinstance(assignee, dict):
            assignees.append(assignee.get('login', ''))

    return IssueDetail(
        number=issue_number,
        title=raw.get('title', ''),
        body=raw.get('body', ''),
        state=raw.get('state', 'open'),
        repository=repository,
        author=raw.get('user', {}).get('login', ''),
        labels=labels,
        assignees=assignees,
        is_pull_request='pull_request' in raw,
    )


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.get('/issue/{owner}/{repo}/{number}')
async def get_issue_details(
    owner: str,
    repo: str,
    number: int,
    user_context: UserContext = user_context_dependency,
) -> IssueDetail:
    """Fetch details of a GitHub issue.

    Returns the issue title, body, state, labels, and assignees.
    Useful for viewing issue details before creating a PR.
    """
    service = _get_github_service(user_context)
    repository = f'{owner}/{repo}'
    return await _fetch_issue_details(service, repository, number)


@router.post('/issue-to-pr')
async def start_issue_to_pr(
    request: IssueToPRRequest,
    user_context: UserContext = user_context_dependency,
) -> IssueToPRResponse:
    """Start the Issue→PR workflow.

    Given an issue number and repository, this endpoint:
    1. Fetches the issue details (title, body, labels)
    2. Generates a feature branch name based on the issue
    3. Returns structured instructions for the agent to implement

    The agent should then:
    1. Create and switch to the generated branch
    2. Implement the changes
    3. Commit and push
    4. Use the MCP `create_pr` tool to open the PR
    """
    service = _get_github_service(user_context)
    issue = await _fetch_issue_details(service, request.repository, request.issue_number)

    # Generate branch name
    branch_name = (
        f'fix/issue-{issue.number}-{_sanitize_branch_name(issue.title)}'
    )

    # Build structured instructions for the agent
    instructions = (
        f'## Issue #{issue.number}: {issue.title}\n\n'
        f'{issue.body or "No description provided."}\n\n'
        f'### Instructions\n\n'
        f'1. Create and switch to branch `{branch_name}`:\n'
        f'   ```bash\n'
        f'   git fetch origin {request.target_branch}\n'
        f'   git checkout -b {branch_name} origin/{request.target_branch}\n'
        f'   ```\n'
        f'2. Implement the changes described in the issue above\n'
        f'3. Commit and push:\n'
        f'   ```bash\n'
        f'   git add -A\n'
        f'   git commit -m "{issue.title}\\n\\nCloses #{issue.number}"\n'
        f'   git push origin {branch_name}\n'
        f'   ```\n'
        f'4. Create a pull request using the MCP `create_pr` tool:\n'
        f'   - repo_name: `{request.repository}`\n'
        f'   - source_branch: `{branch_name}`\n'
        f'   - target_branch: `{request.target_branch}`\n'
        f'   - title: `{issue.title}`\n'
        f'   - body: Include "Closes #{issue.number}" to auto-close\n'
        f'   - draft: {"yes" if request.draft else "no"}'
    )

    return IssueToPRResponse(
        issue=issue,
        branch_name=branch_name,
        instructions=instructions,
    )
