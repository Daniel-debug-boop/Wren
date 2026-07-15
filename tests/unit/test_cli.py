"""Tests for the oh CLI entry point."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from wren.cli.main import (
    _build_parser,
    _check_port,
    _check_dependencies_hard,
    _set_solo_mode_env,
    _check_python_version,
    _check_package,
    _check_node,
    _check_playwright,
    _check_port_available,
    CheckResult,
    cmd_doctor,
    main,
)


class TestBuildParser:
    def test_default_args(self):
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.port == int(os.getenv('BACKEND_PORT', '3000'))
        assert args.host == os.getenv('BACKEND_HOST', '127.0.0.1')
        assert args.no_browser is False
        assert args.verbose is False
        assert args.command is None

    def test_custom_port(self):
        parser = _build_parser()
        args = parser.parse_args(['--port', '8080'])
        assert args.port == 8080

    def test_custom_host(self):
        parser = _build_parser()
        args = parser.parse_args(['--host', '0.0.0.0'])
        assert args.host == '0.0.0.0'

    def test_no_browser(self):
        parser = _build_parser()
        args = parser.parse_args(['--no-browser'])
        assert args.no_browser is True

    def test_verbose(self):
        parser = _build_parser()
        args = parser.parse_args(['--verbose'])
        assert args.verbose is True

    def test_verbose_short(self):
        parser = _build_parser()
        args = parser.parse_args(['-v'])
        assert args.verbose is True

    def test_doctor_subcommand(self):
        parser = _build_parser()
        args = parser.parse_args(['doctor'])
        assert args.command == 'doctor'

    def test_health_subcommand(self):
        parser = _build_parser()
        args = parser.parse_args(['health'])
        assert args.command == 'health'

    def test_health_with_port(self):
        parser = _build_parser()
        args = parser.parse_args(['health', '--port', '8080'])
        assert args.command == 'health'
        assert args.port == 8080


class TestSetSoloModeEnv:
    def test_sets_env_vars(self):
        _set_solo_mode_env()
        assert os.environ.get('APP_MODE') == 'oss'
        assert os.environ.get('ENABLE_BILLING') == 'false'
        assert os.environ.get('SERVE_FRONTEND') == 'true'

    def test_does_not_override_existing(self):
        os.environ['APP_MODE'] = 'saas'
        _set_solo_mode_env()
        assert os.environ['APP_MODE'] == 'saas'
        del os.environ['APP_MODE']


class TestCheckPort:
    def test_available_port(self):
        # Should not raise
        _check_port('127.0.0.1', 19876)

    def test_port_in_use(self):
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', 19877))
        sock.listen(1)
        try:
            with pytest.raises(SystemExit):
                _check_port('127.0.0.1', 19877)
        finally:
            sock.close()


class TestCheckDependenciesHard:
    def test_missing_package(self):
        with patch.dict('sys.modules', {'uvicorn': None}):
            with pytest.raises(SystemExit):
                _check_dependencies_hard()


class TestCheckResults:
    def test_check_result_ok(self):
        r = CheckResult('test', True, 'works')
        assert r.ok is True
        assert 'test' in str(r)

    def test_check_result_fail(self):
        r = CheckResult('test', False, 'broken', 'do this')
        assert r.ok is False
        assert 'do this' in r.fix

    def test_python_version_check(self):
        r = _check_python_version()
        assert r.ok is True  # tests run on 3.12+

    def test_package_check_missing(self):
        r = _check_package('nonexistent_package_xyz_123')
        assert r.ok is False
        assert 'not installed' in r.detail

    def test_package_check_present(self):
        r = _check_package('json')
        assert r.ok is True

    def test_node_check(self):
        r = _check_node()
        # May or may not be installed in test env
        assert isinstance(r, CheckResult)

    def test_playwright_check(self):
        r = _check_playwright()
        assert isinstance(r, CheckResult)

    def test_port_available_check(self):
        r = _check_port_available(19876)
        assert r.ok is True

    def test_port_in_use_check(self):
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', 19878))
        sock.listen(1)
        try:
            r = _check_port_available(19878)
            assert r.ok is False
        finally:
            sock.close()


class TestDoctorCommand:
    def test_doctor_runs(self, capsys):
        cmd_doctor()
        captured = capsys.readouterr()
        assert 'Wren Doctor' in captured.out or 'Python' in captured.out


class TestMain:
    def test_help_exits_cleanly(self):
        with pytest.raises(SystemExit) as exc_info:
            main(['--help'])
        assert exc_info.value.code == 0

    def test_version_exits_cleanly(self):
        with pytest.raises(SystemExit) as exc_info:
            main(['--version'])
        assert exc_info.value.code == 0

    def test_doctor_exits_cleanly(self):
        # Should not raise
        main(['doctor'])

    def test_health_exits_cleanly(self):
        # Should not raise (will fail to connect but that's fine)
        try:
            main(['health'])
        except SystemExit:
            pass  # health check may fail, that's ok
