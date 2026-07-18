"""Shared utilities for issue-check scripts.

Extracted from issue_duplicate_check_wren.py and
issue_good_first_issue_check_wren.py to
eliminate R0801 duplicate code.
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
from pathlib import Path
from typing import Any

WREN_BASE_URL = os.environ.get(
    'WREN_BASE_URL',
    'https://app.wren.dev',
)
REPOSITORY_PATTERN = re.compile(
    r'^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$'
)
GITHUB_API_BASE_URL = os.environ.get(
    'GITHUB_API_BASE_URL',
    'https://api.github.com',
)
FAILED_EXECUTION_STATUSES = {
    'error',
    'errored',
    'failed',
    'stopped',
}
SUCCESSFUL_TERMINAL_EXECUTION_STATUSES = {
    'completed',
    'finished',
}
TERMINAL_EXECUTION_STATUSES = (
    FAILED_EXECUTION_STATUSES
    | SUCCESSFUL_TERMINAL_EXECUTION_STATUSES
)
EVENT_SEARCH_LIMIT = 1000
EVENT_SEARCH_LIMIT_HIT_MESSAGE = (
    f'Event search returned at least '
    f'{EVENT_SEARCH_LIMIT} events; '
    'results may be incomplete'
)


def github_headers() -> dict[str, str]:
    """Build standard GitHub API headers."""
    headers = {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'wren-issue-check',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token:
        headers['Authorization'] = (
            f'Bearer {github_token}'
        )
    return headers


def wren_headers() -> dict[str, str]:
    """Build OpenHands API headers with auth."""
    api_key = os.environ.get('WREN_API_KEY')
    if not api_key:
        raise RuntimeError(
            'WREN_API_KEY env var is required'
        )
    return {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }


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


def escape_json_text(value: str | None) -> str:
    """Escape a string for embedding in JSON."""
    return json.dumps(
        value or '', ensure_ascii=False
    )


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


def extract_first_item(
    payload: Any,
) -> dict[str, Any] | None:
    """Extract first item from list-or-dict response."""
    if isinstance(payload, list):
        first_item = (
            payload[0] if payload else None
        )
        return (
            first_item
            if isinstance(first_item, dict)
            else None
        )
    if not isinstance(payload, dict):
        return None

    items = payload.get('items')
    if isinstance(items, list):
        first_item = (
            items[0] if items else None
        )
        return (
            first_item
            if isinstance(first_item, dict)
            else None
        )
    return payload


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
            headers={
                'Authorization':
                    wren_headers()['Authorization']
            },
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
            headers={
                'Authorization':
                    wren_headers()['Authorization']
            },
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
                'Conversation ended with '
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


def validate_event_search_results(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Validate event search results limits."""
    if len(events) >= EVENT_SEARCH_LIMIT:
        raise RuntimeError(
            EVENT_SEARCH_LIMIT_HIT_MESSAGE
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
        headers={
            'Authorization':
                wren_headers()['Authorization']
        },
    )
    if isinstance(payload, dict):
        items = payload.get('items')
        if isinstance(items, list):
            return (
                validate_event_search_results(items)
            )
        return []
    if isinstance(payload, list):
        return (
            validate_event_search_results(payload)
        )
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
        headers={
            'X-Session-API-Key': session_api_key
        },
    )
    if isinstance(payload, dict):
        items = payload.get('items')
        if isinstance(items, list):
            return (
                validate_event_search_results(items)
            )
        return []
    if isinstance(payload, list):
        return (
            validate_event_search_results(payload)
        )
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
        headers={
            'X-Session-API-Key': session_api_key
        },
    )
    if not isinstance(payload, dict):
        return ''
    return str(
        payload.get('response') or ''
    ).strip()


def extract_agent_server_url(
    conversation_url: str,
) -> str | None:
    """Extract agent server URL."""
    marker = '/api/conversations/'
    if marker not in conversation_url:
        return None
    return conversation_url.rsplit(marker, 1)[0]


def extract_last_agent_text(
    events: list[dict[str, Any]],
) -> str:
    """Extract last agent text message."""
    agent_events = [
        event
        for event in events
        if (
            event.get('kind') == 'MessageEvent'
            and event.get('source') == 'agent'
        )
    ]
    if not agent_events:
        raise RuntimeError(
            'No assistant text message was found '
            'in the conversation events'
        )

    llm_message = (
        agent_events[-1].get('llm_message')
    )
    if not isinstance(llm_message, dict):
        raise RuntimeError(
            'Last agent message has no '
            'llm_message field'
        )
    content = llm_message.get('content')
    if not isinstance(content, list):
        raise RuntimeError(
            'Last agent message content '
            'is not a list'
        )

    text_parts: list[str] = []
    for part in content:
        if not isinstance(part, dict):
            continue
        if (
            part.get('type') == 'text'
            and part.get('text')
        ):
            text_parts.append(str(part['text']))
    if not text_parts:
        raise RuntimeError(
            'Last agent message contains '
            'no text content'
        )
    return ''.join(text_parts).strip()


def parse_agent_json(
    text: str,
) -> dict[str, Any]:
    """Parse JSON object from agent text."""
    cleaned = text.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for start, character in enumerate(cleaned):
            if character != '{':
                continue
            try:
                candidate, end_idx = (
                    decoder.raw_decode(
                        cleaned[start:]
                    )
                )
            except json.JSONDecodeError:
                continue
            trailing = cleaned[
                start + end_idx:
            ].strip()
            if trailing not in {'', '```'}:
                continue
            if isinstance(candidate, dict):
                return candidate
    raise ValueError(
        'No valid JSON object found '
        'in the agent response'
    )


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


def normalize_confidence(
    normalized: dict[str, Any],
) -> str:
    """Normalize confidence level."""
    confidence = str(
        normalized.get('confidence') or 'low'
    ).strip().lower()
    if confidence not in {
        'high', 'medium', 'low'
    }:
        return 'low'
    return confidence


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


def extract_agent_text_from_conversation(
    app_conversation_id: str,
    agent_server_url: str | None,
    session_api_key: str,
    conversation_url: str,
) -> str:
    """Extract agent text from conversation.

    Tries agent server first,
    falls back to app server.
    """
    if agent_server_url and session_api_key:
        try:
            return (
                fetch_agent_server_final_response(
                    app_conversation_id,
                    agent_server_url,
                    session_api_key,
                )
            )
        except RuntimeError:
            pass

    events = fetch_app_server_events(
        app_conversation_id
    )
    try:
        return extract_last_agent_text(events)
    except RuntimeError as extract_err:
        if not session_api_key:
            raise RuntimeError(
                'App server events did not '
                'contain assistant text and '
                'session_api_key was missing '
                'from the OpenHands conversation'
            ) from extract_err
        if not agent_server_url:
            raise RuntimeError(
                'App server events did not '
                'contain assistant text and '
                'cannot extract agent server URL '
                'from conversation URL: '
                f'{conversation_url}'
            ) from extract_err
        events = fetch_agent_server_events(
            app_conversation_id,
            agent_server_url,
            session_api_key,
        )
        return extract_last_agent_text(events)


def write_json_output(
    output_path: Any,
    result: dict[str, Any],
) -> None:
    """Write JSON result to output file."""
    try:
        output_path.write_text(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
            + '\n',
            encoding='utf-8',
        )
    except OSError as io_err:
        raise RuntimeError(
            f'Failed to write output to '
            f'{output_path}: {io_err}'
        ) from io_err


def print_json_result(result: dict[str, Any]) -> None:
    """Print JSON result to stdout."""
    print(json.dumps(result, indent=2, ensure_ascii=False))


def build_common_argparser(
    description: str = '', default_output: str = ''
) -> argparse.ArgumentParser:
    """Build common argument parser."""
    parser = argparse.ArgumentParser(
        description=description
    )
    parser.add_argument(
        '--repository',
        required=True,
        help='Repository in owner/repo form',
    )
    parser.add_argument(
        '--issue-number',
        required=True,
        type=int,
        help='Issue number to inspect',
    )
    parser.add_argument(
        '--output',
        default=default_output,
        help=(
            'Path where the JSON result '
            'should be written'
        ),
    )
    parser.add_argument(
        '--poll-interval-seconds',
        default=5,
        type=int,
        help=(
            'Polling interval while waiting '
            'for conversation to finish'
        ),
    )
    parser.add_argument(
        '--max-wait-seconds',
        default=900,
        type=int,
        help=(
            'Maximum time to wait per '
            'polling phase; if a start task '
            'must be awaited first, total '
            'runtime can approach twice this'
        ),
    )
    return parser


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
            'session_api_key unexpected type: '
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


def run_issue_check(
    title: str,
    args: argparse.Namespace,
    build_prompt_fn: Any,
    normalize_fn: Any,
    summary_fn: Any,
) -> dict[str, Any]:
    """Run the common issue-check flow.

    Handles fetching the issue, starting a
    conversation, polling for results, extracting
    agent text, normalizing, writing output,
    and printing summary.
    """
    issue = fetch_issue(
        args.repository, args.issue_number
    )
    if issue.get('pull_request'):
        raise RuntimeError(
            f'#{args.issue_number} is a pull '
            'request, not an issue'
        )

    prompt = build_prompt_fn(
        args.repository, issue
    )
    start_task = start_conversation(
        title, prompt, args.repository
    )
    app_conversation_id = (
        resolve_conversation_id(
            start_task,
            args.poll_interval_seconds,
            args.max_wait_seconds,
        )
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

    agent_text = (
        extract_agent_text_from_conversation(
            app_conversation_id,
            agent_server_url,
            session_api_key,
            conversation_url,
        )
    )
    result = normalize_fn(
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

    summary_fn(result, Path(args.output))
    return result


def make_summary_printer(
    keys: list[str],
) -> Any:
    """Create a summary printer."""

    def printer(
        result: dict[str, Any],
        output_path: Any,
    ) -> None:
        """Print JSON summary."""
        summary = {
            key: result.get(key) for key in keys
        }
        summary['output'] = str(output_path)
        print(
            json.dumps(
                summary, ensure_ascii=False
            )
        )

    return printer


def run_cli_main(main_fn: Any) -> None:
    """Run main function with error handling."""
    try:
        raise SystemExit(main_fn())
    except Exception as cli_err:  # pylint: disable=broad-except
        print(
            f'error: {cli_err}',
            file=sys.stderr,
        )
        raise SystemExit(1) from cli_err


def make_issue_check_main(
    parse_args_fn: Any,
    title_template: str,
    build_prompt_fn: Any,
    normalize_fn: Any,
    summary_fn: Any,
) -> Any:
    """Create main function for issue-check.

    Returns callable that parses args, runs
    shared issue-check flow, prints summary.
    """

    def main() -> int:
        """Run issue-check main flow."""
        try:
            args = parse_args_fn()
            run_issue_check(
                title=(
                    title_template.format(
                        issue_number=(
                            args.issue_number
                        )
                    )
                ),
                args=args,
                build_prompt_fn=build_prompt_fn,
                normalize_fn=normalize_fn,
                summary_fn=summary_fn,
            )
            return 0
        except Exception as cli_err:  # pylint: disable=broad-except
            print(
                f'error: {cli_err}',
                file=sys.stderr,
            )
            raise SystemExit(1) from cli_err

    return main
