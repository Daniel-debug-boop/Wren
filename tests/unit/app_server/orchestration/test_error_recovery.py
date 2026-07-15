"""Tests for Error Recovery — ErrorSignature, SolutionRegistry, AdaptiveRetryLoop."""

import os
import tempfile
import time

import pytest

from wren.app_server.orchestration.error_recovery import (
    AdaptiveRetryLoop,
    ErrorSignature,
    SolutionRegistry,
)


class TestErrorSignature:
    def test_classify_import_missing(self):
        sig = ErrorSignature("ModuleNotFoundError: No module named 'flask'")
        assert sig.error_type == 'import_missing'

    def test_classify_syntax(self):
        sig = ErrorSignature('SyntaxError: invalid syntax (line 42)')
        assert sig.error_type == 'syntax'

    def test_classify_name_undefined(self):
        sig = ErrorSignature("NameError: name 'my_var' is not defined")
        assert sig.error_type == 'name_undefined'

    def test_classify_type_error(self):
        sig = ErrorSignature("TypeError: 'int' object is not callable")
        assert sig.error_type == 'type_not_callable'

    def test_classify_type_missing_arg(self):
        sig = ErrorSignature("TypeError: missing 1 required positional argument: 'name'")
        assert sig.error_type == 'type_missing_arg'

    def test_classify_attr_missing(self):
        sig = ErrorSignature("AttributeError: 'NoneType' object has no attribute 'foo'")
        assert sig.error_type == 'attr_missing'

    def test_classify_key_error(self):
        sig = ErrorSignature("KeyError: 'username'")
        assert sig.error_type == 'key_missing'

    def test_classify_file_not_found(self):
        sig = ErrorSignature("FileNotFoundError: [Errno 2] No such file: '/path/file'")
        assert sig.error_type == 'file_not_found'

    def test_classify_permission(self):
        sig = ErrorSignature("PermissionError: [Errno 13] Permission denied")
        assert sig.error_type == 'permission'

    def test_classify_timeout(self):
        sig = ErrorSignature('TimeoutError: Connection timed out')
        assert sig.error_type == 'timeout'

    def test_classify_connection(self):
        sig = ErrorSignature("ConnectionRefusedError: [Errno 111] Connection refused")
        assert sig.error_type == 'connection'

    def test_classify_command_missing(self):
        sig = ErrorSignature('command not found: docker')
        assert sig.error_type == 'command_missing'

    def test_classify_pip_install(self):
        sig = ErrorSignature("pip install failed: Could not find a version")
        assert sig.error_type == 'pip_install'

    def test_classify_npm_error(self):
        sig = ErrorSignature('npm ERR! code E404')
        assert sig.error_type == 'npm_error'

    def test_classify_docker(self):
        sig = ErrorSignature('docker: Error response from daemon')
        assert sig.error_type == 'docker'

    def test_classify_json_decode(self):
        sig = ErrorSignature('json.decoder.JSONDecodeError: Expecting value')
        assert sig.error_type == 'json_decode'

    def test_classify_indentation(self):
        sig = ErrorSignature('IndentationError: unexpected indent')
        assert sig.error_type == 'indentation'

    def test_classify_unknown(self):
        sig = ErrorSignature('Some completely unknown error message')
        assert sig.error_type == 'default'

    def test_signature_deterministic(self):
        sig1 = ErrorSignature("ModuleNotFoundError: No module named 'flask'")
        sig2 = ErrorSignature("ModuleNotFoundError: No module named 'flask'")
        assert sig1.signature == sig2.signature

    def test_signature_different_for_different_errors(self):
        sig1 = ErrorSignature("ModuleNotFoundError: No module named 'flask'")
        sig2 = ErrorSignature("ModuleNotFoundError: No module named 'django'")
        assert sig1.signature != sig2.signature

    def test_key_identifiers_contains_module_name(self):
        sig = ErrorSignature("ModuleNotFoundError: No module named 'flask'")
        assert 'flask' in sig.key_identifiers

    def test_key_identifiers_contains_file_path(self):
        sig = ErrorSignature("FileNotFoundError: '/home/user/project/config.json'")
        assert any('config.json' in id for id in sig.key_identifiers)

    def test_key_identifiers_fallback(self):
        sig = ErrorSignature('Something bad happened')
        assert sig.key_identifiers == ['generic']

    def test_to_dict(self):
        sig = ErrorSignature("ImportError: No module named 'requests'")
        d = sig.to_dict()
        assert d['error_type'] == 'import_missing'
        assert 'signature' in d
        assert 'key_identifiers' in d
        assert 'requests' in d['key_identifiers']

    def test_import_name_differentiation(self):
        """Test that import_name and import_missing are differentiated."""
        name_sig = ErrorSignature("ImportError: cannot import name 'flask'")
        mod_sig = ErrorSignature("ModuleNotFoundError: No module named 'flask'")
        assert name_sig.error_type == 'import_name'
        assert mod_sig.error_type == 'import_missing'


class TestSolutionRegistry:
    def test_lookup_nonexistent(self, tmp_path):
        reg = SolutionRegistry(project_root=str(tmp_path))
        result = reg.lookup('ModuleNotFoundError: No such thing')
        assert result is None

    def test_record_and_lookup(self, tmp_path):
        reg = SolutionRegistry(project_root=str(tmp_path))
        reg.record_success(
            "ModuleNotFoundError: No module named 'flask'",
            'Install flask via pip',
            strategy_index=0,
        )
        result = reg.lookup("ModuleNotFoundError: No module named 'flask'")
        assert result is not None
        assert result['strategy'] == 'Install flask via pip'

    def test_multiple_recordings_increment_usage(self, tmp_path):
        reg = SolutionRegistry(project_root=str(tmp_path))
        error = "ModuleNotFoundError: No module named 'flask'"
        reg.record_success(error, 'pip install flask', 0)
        reg.record_success(error, 'pip install flask', 0)
        result = reg.lookup(error)
        assert result['times_used'] == 2

    def test_record_failure_changes_strategy(self, tmp_path):
        reg = SolutionRegistry(project_root=str(tmp_path))
        error = "ModuleNotFoundError: No module named 'flask'"
        reg.record_success(error, 'pip install flask', 0)
        reg.record_failure(error, 0)
        result = reg.lookup(error)
        # The strategy index should have changed
        assert result['strategy_index'] != 0

    def test_all_solutions(self, tmp_path):
        reg = SolutionRegistry(project_root=str(tmp_path))
        assert reg.all_solutions() == []

        reg.record_success("Error 1", 'Strategy 1', 0)
        reg.record_success("Error 2", 'Strategy 2', 0)
        assert len(reg.all_solutions()) == 2

    def test_persistence(self, tmp_path):
        reg = SolutionRegistry(project_root=str(tmp_path))
        reg.record_success(
            "ModuleNotFoundError: No module named 'flask'",
            'pip install flask',
            0,
        )

        # New instance should load saved data
        reg2 = SolutionRegistry(project_root=str(tmp_path))
        result = reg2.lookup("ModuleNotFoundError: No module named 'flask'")
        assert result is not None


class TestAdaptiveRetryLoop:
    @pytest.mark.asyncio
    async def test_success_first_attempt(self, tmp_path):
        """Test that a successful operation returns immediately."""
        loop = AdaptiveRetryLoop(
            project_root=str(tmp_path),
            max_retries=3,
        )

        async def op(_strategy=None):
            return 'success'

        result = await loop.execute('test_op', op)
        assert result['status'] == 'success'
        assert result['attempts'] == 1
        assert result['result'] == 'success'

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, tmp_path):
        """Test retry on initial failure."""
        attempts = 0
        loop = AdaptiveRetryLoop(
            project_root=str(tmp_path),
            max_retries=3,
        )

        async def op(_strategy=None):
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ValueError('Temporary error')
            return 'retried_success'

        result = await loop.execute('flaky_op', op)
        assert result['status'] == 'success'
        assert result['attempts'] == 2
        assert result['result'] == 'retried_success'

    @pytest.mark.asyncio
    async def test_exhaust_retries(self, tmp_path):
        """Test that exhausting retries returns failure."""
        loop = AdaptiveRetryLoop(
            project_root=str(tmp_path),
            max_retries=3,
        )

        async def op(_strategy=None):
            raise RuntimeError('Persistent error')

        result = await loop.execute('failing_op', op)
        assert result['status'] == 'failed'
        assert result['attempts'] == 3

    @pytest.mark.asyncio
    async def test_strategies_tried_recorded(self, tmp_path):
        """Test that strategies_tried are recorded for each attempt."""
        loop = AdaptiveRetryLoop(
            project_root=str(tmp_path),
            max_retries=2,
        )

        async def op(_strategy=None):
            raise RuntimeError('Always fails')

        result = await loop.execute('failing_op', op)
        assert result['status'] == 'failed'
        assert len(result['strategies_tried']) == 2

    @pytest.mark.asyncio
    async def test_known_solution_used_first(self, tmp_path):
        """Test that a known solution is tried first on retry."""
        # First, record a known solution
        reg = SolutionRegistry(project_root=str(tmp_path))
        reg.record_success(
            'Initial error: something broke',
            'Use workaround A',
            0,
        )

        loop = AdaptiveRetryLoop(
            project_root=str(tmp_path),
            max_retries=3,
        )

        first_attempt = True

        async def op(_strategy=None):
            nonlocal first_attempt
            if first_attempt:
                first_attempt = False
                raise RuntimeError('Initial error: something broke')
            return 'fixed'

        result = await loop.execute('known_solution_op', op)
        assert result['status'] == 'success'
        assert result['solution_was_known'] is True

    @pytest.mark.asyncio
    async def test_summary(self, tmp_path):
        """Test summary returns known solutions."""
        loop = AdaptiveRetryLoop(project_root=str(tmp_path))
        summary = loop.summary()
        assert 'known_solutions' in summary
        assert 'solutions' in summary
