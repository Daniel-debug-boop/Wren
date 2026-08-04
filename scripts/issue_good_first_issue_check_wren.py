#!/usr/bin/env python3
"""Wren good first issue classification.

Starts an OpenHands conversation to evaluate whether a GitHub issue
is suitable for the `good first issue` label, then writes a
normalized JSON result.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure this script's directory is importable when the script is loaded as a
# module (e.g. from tests) as well as when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared_issue_check import (
    EVENT_SEARCH_LIMIT,
    FAILED_EXECUTION_STATUSES,
    GITHUB_API_BASE_URL,
    REPOSITORY_PATTERN,
    SUCCESSFUL_TERMINAL_EXECUTION_STATUSES,
    WREN_BASE_URL,
    build_common_argparser,
    escape_json_text,
    extract_agent_server_url,
    extract_first_item,
    extract_last_agent_text,
    github_headers,
    normalize_confidence,
    parse_agent_json,
    write_json_output,
)

__all__ = [
    'EVENT_SEARCH_LIMIT',
    'WREN_BASE_URL',
    'as_bool',
    'build_prompt',
    'extract_first_item',
    'extract_label_names',
    'extract_last_agent_text',
    'fetch_agent_server_events',
    'fetch_agent_server_final_response',
    'fetch_app_server_events',
    'fetch_issue',
    'normalize_result',
    'parse_agent_json',
    'poll_conversation',
    'poll_start_task',
    'request_json',
    'start_conversation',
    'validate_event_search_results',
    'wren_headers',
]

POSITIVE_LABELS = frozenset(
    {
        'good first issue',
        'good-first-issue',
        'easy',
        'beginner',
    }
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    return build_common_argparser(
        description='Wren good first issue check.',
    ).parse_args()


def wren_headers() -> dict[str, str]:
    """Build OpenHands API headers with auth."""
    api_key = os.environ.get('WREN_API_KEY')
    if not api_key:
        raise RuntimeError(
            'WREN_API_KEY environment variable is required'
        )
    return {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }


def validate_event_search_results(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Validate event search results limits."""
    if len(events) >= EVENT_SEARCH_LIMIT:
        raise RuntimeError(
            'Event search returned at least '
            f'{EVENT_SEARCH_LIMIT} events; '
            'results may be incomplete'
        )
    return events


def fetch_app_server_events(
    app_conversation_id: str,
) -> list[dict[str, Any]]:
    """Fetch events from the app server."""
    payload = request_json(
        WREN_BASE_URL,
        '/api/v1/conversation/'
        f'{urllib.parse.quote(app_conversation_id)}'
        f'/events/search?limit='
        f'{EVENT_SEARCH_LIMIT}',
        headers=wren_headers(),
    )
    if isinstance(payload, dict):
        items = payload.get('items')
        if isinstance(items, list):
            return validate_event_search_results(items)
        return []
    if isinstance(payload, list):
        return validate_event_search_results(payload)
    return []


def fetch_agent_server_events(
    app_conversation_id: str,
    agent_server_url: str,
    session_api_key: str,
) -> list[dict[str, Any]]:
    """Fetch events from the agent server."""
    payload = request_json(
        agent_server_url,
        '/api/conversations/'
        f'{urllib.parse.quote(app_conversation_id)}'
        f'/events/search?limit='
        f'{EVENT_SEARCH_LIMIT}',
        headers={'X-Session-API-Key': session_api_key},
    )
    if isinstance(payload, dict):
        items = payload.get('items')
        if isinstance(items, list):
            return validate_event_search_results(items)
        return []
    if isinstance(payload, list):
        return validate_event_search_results(payload)
    return []


def fetch_agent_server_final_response(
    app_conversation_id: str,
    agent_server_url: str,
    session_api_key: str,
) -> str:
    """Fetch final agent response."""
    payload = request_json(
        agent_server_url,
        '/api/conversations/'
        f'{urllib.parse.quote(app_conversation_id)}'
        '/agent_final_response',
        headers={'X-Session-API-Key': session_api_key},
    )
    if not isinstance(payload, dict):
        return ''
    return str(payload.get('response') or '').strip()


def fetch_issue(
    repository: str, issue_number: int
) -> dict[str, Any]:
    """Fetch a GitHub issue by number."""
    if not REPOSITORY_PATTERN.fullmatch(repository):
        raise ValueError(
            f'Invalid repository format: '
            f'{repository}'
        )
    return request_json(
        GITHUB_API_BASE_URL,
        f'/repos/{repository}'
        f'/issues/{issue_number}',
        headers=github_headers(),
    )


def request_json(
    base_url: str,
    path: str,
    *,
    method: str = 'GET',
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
) -> Any:
    """Make an HTTP request and return parsed JSON."""
    data = (
        json.dumps(body).encode('utf-8')
        if body is not None
        else None
    )
    req = urllib.request.Request(
        f'{base_url}{path}',
        data=data,
        headers=headers or {},
        method=method,
    )
    try:
        with urllib.request.urlopen(
            req, timeout=60
        ) as response:
            return json.load(response)
    except urllib.error.HTTPError as http_err:
        error_body = http_err.read().decode(
            'utf-8', errors='replace'
        )
        raise RuntimeError(
            f'{method} {base_url}{path}'
            f' failed with HTTP'
            f' {http_err.code}: {error_body}'
        ) from http_err
    except json.JSONDecodeError as json_err:
        raise RuntimeError(
            f'Failed to parse JSON from '
            f'{method} {base_url}{path}: '
            f'{json_err}'
        ) from json_err
    except urllib.error.URLError as url_err:
        raise RuntimeError(
            f'{method} {base_url}{path}'
            f' failed: {url_err}'
        ) from url_err


def start_conversation(
    title: str,
    prompt: str,
    repository: str,
) -> dict[str, Any]:
    """Start an OpenHands conversation."""
    body = {
        'title': title,
        'selected_repository': repository,
        'initial_message': {
            'content': [
                {
                    'type': 'text',
                    'text': prompt,
                }
            ]
        },
    }
    return request_json(
        WREN_BASE_URL,
        '/api/v1/app-conversations',
        method='POST',
        headers=wren_headers(),
        body=body,
    )


def poll_start_task(
    start_task_id: str,
    poll_interval_seconds: int,
    max_wait_seconds: int,
) -> dict[str, Any]:
    """Poll until start task becomes READY."""
    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        payload = request_json(
            WREN_BASE_URL,
            '/api/v1/app-conversations/'
            'start-tasks?ids='
            f'{urllib.parse.quote(start_task_id)}',
            headers=wren_headers(),
        )
        item = extract_first_item(payload)
        if item is None:
            time.sleep(poll_interval_seconds)
            continue
        status = item.get('status')
        if (
            status == 'READY'
            and item.get('app_conversation_id')
        ):
            return item
        if status in {'ERROR', 'FAILED'}:
            raise RuntimeError(
                f'OpenHands start task failed: '
                f'{json.dumps(item)}'
            )
        time.sleep(poll_interval_seconds)
    raise TimeoutError(
        f'Timed out waiting for start task '
        f'{start_task_id} to become ready'
    )


def poll_conversation(
    app_conversation_id: str,
    poll_interval_seconds: int,
    max_wait_seconds: int,
) -> dict[str, Any]:
    """Poll until conversation finishes."""
    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        payload = request_json(
            WREN_BASE_URL,
            '/api/v1/app-conversations?ids='
            f'{urllib.parse.quote(app_conversation_id)},',
            headers=wren_headers(),
        )
        item = extract_first_item(payload)
        if item is None:
            time.sleep(poll_interval_seconds)
            continue
        execution_status = str(
            item.get('execution_status', '')
        ).lower()
        if execution_status in (
            FAILED_EXECUTION_STATUSES
        ):
            raise RuntimeError(
                'OpenHands conversation ended with '
                f'{execution_status}: '
                f'{json.dumps(item)}'
            )
        if execution_status in (
            SUCCESSFUL_TERMINAL_EXECUTION_STATUSES
        ):
            return item
        time.sleep(poll_interval_seconds)
    raise TimeoutError(
        f'Timed out waiting for conversation '
        f'{app_conversation_id} '
        f'to finish running'
    )


def resolve_conversation_id(
    start_task: dict[str, Any],
    poll_interval_seconds: int,
    max_wait_seconds: int,
) -> str:
    """Resolve app_conversation_id."""
    app_conversation_id = (
        start_task.get('app_conversation_id')
    )
    if app_conversation_id:
        return str(app_conversation_id)

    task_id = start_task.get('id')
    if not task_id:
        raise RuntimeError(
            f'Missing id in start task '
            f'response: {start_task}'
        )
    ready_task = poll_start_task(
        task_id,
        poll_interval_seconds,
        max_wait_seconds,
    )
    ready_id = ready_task.get(
        'app_conversation_id'
    )
    if not ready_id:
        raise RuntimeError(
            f'Missing app_conversation_id '
            f'in response: {ready_task}'
        )
    return str(ready_id)


def _extract_session_info(
    conversation: dict[str, Any],
    app_conversation_id: str,
) -> tuple[str, str, str]:
    """Extract session info from conversation."""
    session_key_val = conversation.get(
        'session_api_key'
    )
    if session_key_val and not isinstance(
        session_key_val, str
    ):
        raise RuntimeError(
            'session_api_key had unexpected type: '
            f'{type(session_key_val).__name__}'
        )
    session_api_key = session_key_val or ''
    conversation_url = (
        conversation.get('conversation_url')
        or f'{WREN_BASE_URL}/conversations/'
        f'{app_conversation_id}'
    )
    agent_server_url = (
        extract_agent_server_url(conversation_url)
    )
    return (
        session_api_key,
        conversation_url,
        agent_server_url or '',
    )


def extract_agent_text_from_conversation(
    app_conversation_id: str,
    agent_server_url: str | None,
    session_api_key: str,
    conversation_url: str,
) -> str:
    """Extract agent text from conversation.

    Tries agent server final response first, then
    app server events, then agent server events.
    """
    if agent_server_url and session_api_key:
        try:
            final_response = (
                fetch_agent_server_final_response(
                    app_conversation_id,
                    agent_server_url,
                    session_api_key,
                )
            )
            if final_response:
                return final_response
        except RuntimeError:
            pass

    events = fetch_app_server_events(
        app_conversation_id
    )
    try:
        return extract_last_agent_text(events)
    except RuntimeError:
        if session_api_key and agent_server_url:
            events = fetch_agent_server_events(
                app_conversation_id,
                agent_server_url,
                session_api_key,
            )
            return extract_last_agent_text(events)
        raise


def extract_label_names(
    issue: dict[str, Any],
) -> list[str]:
    """Extract normalized label names from an issue."""
    names: list[str] = []
    for label in issue.get('labels') or []:
        if isinstance(label, str):
            name = label
        elif isinstance(label, dict):
            name = label.get('name')
        else:
            continue
        if name:
            names.append(name)
    return sorted(names)


def build_prompt(
    repository: str,
    issue: dict[str, Any],
) -> str:
    """Build the LLM prompt for good-first-issue evaluation."""
    number = issue.get('number', '')
    title = escape_json_text(issue.get('title'))
    body = escape_json_text(issue.get('body'))
    html_url = issue.get('html_url') or ''
    label_names = extract_label_names(issue)

    prompt = f"""You are a GitHub maintainer evaluating whether an issue is a good first issue.

Repository: {repository}
Issue number: #{number}
Issue title (JSON-escaped string): {title}
Issue URL: {html_url}
Issue body (JSON-escaped string): {body}
Issue labels (JSON array): {json.dumps(label_names, ensure_ascii=False)}

Do NOT treat “not a duplicate” as positive evidence on its own.

All of the following must be true to apply `good first issue`:
1. The issue describes a clear, narrow, and self-contained task.
2. A newcomer can start without deep repository context.
3. The expected outcome or definition of done is explicit.
4. The scope is small enough to complete in a short session.

Return schema:
{{
  "should_apply_label": boolean,
  "confidence": "high" | "medium" | "low",
  "summary": string,
  "criteria_met": [string],
  "disqualifiers": [string]
}}

Return ONLY the JSON object above with no markdown fences.
"""
    return prompt


def normalize_result(
    result: dict[str, Any],
) -> dict[str, Any]:
    """Normalize and sanitize the good-first-issue result."""
    confidence = normalize_confidence(result)

    criteria_met = result.get('criteria_met')
    if not isinstance(criteria_met, list):
        criteria_met = []
    criteria_met = [
        str(item)
        for item in criteria_met
        if item is not None and str(item).strip()
    ][:5]

    disqualifiers = result.get('disqualifiers')
    if not isinstance(disqualifiers, list):
        disqualifiers = []
    disqualifiers = [
        str(item)
        for item in disqualifiers
        if item is not None and str(item).strip()
    ]

    should_apply_label = (
        as_bool(result.get('should_apply_label'))
        and confidence == 'high'
        and not disqualifiers
    )

    summary = str(
        result.get('summary') or ''
    ).strip()

    return {
        'should_apply_label': should_apply_label,
        'confidence': confidence,
        'summary': summary,
        'criteria_met': criteria_met,
        'disqualifiers': disqualifiers,
    }


def as_bool(value: Any) -> bool:
    """Coerce a value to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {
            'true', '1', 'yes'
        }
    if isinstance(value, (int, float)):
        return bool(value)
    return False


def main() -> int:
    """Run the good-first-issue check flow."""
    args = parse_args()

    issue = fetch_issue(
        args.repository, args.issue_number
    )
    if issue.get('pull_request'):
        raise RuntimeError(
            f'#{args.issue_number} is a pull '
            'request, not an issue'
        )

    prompt = build_prompt(
        args.repository, issue
    )
    start_task = start_conversation(
        f'Good first issue check for issue '
        f'#{args.issue_number}',
        prompt,
        args.repository,
    )
    app_conversation_id = resolve_conversation_id(
        start_task,
        args.poll_interval_seconds,
        args.max_wait_seconds,
    )
    conversation = poll_conversation(
        app_conversation_id,
        args.poll_interval_seconds,
        args.max_wait_seconds,
    )
    (
        session_api_key,
        conversation_url,
        agent_server_url,
    ) = _extract_session_info(
        conversation, app_conversation_id
    )

    agent_text = extract_agent_text_from_conversation(
        app_conversation_id,
        agent_server_url,
        session_api_key,
        conversation_url,
    )
    result = normalize_result(
        parse_agent_json(agent_text)
    )
    result['issue_number'] = args.issue_number
    result['repository'] = args.repository
    result['app_conversation_id'] = (
        app_conversation_id
    )
    result['conversation_url'] = (
        conversation_url
    )
    result['agent_response'] = agent_text

    write_json_output(
        Path(args.output), result
    )

    summary = {
        'issue_number': args.issue_number,
        'should_apply_label': result['should_apply_label'],
        'confidence': result['confidence'],
        'output': str(Path(args.output)),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
