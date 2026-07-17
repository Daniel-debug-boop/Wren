"""Auto-close issues previously flagged as duplicate candidates."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from typing import Any

GITHUB_API_BASE_URL = 'https://api.github.com'
MAX_PAGES = 100
DUPLICATE_CANDIDATE_LABEL = 'duplicate-candidate'
DUPLICATE_VETO_MARKER = '<!-- wren-duplicate-veto -->'
AUTOMATION_BOT_LOGINS = {'wren-bot'}
REPOSITORY_PATTERN = re.compile(r'^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$')
DUPLICATE_MARKER_RE = re.compile(
    r'<!-- wren-duplicate-check canonical=(?P<canonical>\d+) '
    r'auto-close=(?P<auto_close>true|false) -->'
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the auto-close script."""
    parser = argparse.ArgumentParser(
        description='Auto-close issues previously flagged as duplicate candidates.',
    )
    parser.add_argument('--repository', required=True)
    parser.add_argument('--close-after-days', type=int, default=3)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if not REPOSITORY_PATTERN.fullmatch(args.repository):
        parser.error(f'Invalid repository format: {args.repository}')
    return args


def github_headers() -> dict[str, str]:
    """Build standard GitHub API headers with auth token."""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise RuntimeError('GITHUB_TOKEN environment variable is required')
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'wren-duplicate-auto-close',
        'X-GitHub-Api-Version': '2022-11-28',
    }


def request_json(
    path: str,
    *,
    method: str = 'GET',
    body: dict[str, Any] | None = None,
) -> Any:
    """Make an authenticated GitHub API request and return parsed JSON."""
    request_body = None
    headers = github_headers()
    if body is not None:
        request_body = json.dumps(body).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    req = urllib.request.Request(
        f'{GITHUB_API_BASE_URL}{path}',
        data=request_body,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            payload = response.read().decode('utf-8')
    except urllib.error.HTTPError as http_err:
        error_body = http_err.read().decode('utf-8', errors='replace')
        raise RuntimeError(
            f'{method} {path} failed with HTTP {http_err.code}: {error_body}'
        ) from http_err
    except urllib.error.URLError as url_err:
        raise RuntimeError(f'{method} {path} failed: {url_err}') from url_err

    if not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError as json_err:
        raise RuntimeError(
            f'Failed to parse JSON from {path}: {json_err}'
        ) from json_err


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO 8601 timestamp string."""
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError(
            f'Failed to parse timestamp {value!r}: {exc}'
        ) from exc


def ensure_page_limit(page: int, resource_name: str) -> None:
    """Raise if pagination exceeds the configured maximum."""
    if page > MAX_PAGES:
        raise RuntimeError(
            f'Exceeded pagination limit while listing {resource_name}'
        )


def list_open_issues(repository: str) -> list[dict[str, Any]]:
    """List open issues with the duplicate-candidate label."""
    issues: list[dict[str, Any]] = []
    page = 1
    label_query = urllib.parse.quote(DUPLICATE_CANDIDATE_LABEL)
    while True:
        ensure_page_limit(page, f'open issues for {repository}')
        payload = request_json(
            f'/repos/{repository}/issues?state=open'
            f'&labels={label_query}&per_page=100&page={page}'
        )
        if not isinstance(payload, list):
            raise RuntimeError(
                f'Expected list response while listing open issues '
                f'for {repository}, got {type(payload).__name__}'
            )
        if not payload:
            return issues
        for issue in payload:
            if issue.get('pull_request'):
                continue
            issues.append(issue)
        page += 1


def list_issue_comments(
    repository: str, issue_number: int
) -> list[dict[str, Any]]:
    """List all comments for a given issue."""
    comments: list[dict[str, Any]] = []
    page = 1
    while True:
        ensure_page_limit(page, f'comments for issue #{issue_number}')
        payload = request_json(
            f'/repos/{repository}/issues/{issue_number}/comments'
            f'?per_page=100&page={page}'
        )
        if not isinstance(payload, list):
            raise RuntimeError(
                'Expected list response while listing comments for '
                f'issue #{issue_number}, got {type(payload).__name__}'
            )
        if not payload:
            return comments
        comments.extend(payload)
        page += 1


def list_comment_reactions(
    repository: str, comment_id: int
) -> list[dict[str, Any]]:
    """List all reactions for a given comment."""
    reactions: list[dict[str, Any]] = []
    page = 1
    while True:
        ensure_page_limit(page, f'reactions for comment {comment_id}')
        payload = request_json(
            f'/repos/{repository}/issues/comments/{comment_id}'
            f'/reactions?per_page=100&page={page}'
        )
        if not isinstance(payload, list):
            raise RuntimeError(
                'Expected list response while listing reactions for '
                f'comment {comment_id}, got {type(payload).__name__}'
            )
        if not payload:
            return reactions
        reactions.extend(payload)
        page += 1


def extract_duplicate_metadata(
    comment_body: str,
) -> tuple[int | None, bool]:
    """Extract canonical issue number and auto-close flag from a comment."""
    match = DUPLICATE_MARKER_RE.search(comment_body)
    if not match:
        return None, False
    return int(match.group('canonical')), match.group('auto_close') == 'true'


def find_latest_auto_close_comment(
    comments: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, int | None]:
    """Find the most recent auto-close marker comment."""
    latest_comment: dict[str, Any] | None = None
    latest_canonical_issue: int | None = None
    latest_created_at: str | None = None
    for comment in comments:
        canonical_issue, auto_close = extract_duplicate_metadata(
            comment.get('body') or ''
        )
        if canonical_issue is None or not auto_close:
            continue
        comment_created_at = comment.get('created_at')
        if not isinstance(comment_created_at, str):
            comment_created_at = None
        if latest_comment is None:
            latest_comment = comment
            latest_canonical_issue = canonical_issue
            latest_created_at = comment_created_at
            continue
        if comment_created_at is None:
            continue
        if latest_created_at is not None:
            try:
                if parse_timestamp(comment_created_at) < parse_timestamp(
                    latest_created_at
                ):
                    continue
            except ValueError:
                continue
        latest_comment = comment
        latest_canonical_issue = canonical_issue
        latest_created_at = comment_created_at
    return latest_comment, latest_canonical_issue


def issue_has_label(issue: dict[str, Any], label_name: str) -> bool:
    """Check if an issue has a specific label."""
    labels = issue.get('labels') or []
    for label in labels:
        if label == label_name:
            return True
        if isinstance(label, dict) and label.get('name') == label_name:
            return True
    return False


def user_id_from_item(item: dict[str, Any]) -> int | None:
    """Extract the user ID from a GitHub API item."""
    user = item.get('user')
    if not isinstance(user, dict):
        return None
    user_id = user.get('id')
    return user_id if isinstance(user_id, int) else None


def has_reaction_from_user(
    reactions: list[dict[str, Any]],
    user_id: int | None,
    content: str,
) -> bool:
    """Check if a specific user left a specific reaction."""
    if user_id is None:
        return False
    return any(
        user_id_from_item(r) == user_id and r.get('content') == content
        for r in reactions
    )


def has_veto_note(comments: list[dict[str, Any]]) -> bool:
    """Check if any comment contains the duplicate veto marker."""
    return any(DUPLICATE_VETO_MARKER in (c.get('body') or '') for c in comments)


def is_non_bot_comment(comment: dict[str, Any]) -> bool:
    """Check if a comment was written by a non-bot user."""
    if user_id_from_item(comment) is None:
        return False
    user = comment.get('user')
    if not isinstance(user, dict):
        return False
    login = user.get('login')
    if not isinstance(login, str):
        return False
    login_lower = login.lower()
    return (
        user.get('type') != 'Bot'
        and not login_lower.endswith('[bot]')
        and login_lower not in AUTOMATION_BOT_LOGINS
    )


def remove_candidate_label(
    repository: str, issue_number: int, *, dry_run: bool
) -> bool:
    """Remove the duplicate-candidate label from an issue."""
    if dry_run:
        return True
    try:
        request_json(
            f'/repos/{repository}/issues/{issue_number}'
            f'/labels/{DUPLICATE_CANDIDATE_LABEL}',
            method='DELETE',
        )
    except RuntimeError as exc:
        if 'HTTP 404' in str(exc):
            return False
        raise
    return True


def post_veto_note(
    repository: str,
    issue_number: int,
    *,
    dry_run: bool,
) -> bool:
    """Post a comment explaining the issue is being kept open."""
    if dry_run:
        return True
    request_json(
        f'/repos/{repository}/issues/{issue_number}/comments',
        method='POST',
        body={
            'body': (
                'Thanks — leaving this open and removing the '
                f'{DUPLICATE_CANDIDATE_LABEL} label.\n\n'
                f'{DUPLICATE_VETO_MARKER}\n'
                '_This comment was created by an AI assistant '
                '(OpenHands) on behalf of the repository maintainer._'
            )
        },
    )
    return True


def close_issue_as_duplicate(
    repository: str,
    issue_number: int,
    canonical_issue_number: int,
    *,
    dry_run: bool,
) -> None:
    """Close an issue as a duplicate of another."""
    if dry_run:
        return
    request_json(
        f'/repos/{repository}/issues/{issue_number}',
        method='PATCH',
        body={'state': 'closed', 'state_reason': 'duplicate'},
    )
    request_json(
        f'/repos/{repository}/issues/{issue_number}/comments',
        method='POST',
        body={
            'body': (
                'This issue has been automatically closed as a '
                f'duplicate of #{canonical_issue_number}.\n\n'
                'If this is incorrect, please add a comment and it '
                'can be reopened.\n\n'
                '_This comment was created by an AI assistant '
                '(OpenHands) on behalf of the repository maintainer._'
            )
        },
    )
    remove_candidate_label(repository, issue_number, dry_run=False)


def _find_newer_comments(
    comments: list[dict[str, Any]],
    since: datetime,
    issue_number: int,
) -> list[dict[str, Any]]:
    """Find non-bot comments posted after a given timestamp."""
    newer: list[dict[str, Any]] = []
    for comment in comments:
        created_at = comment.get('created_at')
        if not created_at or not is_non_bot_comment(comment):
            continue
        try:
            ts = parse_timestamp(created_at)
        except ValueError as parse_err:
            print(
                'Warning: Ignoring newer comment with invalid '
                f'timestamp on issue #{issue_number}: {parse_err}',
                file=sys.stderr,
            )
            continue
        if ts > since:
            newer.append(comment)
    return newer


def _handle_thumbs_down(
    repository: str,
    issue: dict[str, Any],
    issue_number: int,
    comments: list[dict[str, Any]],
    *,
    dry_run: bool,
) -> dict[str, Any]:
    """Handle the case where the author thumb-downed the duplicate notice."""
    label_removed = False
    if issue_has_label(issue, DUPLICATE_CANDIDATE_LABEL):
        label_removed = remove_candidate_label(
            repository, issue_number, dry_run=dry_run
        )
    veto_posted = False
    if not has_veto_note(comments):
        veto_posted = post_veto_note(repository, issue_number, dry_run=dry_run)
    return {
        'issue_number': issue_number,
        'action': 'kept-open',
        'reason': 'author-thumbed-down-duplicate-comment',
        'label_removed': label_removed,
        'veto_note_posted': veto_posted,
    }


def _handle_newer_comments(
    repository: str,
    issue: dict[str, Any],
    issue_number: int,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    """Handle newer comments after the duplicate notice."""
    label_removed = False
    if issue_has_label(issue, DUPLICATE_CANDIDATE_LABEL):
        label_removed = remove_candidate_label(
            repository, issue_number, dry_run=dry_run
        )
    return {
        'issue_number': issue_number,
        'action': 'kept-open',
        'reason': 'newer-comment-after-duplicate-notice',
        'label_removed': label_removed,
    }


def _coerce_issue_number(issue: dict[str, Any]) -> int | None:
    """Safely extract the issue number as an integer."""
    raw = issue.get('number')
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _coerce_comment_id(raw: Any) -> int | None:
    """Safely extract a comment ID as an integer."""
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _parse_comment_timestamp(
    created_at_str: str, issue_number: int
) -> datetime | None:
    """Parse a comment timestamp, printing a warning on failure."""
    try:
        return parse_timestamp(created_at_str)
    except ValueError as parse_err:
        print(
            'Warning: Skipping issue '
            f'#{issue_number} due to invalid '
            f'duplicate-comment timestamp: {parse_err}',
            file=sys.stderr,
        )
        return None


def _decide_action(
    repository: str,
    issue: dict[str, Any],
    marker_info: tuple[int, int, datetime],
    comments: list[dict[str, Any]],
    *,
    dry_run: bool,
) -> dict[str, Any] | None:
    """Decide what to do with a single issue based on reactions and comments.

    marker_info is a tuple of
    (canonical_num, marker_comment_id, comment_created_at).
    """
    issue_number = _coerce_issue_number(issue)
    if issue_number is None:
        return None
    canonical_num, marker_comment_id, comment_created_at = marker_info
    author_id = user_id_from_item(issue)
    reactions = list_comment_reactions(repository, marker_comment_id)
    thumbs_down = has_reaction_from_user(reactions, author_id, '-1')
    thumbs_up = has_reaction_from_user(reactions, author_id, '+1')

    if thumbs_down:
        result = _handle_thumbs_down(
            repository, issue, issue_number, comments, dry_run=dry_run
        )
        result['author_thumbs_up'] = thumbs_up
        return result

    if _find_newer_comments(comments, comment_created_at, issue_number):
        return _handle_newer_comments(
            repository, issue, issue_number, dry_run=dry_run,
        )

    close_issue_as_duplicate(
        repository, issue_number, canonical_num, dry_run=dry_run,
    )
    return {
        'issue_number': issue_number,
        'action': (
            'closed-as-duplicate' if not dry_run else 'would-close-as-duplicate'
        ),
        'canonical_issue_number': canonical_num,
        'author_thumbs_up': thumbs_up,
    }


def _process_issue(
    issue: dict[str, Any],
    repository: str,
    cutoff: datetime,
    *,
    dry_run: bool,
) -> dict[str, Any] | None:
    """Process a single issue for potential auto-closure."""
    issue_number = _coerce_issue_number(issue)
    if issue_number is None:
        return None

    comments = list_issue_comments(repository, issue_number)
    latest_comment, canonical_num = find_latest_auto_close_comment(comments)
    if latest_comment is None or canonical_num is None:
        return None

    created_at_str = latest_comment.get('created_at')
    marker_comment_id = _coerce_comment_id(latest_comment.get('id'))
    if not created_at_str or marker_comment_id is None:
        return None

    comment_created_at = _parse_comment_timestamp(created_at_str, issue_number)
    if comment_created_at is None or comment_created_at > cutoff:
        return None

    return _decide_action(
        repository,
        issue,
        (canonical_num, marker_comment_id, comment_created_at),
        comments,
        dry_run=dry_run,
    )


def main() -> int:
    """Run the auto-close main flow."""
    args = parse_args()
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=args.close_after_days)

    summary: list[dict[str, Any]] = []
    for issue in list_open_issues(args.repository):
        result = _process_issue(
            issue,
            args.repository,
            cutoff,
            dry_run=args.dry_run,
        )
        if result is not None:
            summary.append(result)

    print(
        json.dumps(
            {'repository': args.repository, 'results': summary},
            indent=2,
        )
    )
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as cli_err:  # pylint: disable=broad-except
        print(f'error: {cli_err}', file=sys.stderr)
        raise SystemExit(1) from cli_err
