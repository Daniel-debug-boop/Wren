#!/usr/bin/env python3
"""Wren duplicate issue detection.

Monitors GitHub issues via webhooks and periodic scans
to flag potential duplicates using fuzzy matching.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

from _shared_issue_check import (
    GITHUB_API_BASE_URL,
    build_common_argparser,
    fetch_issue,
    github_headers,
    print_json_result,
    request_json,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parent = build_common_argparser()
    parser = argparse.ArgumentParser(
        parents=[parent],
        description='Wren duplicate issue check.',
    )
    parser.add_argument(
        '--event-json',
        type=str,
        default=None,
        help='GitHub event payload JSON string.',
    )
    parser.add_argument(
        '--scan',
        action='store_true',
        default=False,
        help='Run a periodic scan of open issues.',
    )
    return parser.parse_args()


def classify_event(
    event: dict[str, Any],
) -> str | None:
    """Return event action or None if unsupported."""
    action = event.get('action')
    if action in ('opened', 'edited', 'labeled'):
        return action
    return None


def fetch_recent_issues(
    owner: str,
    repo: str,
    token: str,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Fetch recent open issues for comparison."""
    path = (
        f'/repos/{owner}/{repo}/issues'
        f'?state=open&per_page={limit}'
        '&sort=updated&direction=desc'
    )
    data = request_json(
        GITHUB_API_BASE_URL, path,
        headers=github_headers(),
    )
    if data is None:
        return []
    return [item for item in data if 'pull_request' not in item]


def build_issue_text(issue: dict[str, Any]) -> str:
    """Build searchable text from issue."""
    parts = [
        issue.get('title', ''),
        issue.get('body', '') or '',
    ]
    return ' '.join(parts).lower()


def compute_similarity(text_a: str, text_b: str) -> float:
    """Simple token overlap similarity (0-1)."""
    tokens_a = set(text_a.split())
    tokens_b = set(text_b.split())
    if not tokens_a or not tokens_b:
        return 0.0
    overlap = tokens_a & tokens_b
    return len(overlap) / max(len(tokens_a), len(tokens_b))


def find_candidates(
    target: dict[str, Any],
    recent: list[dict[str, Any]],
    threshold: float = 0.4,
) -> list[dict[str, Any]]:
    """Find issues similar to target."""
    target_text = build_issue_text(target)
    candidates = []
    for issue in recent:
        if issue['number'] == target['number']:
            continue
        other_text = build_issue_text(issue)
        score = compute_similarity(target_text, other_text)
        if score >= threshold:
            candidates.append(
                {
                    'number': issue['number'],
                    'title': issue.get('title', ''),
                    'score': round(score, 3),
                    'url': issue.get('html_url', ''),
                }
            )
    candidates.sort(key=lambda c: c['score'], reverse=True)
    return candidates[:5]


def run_check(
    owner: str,
    repo: str,
    issue_number: int,
    token: str,
) -> dict[str, Any]:
    """Run duplicate check on a single issue."""
    issue = fetch_issue(f'{owner}/{repo}', issue_number)
    if issue is None:
        return {
            'status': 'error',
            'message': f'Issue #{issue_number} not found',
        }

    recent = fetch_recent_issues(owner, repo, token)
    candidates = find_candidates(issue, recent)

    result: dict[str, Any] = {
        'status': 'ok',
        'issue_number': issue_number,
        'title': issue.get('title', ''),
        'duplicate_candidates': candidates,
        'is_likely_duplicate': len(candidates) > 0,
        'checked_at': datetime.now(tz=timezone.utc).isoformat(),
    }

    if candidates:
        best = candidates[0]
        result['best_match_number'] = best['number']
        result['best_match_score'] = best['score']

    return result


def run_scan(
    owner: str,
    repo: str,
    token: str,
) -> dict[str, Any]:
    """Run periodic scan across all open issues."""
    recent = fetch_recent_issues(owner, repo, token)
    flagged: list[dict[str, Any]] = []

    for issue in recent:
        others = [i for i in recent if i['number'] != issue['number']]
        candidates = find_candidates(issue, others)
        if candidates:
            flagged.append(
                {
                    'number': issue['number'],
                    'title': issue.get('title', ''),
                    'candidates': [c['number'] for c in candidates],
                }
            )

    return {
        'status': 'ok',
        'scan': True,
        'total_issues': len(recent),
        'flagged': flagged,
        'checked_at': datetime.now(tz=timezone.utc).isoformat(),
    }


def main() -> int:
    """Entry point for the duplicate check."""
    args = parse_args()

    owner = args.owner or os.environ.get('GITHUB_REPOSITORY_OWNER', '')
    repo = args.repo or os.environ.get('GITHUB_REPOSITORY_NAME', '')
    token = args.token or os.environ.get('GITHUB_TOKEN', '')

    if not all([owner, repo, token]):
        print(
            'Error: owner, repo, and token required',
            file=sys.stderr,
        )
        return 1

    if args.event_json:
        event = json.loads(args.event_json)
        action = classify_event(event)
        if action is None:
            print_json_result(
                {
                    'status': 'skipped',
                    'reason': 'unsupported action',
                }
            )
            return 0

        issue = event.get('issue', {})
        number = issue.get('number')
        if number is None:
            print_json_result(
                {
                    'status': 'skipped',
                    'reason': 'no issue in event',
                }
            )
            return 0

        result = run_check(owner, repo, int(number), token)
    elif args.scan:
        result = run_scan(owner, repo, token)
    else:
        print(
            'Error: provide --event-json or --scan',
            file=sys.stderr,
        )
        return 1

    print_json_result(result)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
