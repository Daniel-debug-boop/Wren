"""Redaction utilities for sanitizing sensitive data in logs and output.

Provides functions to redact API keys, secrets, and URL parameters
from strings and config structures to prevent accidental exposure in
logs or displays.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Pattern

_logger = logging.getLogger(__name__)

# Patterns for common API key literal formats
API_KEY_PATTERNS: list[Pattern[str]] = [
    # OpenAI project keys
    re.compile(r'(sk-proj-[A-Za-z0-9_-]{10,})'),
    # OpenAI / OpenRouter keys
    re.compile(r'(sk-[A-Za-z0-9_-]{20,})'),
    # Wren/OpenHands session tokens
    re.compile(r'(sk-oh-[A-Za-z0-9_-]{10,})'),
    # Tavily keys
    re.compile(r'(tvly-[A-Za-z0-9_-]{10,})'),
    # GitHub personal access tokens
    re.compile(r'(ghp_[A-Za-z0-9]{20,})'),
    # GitHub fine-grained PATs
    re.compile(r'(github_pat_[A-Za-z0-9_]{20,})'),
    # Generic bearer tokens
    re.compile(r'(Bearer\s+)[A-Za-z0-9\-_.]{20,}'),
    # Authorization header values
    re.compile(r'(Authorization:\s*)[A-Za-z0-9\-_.]{20,}'),
    # x-api-key headers
    re.compile(r'(x-api-key:\s*)[A-Za-z0-9\-_.]{20,}'),
]

# Key names that indicate a value is secret (matched case-insensitively,
# and as a substring so ``TAVILY_API_KEY`` / ``X-Session-API-Key`` match).
SENSITIVE_KEY_RE: Pattern[str] = re.compile(
    r'(api[_-]?key|secret|token|password|passwd|pwd|auth|session|credential)',
    re.IGNORECASE,
)

# ``key<sep>'value'`` patterns used by redact_text_secrets.
# The key may optionally be quoted (dict repr: ``'KEY': 'value'``) and the
# value may be quoted with either quote style.
_REDACT_SECRET_PATTERN: Pattern[str] = re.compile(
    r'(?P<keyquote>[\"\']?)'
    r'(?P<key>[A-Za-z0-9_.-]*'
    r'(?:api[_-]?key|secret|token|password|passwd|pwd|session|authorization)'
    r'[A-Za-z0-9_.-]*)'
    r'(?P=keyquote)?'
    r'(?P<sep>\s*[:=]\s*)'
    r'(?P<quote>[\"\']?)'
    r'(?P<value>[^\"\'\s,;{}]+)'
    r'(?P=quote)?',
    re.IGNORECASE,
)

SECRET_PATTERNS: list[Pattern[str]] = [
    # Password-like patterns
    re.compile(r'(password|passwd|pwd)\s*[:=]\s*[\"\']?([^\"\'&\s]{4,})[\"\']?', re.IGNORECASE),
    # Secret-like patterns
    re.compile(r'(secret|token|key|api[_-]?key)\s*[:=]\s*[\"\']?([^\"\'&\s]{4,})[\"\']?', re.IGNORECASE),
]


def redact_api_key_literals(text: str, replacement: str = '<redacted>') -> str:
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
            result = pattern.sub(replacement, result)
        except Exception as exc:
            _logger.warning('Failed to apply redaction pattern %s: %s', pattern, exc)

    return result


def redact_text_secrets(text: str, placeholder: str = '<redacted>') -> str:
    """Redact secret values (passwords, tokens, keys) from structured text.

    Looks for patterns like ``key=value``, ``'KEY': 'value'`` or
    ``key: value`` where the key name suggests a secret and replaces the
    value with ``placeholder`` (default ``'<redacted>'``).

    Args:
        text: The input string potentially containing secret values.
        placeholder: The replacement text for each redacted value.

    Returns:
        The string with secret values replaced.
    """
    if not text:
        return text

    def _replace(match: re.Match[str]) -> str:
        value = match.group('value')
        if value in ('******', '<redacted>', '***REDACTED***'):
            # Already masked by an earlier pass; leave untouched.
            return match.group(0)
        keyquote = match.group('keyquote') or ''
        quote = match.group('quote') or ''
        return (
            f"{keyquote}{match.group('key')}{keyquote}"
            f"{match.group('sep')}{quote}{placeholder}{quote}"
        )

    result = _REDACT_SECRET_PATTERN.sub(_replace, text)

    # Fall back to the generic key=value patterns for anything the
    # key-name-aware pattern missed. Values already replaced with a
    # placeholder are left untouched so quotes are not stripped from
    # ``'key': '<redacted>'`` output.
    _MASKED_VALUES = ('******', '<redacted>', '***REDACTED***')
    for pattern in SECRET_PATTERNS:
        try:
            result = pattern.sub(
                lambda m: (
                    f"{m.group(1)}={placeholder}"
                    if m.group(2).rstrip(',;{} ').rstrip() not in _MASKED_VALUES
                    else m.group(0)
                ),
                result,
            )
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
            'session_api_key', 'session-key', 'sessionkey',
        })

    import urllib.parse

    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.query:
            return url

        params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        redacted = False

        for param in list(params.keys()):
            param_lower = param.lower()
            # Match exact names or names containing a sensitive token
            # (e.g. ``session_api_key`` matches ``api_key``).
            if param_lower in sensitive_params or any(
                token in param_lower for token in sensitive_params
            ):
                params[param] = ['<redacted>']
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


def sanitize_config(config: Any, placeholder: str = '<redacted>') -> Any:
    """Recursively redact secrets from a config structure (dict/list).

    Walks the structure and:
    - replaces string values whose dict key looks sensitive (``api_key``,
      ``token``, ``session``, ...) with ``placeholder``;
    - redacts URL query params that carry secrets;
    - redacts ``key=value`` secrets inside string values.

    The rest of the structure (server names, transports, hosts) is preserved
    so logs remain readable.
    """
    if isinstance(config, dict):
        sanitized: dict[str, Any] = {}
        for key, value in config.items():
            key_str = str(key)
            if isinstance(value, str) and SENSITIVE_KEY_RE.search(key_str):
                sanitized[key_str] = placeholder
            else:
                sanitized[key_str] = sanitize_config(value, placeholder)
        return sanitized
    if isinstance(config, list):
        return [sanitize_config(item, placeholder) for item in config]
    if isinstance(config, str):
        redacted_url = redact_url_params(config)
        if redacted_url != config:
            return redacted_url
        return redact_text_secrets(config, placeholder)
    return config
