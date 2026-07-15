"""Adaptive error recovery loop: try → classify → mutate → retry → record.

When an agent hits an error:
1. Classify the error type (import, syntax, timeout, permission, etc.)
2. Look up known solutions for that error signature
3. Try the best-known strategy first
4. If it fails, mutate to a different strategy
5. Repeat until success or exhaustion
6. Record the winning strategy as a skill + FableMemory lesson
7. Next time the same error signature appears, try recorded strategy first
8. If recorded strategy fails (context changed), mutate and re-record
"""

import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

from wren.app_server.orchestration.working_memory import WorkingMemory

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error Classification
# ---------------------------------------------------------------------------


class ErrorSignature:
    """Classifies an error into a canonical signature for solution lookup.

    The signature is a hash of the error type + key identifiers, so the
    same error type in different contexts maps to the same signature.
    """

    ERROR_PATTERNS = [
        (r'ModuleNotFoundError|ImportError.*No module', 'import_missing'),
        (r'ImportError.*cannot import name', 'import_name'),
        (r'ModuleNotFoundError.*No module named', 'import_missing'),
        (r'SyntaxError|invalid syntax', 'syntax'),
        (r'IndentationError|unexpected indent', 'indentation'),
        (r'NameError.*is not defined', 'name_undefined'),
        (r'TypeError.*is not.*callable', 'type_not_callable'),
        (r'TypeError.*missing.*required.*argument', 'type_missing_arg'),
        (r'AttributeError.*has no attribute', 'attr_missing'),
        (r'KeyError', 'key_missing'),
        (r'IndexError|list index out of range', 'index_out_of_range'),
        (r'ValueError.*invalid literal', 'value_invalid'),
        (r'FileNotFoundError|No such file|ENOENT', 'file_not_found'),
        (r'PermissionError|permission denied|EACCES', 'permission'),
        (
            r'ConnectionError|ConnectionRefused|ECONNREFUSED|Connection refused',
            'connection',
        ),
        (r'TimeoutError|timed out|timeout', 'timeout'),
        (r'OSError|errno', 'os_error'),
        (r'RuntimeError', 'runtime'),
        (r'RecursionError|maximum recursion depth', 'recursion'),
        (r'MemoryError|OutOfMemory|OOM', 'memory'),
        (r'KeyboardInterrupt|SIGINT', 'interrupt'),
        (r'json\.decode|JSONDecodeError|Expecting value', 'json_decode'),
        (r'pip.*install.*failed|Could not find.*package', 'pip_install'),
        (r'npm ERR|npm ERR!', 'npm_error'),
        (r'docker.*Error|Cannot connect to the Docker', 'docker'),
        (r'command not found|which: no', 'command_missing'),
        (r'assert.*Error|AssertionError', 'assertion'),
        (r'Permission denied.*publickey|Host key verification', 'ssh'),
    ]

    STRATEGY_MUTATIONS = {
        'import_missing': [
            'Install the missing package via pip',
            'Check Python version compatibility, install correct version',
            'Add the package to requirements.txt and install',
            'Use a vendored copy if package is not available on PyPI',
        ],
        'import_name': [
            'Check the correct import path in documentation',
            'The class/function may have been renamed or moved',
            'Use try/except ImportError with fallback import',
        ],
        'syntax': [
            'Use a linter (ruff, flake8) to find and fix syntax errors',
            'Wrap in proper function/class structure',
            'Check for missing colons, brackets, or parentheses',
        ],
        'indentation': [
            'Reformat the file with black/ruff formatter',
            'Check for mixed tabs and spaces',
            'Ensure consistent indentation level',
        ],
        'name_undefined': [
            'Check variable/function name spelling',
            'Verify the name is in scope (imported or defined earlier)',
            'The name may be conditional — check if block always executes',
        ],
        'type_missing_arg': [
            'Check function signature for required parameters',
            'Add the missing argument with a default value',
            'Use **kwargs to accept unknown arguments',
        ],
        'type_not_callable': [
            'The variable shadows a function name — rename the variable',
            'The class was instantiated without ()',
            'Check if the import resolved to the expected type',
        ],
        'attr_missing': [
            'Check if the object was properly initialized',
            'The attribute may be created conditionally',
            'The class/type may not be what you expect — print(type(obj))',
        ],
        'key_missing': [
            'Use dict.get(key, default) instead of direct access',
            'Check if the key exists with ' in ' before accessing',
            'The data structure may be empty or differently shaped',
        ],
        'file_not_found': [
            'Check if the file path is absolute or relative correctly',
            'Verify the file exists with os.path.exists() before opening',
            'Use pathlib.Path for cross-platform paths',
            'The working directory may differ from expected',
        ],
        'permission': [
            'Check file permissions with os.access()',
            'Run the operation in a sandbox directory where write is allowed',
            'Use a temporary directory for file operations',
        ],
        'timeout': [
            'Increase the timeout value',
            'Add retry with exponential backoff',
            'The operation may need different parameters — check input size',
        ],
        'connection': [
            'Check if the service is running and reachable',
            'Add retry with exponential backoff',
            'Check firewall/network rules',
            'The URL may be incorrect — verify endpoint',
        ],
        'command_missing': [
            'Check if the command needs to be installed first',
            'Use apt-get/npm/pip to install it',
            'Verify PATH includes the installation directory',
            'The command may have a different name on this OS',
        ],
        'pip_install': [
            'Try installing a specific version instead of latest',
            'Check Python version compatibility',
            'The package name may be different on PyPI — search for correct name',
            'Use --no-deps if dependency resolution fails',
        ],
        'npm_error': [
            'Delete node_modules and reinstall',
            'Check Node.js version compatibility',
            'Try npm cache clean --force first',
        ],
        'docker': [
            'Check if Docker daemon is running',
            'Try with sudo or add user to docker group',
            'Pull the image explicitly before running',
        ],
        'runtime': [
            'Add detailed logging before the error line',
            'Wrap in try/except with specific exception types',
            'Check for None/null values before operations',
        ],
        'recursion': [
            'Add a base case check at the start of the function',
            'Convert recursion to iteration',
            'Increase sys.setrecursionlimit()',
        ],
        'default': [
            'Read the full error message and traceback carefully',
            'Search the error message for known solutions',
            'Add defensive checks (if/assert) before the failing operation',
            'Split the operation into smaller steps with logging',
        ],
    }

    def __init__(self, error_text: str):
        self.error_text = error_text
        self.error_type = self._classify(error_text)
        self.key_identifiers = self._extract_identifiers(error_text)
        self.signature = self._compute_signature()

    def _classify(self, text: str) -> str:
        for pattern, category in self.ERROR_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return category
        return 'default'

    def _compute_signature(self) -> str:
        """Hash the error type + key identifiers for deterministic lookup."""
        raw = f'{self.error_type}:{":".join(self.key_identifiers[:3])}'
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _extract_identifiers(self, text: str) -> list[str]:
        ids = []
        # Extract module/package names
        mods = re.findall(r"(?:module|package)\s+'([^']+)'", text, re.IGNORECASE)
        ids.extend(mods)
        # Extract class/function names
        names = re.findall(r"(?:name|attribute)\s+'([^']+)'", text, re.IGNORECASE)
        ids.extend(names)
        # Extract generic quoted identifiers
        quoted = re.findall(r"'([^']+)'", text)
        ids.extend(quoted)
        # Extract file paths
        paths = re.findall(r'(?:/[^/\s]+)+\.\w+', text)
        ids.extend(p[:50] for p in paths)
        return ids[:5] if ids else ['generic']

    def to_dict(self) -> dict[str, Any]:
        return {
            'error_type': self.error_type,
            'signature': self.signature,
            'key_identifiers': self.key_identifiers,
        }


# ---------------------------------------------------------------------------
# Solution Storage
# ---------------------------------------------------------------------------


class SolutionRegistry:
    """Persistent storage for error → solution mappings.

    Solutions are stored in `.wren/error_solutions.json` and also
    synced to FableMemory for cross-session recall.
    """

    def __init__(self, project_root: str | None = None):
        self._project_root = Path(project_root or os.getcwd()).expanduser()
        self._store_path = self._project_root / '.wren' / 'error_solutions.json'
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        self._solutions: dict[str, dict[str, Any]] = {}
        self._load()

    def lookup(self, error_text: str) -> dict[str, Any] | None:
        """Find a known solution for an error. Returns None if unknown."""
        sig = ErrorSignature(error_text)
        entry = self._solutions.get(sig.signature)
        if entry:
            return {
                'error_type': sig.error_type,
                'signature': sig.signature,
                'strategy': entry['best_strategy'],
                'strategy_index': entry.get('strategy_index', 0),
                'times_used': entry.get('times_used', 0),
                'last_success': entry.get('last_success'),
            }
        return None

    def record_success(
        self,
        error_text: str,
        strategy: str,
        strategy_index: int,
    ) -> None:
        """Record a winning strategy for an error."""
        sig = ErrorSignature(error_text)
        existing = self._solutions.get(sig.signature, {})
        times_used = existing.get('times_used', 0) + 1

        self._solutions[sig.signature] = {
            'error_type': sig.error_type,
            'signature': sig.signature,
            'key_identifiers': sig.key_identifiers,
            'best_strategy': strategy,
            'strategy_index': strategy_index,
            'times_used': times_used,
            'last_success': time.time(),
            'first_seen': existing.get('first_seen', time.time()),
        }
        self._flush()
        _logger.info(
            'SolutionRegistry: recorded strategy[%d] for %s (used %d times)',
            strategy_index,
            sig.error_type,
            times_used,
        )

    def record_failure(
        self,
        error_text: str,
        strategy_index: int,
    ) -> None:
        """Mark a strategy as failed so it's deprioritized next time."""
        sig = ErrorSignature(error_text)
        entry = self._solutions.get(sig.signature)
        if entry and entry.get('strategy_index') == strategy_index:
            entry['strategy_index'] = (strategy_index + 1) % self._total_strategies(
                sig.error_type
            )
            entry['times_used'] = entry.get('times_used', 0)
            self._flush()

    def _total_strategies(self, error_type: str) -> int:
        strategies = ErrorSignature.STRATEGY_MUTATIONS.get(
            error_type, ErrorSignature.STRATEGY_MUTATIONS['default']
        )
        return max(len(strategies), 1)

    def all_solutions(self) -> list[dict[str, Any]]:
        return list(self._solutions.values())

    def _load(self) -> None:
        if self._store_path.exists():
            try:
                with open(self._store_path) as f:
                    self._solutions = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._solutions = {}

    def _flush(self) -> None:
        try:
            tmp = self._store_path.with_suffix('.tmp')
            with open(tmp, 'w') as f:
                json.dump(self._solutions, f, indent=2)
            os.replace(tmp, self._store_path)
        except OSError as e:
            _logger.warning('SolutionRegistry flush failed: %s', e)


# ---------------------------------------------------------------------------
# Adaptive Retry Loop
# ---------------------------------------------------------------------------


class AdaptiveRetryLoop:
    """The adaptive error recovery loop.

    Flow:
    1. Try the operation
    2. On error → classify error signature
    3. Look up known solution → try best strategy first
    4. On failure → mutate to next strategy
    5. Repeat until success or max_retries exhausted
    6. On success → record winning strategy in registry + working memory
    7. On exhaustion → record all failures for manual review

    The loop mutates strategies slightly each retry:
    - Strategy 0: direct fix (try the known solution)
    - Strategy 1: slightly different approach
    - Strategy 2: fundamentally different approach
    - After success, the winning strategy is persisted
    """

    def __init__(
        self,
        project_root: str | None = None,
        max_retries: int = 5,
        working_memory: WorkingMemory | None = None,
    ):
        self._project_root = project_root
        self._max_retries = max_retries
        self._wm = working_memory or WorkingMemory(project_root)
        self._registry = SolutionRegistry(project_root)

    async def execute(
        self,
        operation_name: str,
        operation_fn,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run an operation with the adaptive retry loop.

        Args:
            operation_name: Human-readable name for the operation
            operation_fn: Async callable that performs the operation.
                          Should raise exceptions on failure.
            context: Optional context dict for logging

        Returns:
            dict with status, result, retries, strategy_used, solution_recorded
        """
        last_error = ''
        attempt = 0
        winning_strategy = ''
        winning_index = 0
        solution_was_known = False
        strategies_tried: list[str] = []

        while attempt < self._max_retries:
            attempt += 1
            strategy = ''
            strategy_index = 0
            is_known_solution = False

            if attempt == 1 and last_error:
                # Check if we have a known solution for the previous error
                known = self._registry.lookup(last_error)
                if known:
                    strategy = known['strategy']
                    strategy_index = known.get('strategy_index', 0)
                    is_known_solution = True
                    _logger.info(
                        'RetryLoop: known solution found for %s → %s',
                        operation_name,
                        strategy[:60],
                    )

            if not strategy and last_error:
                # Classify and get next mutation
                sig = ErrorSignature(last_error)
                strategies = ErrorSignature.STRATEGY_MUTATIONS.get(
                    sig.error_type,
                    ErrorSignature.STRATEGY_MUTATIONS['default'],
                )
                strategy_index = min(attempt - 1, len(strategies) - 1)
                strategy = strategies[strategy_index]
                _logger.info(
                    'RetryLoop: mutated strategy[%d] for %s → %s',
                    strategy_index,
                    sig.error_type,
                    strategy[:60],
                )

            try:
                result = await operation_fn(strategy if attempt > 1 else None)
                # Success!
                winning_strategy = strategy or 'direct'
                winning_index = strategy_index if attempt > 1 else 0
                solution_was_known = is_known_solution

                if last_error:
                    self._registry.record_success(
                        last_error,
                        winning_strategy,
                        winning_index,
                    )
                    self._wm.add_reflection(
                        f'Fixed {operation_name}: strategy "{winning_strategy}" '
                        f'worked after {attempt} attempt(s)',
                        tags=['error_recovery', operation_name],
                    )

                return {
                    'status': 'success',
                    'result': result,
                    'attempts': attempt,
                    'strategy_used': winning_strategy,
                    'strategy_index': winning_index,
                    'solution_was_known': solution_was_known,
                    'strategies_tried': strategies_tried,
                }

            except Exception as e:
                error_text = str(e)
                last_error = error_text
                strategies_tried.append(strategy or 'direct')
                sig = ErrorSignature(error_text)

                self._wm.add(
                    'error',
                    f'Attempt {attempt}/{self._max_retries} for '
                    f'{operation_name}: {error_text[:200]}',
                    {'error_type': sig.error_type, 'attempt': attempt},
                )

                if not is_known_solution and attempt > 1:
                    self._registry.record_failure(error_text, attempt - 2)

                _logger.info(
                    'RetryLoop: attempt %d/%d failed for %s (%s)',
                    attempt,
                    self._max_retries,
                    operation_name,
                    sig.error_type,
                )

        # All retries exhausted
        self._wm.add_reflection(
            f'Failed to fix {operation_name} after {self._max_retries} '
            f'attempts. Last error: {last_error[:200]}',
            tags=['error_recovery', 'failure', operation_name],
        )
        _logger.warning(
            'RetryLoop: exhausted %d attempts for %s',
            self._max_retries,
            operation_name,
        )
        return {
            'status': 'failed',
            'last_error': last_error,
            'attempts': attempt,
            'strategy_used': winning_strategy or strategies_tried[-1]
            if strategies_tried
            else '',
            'strategies_tried': strategies_tried,
        }

    def summary(self) -> dict[str, Any]:
        """Get current error registry summary."""
        solutions = self._registry.all_solutions()
        return {
            'known_solutions': len(solutions),
            'solutions': solutions,
        }
