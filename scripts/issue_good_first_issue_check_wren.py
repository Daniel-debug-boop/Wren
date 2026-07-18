#!/usr/bin/env python3
"""Wren good first issue classification.

Evaluates GitHub issues for good-first-issue suitability
using heuristic checks on labels, title, and body.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any

from _shared_issue_check import (
    build_common_argparser,
    fetch_issue,
    print_json_result,
)


POSITIVE_LABELS = frozenset(
    {
        'good first issue',
        'good-first-issue',
        'easy',
        'beginner',
        'help wanted',
        'starter',
    }
)

NEGATIVE_LABELS = frozenset(
    {
        'bug',
        'critical',
        'security',
        'breaking change',
        'wontfix',
        'duplicate',
        'question',
        'discussion',
    }
)

EXPERTISE_KEYWORDS = frozenset(
    {
        'security',
        'crypto',
        'auth',
        'migration',
        'database',
        'kubernetes',
        'docker',
        'ci/cd',
        'concurrency',
        'race condition',
        'memory',
        'performance',
        'optimization',
    }
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parent = build_common_argparser()
    parser = argparse.ArgumentParser(
        parents=[parent],
        description=('Wren good first issue classifier.'),
    )
    parser.add_argument(
        '--event-json',
        type=str,
        default=None,
        help='GitHub event payload JSON string.',
    )
    return parser.parse_args()


def extract_labels(
    issue: dict[str, Any],
) -> set[str]:
    """Extract lowercase label names from issue."""
    raw = issue.get('labels', [])
    return {label.get('name', '').lower() for label in raw if isinstance(label, dict)}


def score_labels(labels: set[str]) -> float:
    """Score issue based on labels (0-1)."""
    if labels & POSITIVE_LABELS:
        return 1.0
    if labels & NEGATIVE_LABELS:
        return 0.0
    return 0.5


def score_title(title: str) -> float:
    """Score issue based on title (0-1)."""
    lower = title.lower()
    positive_patterns = [
        r'\bfix\b',
        r'\badd\b',
        r'\bupdate\b',
        r'\brefactor\b',
        r'\bdocs?\b',
        r'\btest\b',
        r'\bsimplify\b',
        r'\bclean\b',
    ]
    negative_patterns = [
        r'\bsecurity\b',
        r'\bcritical\b',
        r'\bbreaking\b',
        r'\bmigration\b',
    ]

    for pattern in negative_patterns:
        if re.search(pattern, lower):
            return 0.2

    for pattern in positive_patterns:
        if re.search(pattern, lower):
            return 0.8

    return 0.5


def score_body(body: str | None) -> float:
    """Score issue based on body (0-1)."""
    if not body:
        return 0.3

    lower = body.lower()
    has_steps = bool(re.search(r'step\s*\d', lower))
    has_repro = bool(re.search(r'(reproduce|steps to|how to)', lower))
    has_expected = bool(re.search(r'(expected|actual|should)', lower))

    score = 0.4
    if has_steps:
        score += 0.2
    if has_repro:
        score += 0.2
    if has_expected:
        score += 0.2

    for keyword in EXPERTISE_KEYWORDS:
        if keyword in lower:
            score -= 0.2
            break

    return max(0.0, min(1.0, score))


def classify_issue(
    issue: dict[str, Any],
) -> dict[str, Any]:
    """Classify an issue for good-first-issue."""
    labels = extract_labels(issue)
    title = issue.get('title', '')
    body = issue.get('body', '')

    label_score = score_labels(labels)
    title_score = score_title(title)
    body_score = score_body(body)

    overall = label_score * 0.4 + title_score * 0.3 + body_score * 0.3

    is_good = overall >= 0.6
    has_negative = bool(labels & NEGATIVE_LABELS)

    return {
        'number': issue.get('number'),
        'title': title,
        'scores': {
            'label': round(label_score, 2),
            'title': round(title_score, 2),
            'body': round(body_score, 2),
            'overall': round(overall, 2),
        },
        'is_good_first_issue': is_good,
        'has_negative_labels': has_negative,
        'labels': sorted(labels),
        'classified_at': datetime.now(tz=timezone.utc).isoformat(),
    }


def main() -> int:
    """Entry point for classification."""
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
        issue_data = fetch_issue(f'{owner}/{repo}', int(number))
        if issue_data is None:
            print_json_result(
                {
                    'status': 'error',
                    'message': (f'Issue #{number} not found'),
                }
            )
            return 1
        result = classify_issue(issue_data)
    else:
        print(
            'Error: provide --event-json',
            file=sys.stderr,
        )
        return 1

    print_json_result(result)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
