"""Redaction utilities for sanitizing sensitive data in logs and output.

Provides functions to redact API keys, secrets, and URL parameters
from strings to prevent accidental exposure in logs or displays.
"""

from __future__ import annotations

import logging
import re
from typing import Pattern

_logger = logging.getLogger(__name__)

# Patterns for common API key formats
API_KEY_PATTERNS: list[Pattern[str]] = [
    # OpenAI / OpenRouter keys
    re.compile(r'(sk-[A-Za-z0-9]{20,})'),
    # Anthropic keys
    re.compile(r'(sk-ant-[A-Za-z0-9]{20,})'),
    # Generic bearer tokens
    re.compile(r'(Bearer\s+)[A-Za-z0-9\-_.]{20,}'),
    # Authorization header values
    re.compile(r'(Authorization:\s*)[A-Za-z0-9\-_.]{20,}'),
    # x-api-key headers
    re.compile(r'(x-api-key:\s*)[A-Za-z0-9\-_.]{20,}'),
]

SECRET_PATTERNS: list[Pattern[str]] = [
    # Password-like patterns
    re.compile(r'(password|passwd|pwd)\s*[:=]\s*["\']?([^"\'&\s]{4,})["\']?', re.IGNORECASE),
    # Secret-like patterns
    re.compile(r'(secret|token|key|api[_-]?key)\s*[:=]\s*["\']?([^"\'&\s]{4,})["\']?', re.IGNORECASE),
]


def redact_api_key_literals(text: str, replacement: str = 'sk-...****') -> str:
    """Redact API key literals from a string.

    Args:
        text: The input string potentially containing API keys.
        replacement: The replacement text for each redacted key.

    Returns:
        The string with API keys replaced.
    """
    if not text:
        return text

    result = text
    for pattern in API_KEY_PATTERNS:
        try:
            result = pattern.sub(rf'\1{replacement}', result)
        except Exception as exc:
            _logger.warning('Failed to apply redaction pattern %s: %s', pattern, exc)

    return result


def redact_text_secrets(text: str, placeholder: str = '***REDACTED***') -> str:
    """Redact secret values (passwords, tokens, keys) from structured text.

    Looks for patterns like ``key=value`` or ``"key": "value"`` where the
    key name suggests a secret and replaces the value.

    Args:
        text: The input string potentially containing secret values.
        placeholder: The replacement text for each redacted value.

    Returns:
        The string with secret values replaced.
    """
    if not text:
        return text

    result = text
    for pattern in SECRET_PATTERNS:
        try:
            result = pattern.sub(rf'\1={placeholder}', result)
        except Exception as exc:
            _logger.warning('Failed to apply secret pattern %s: %s', pattern, exc)

    return result


def redact_url_params(url: str, sensitive_params: frozenset[str] | None = None) -> str:
    """Redact sensitive query parameters from a URL.

    Args:
        url: The URL potentially containing sensitive query parameters.
        sensitive_params: Set of parameter names to redact.
            Defaults to common sensitive params.

    Returns:
        The URL with sensitive parameter values replaced.
    """
    if not url:
        return url

    if sensitive_params is None:
        sensitive_params = frozenset({
            'api_key', 'api-key', 'apikey',
            'token', 'access_token', 'secret',
            'password', 'passwd', 'pwd',
            'key', 'auth', 'session',
        })

    import urllib.parse

    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.query:
            return url

        params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        redacted = False

        for param in list(params.keys()):
            if param.lower() in sensitive_params:
                params[param] = ['***REDACTED***']
                redacted = True

        if not redacted:
            return url

        new_query = urllib.parse.urlencode(params, doseq=True)
        return urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        ))
    except Exception as exc:
        _logger.warning('Failed to redact URL params: %s', exc)
        return url
