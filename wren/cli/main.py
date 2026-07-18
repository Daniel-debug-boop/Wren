"""oh — Wren CLI.

Launches the Wren backend server in OSS/solo mode with no auth required.

Commands:
    oh                  Start the server (default)
    oh code             Terminal-based agentic coding (like Claude Code/Aider)
    oh code "prompt"    One-shot agentic coding with a prompt
    oh chat             Open the TUI chat interface
    oh doctor           Check dependencies and diagnose issues
    oh health           Check if a running server is healthy
    oh build-app        Build an app from a prompt (auto-detect type)
    oh build-web        Build a website
    oh build-mobile     Build a mobile app
    oh build-api        Build an API server
    oh build-desktop    Build a desktop app
    oh build-cli        Build a CLI tool
    oh --port 8080      Custom port
    oh --no-browser     Skip auto-opening browser
"""

from __future__ import annotations

import argparse
import errno
import logging
import os
import signal
import socket
import subprocess
import sys
import textwrap
import time
import webbrowser

__version__ = '0.2.0'

logger = logging.getLogger('oh')

# ─── Colors (auto-disabled if not a terminal) ────────────────────────────────

_COLOR = sys.stderr.isatty()


def _c(code: str, text: str) -> str:
    if not _COLOR:
        return text
    return f'\033[{code}m{text}\033[0m'


def _bold(text: str) -> str:
    return _c('1', text)


def _red(text: str) -> str:
    return _c('31', text)


def _green(text: str) -> str:
    return _c('32', text)


def _yellow(text: str) -> str:
    return _c('33', text)


def _cyan(text: str) -> str:
    return _c('36', text)


# ─── Dependency checks ───────────────────────────────────────────────────────


class CheckResult:
    def __init__(self, name: str, ok: bool, detail: str, fix: str = ''):
        self.name = name
        self.ok = ok
        self.detail = detail
        self.fix = fix

    def __str__(self) -> str:
        icon = _green('✓') if self.ok else _red('✗')
        return f'  {icon} {self.name}: {self.detail}'


def _check_python_version() -> CheckResult:
    v = sys.version_info
    ok = v >= (3, 12)
    detail = f'{v.major}.{v.minor}.{v.micro}'
    fix = '' if ok else 'Install Python 3.12+: https://python.org/downloads'
    return CheckResult('Python', ok, detail, fix)


def _check_package(name: str, import_name: str = '') -> CheckResult:
    import_name = import_name or name
    try:
        mod = __import__(import_name)
        ver = getattr(mod, '__version__', '?')
        return CheckResult(name, True, f'v{ver}')
    except ImportError:
        cmds = [
            f'pip install {name}',
            'poetry install  (if using poetry)',
        ]
        return CheckResult(name, False, 'not installed', ' | '.join(cmds))


def _check_node() -> CheckResult:
    try:
        result = subprocess.run(
            ['node', '--version'],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return CheckResult('Node.js', True, result.stdout.strip())
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return CheckResult('Node.js', False, 'not found', 'Install from https://nodejs.org')


def _check_npm() -> CheckResult:
    try:
        result = subprocess.run(
            ['npm', '--version'],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return CheckResult('npm', True, f'v{result.stdout.strip()}')
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return CheckResult('npm', False, 'not found', 'Comes with Node.js')


def _check_playwright() -> CheckResult:
    cache = os.path.expanduser('~/.cache/playwright')
    if os.path.isdir(cache):
        browsers = os.listdir(cache)
        if browsers:
            return CheckResult('Playwright browsers', True, ', '.join(browsers))
    # Try checking via Python module
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'playwright', 'install', '--dry-run'],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return CheckResult('Playwright browsers', True, 'installed')
    except Exception:
        pass
    return CheckResult(
        'Playwright browsers',
        False,
        'not found',
        'Run: playwright install chromium',
    )


def _check_port_available(port: int) -> CheckResult:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.bind(('127.0.0.1', port))
        sock.close()
        return CheckResult(f'Port {port}', True, 'available')
    except OSError:
        return CheckResult(f'Port {port}', False, 'in use', f'Use oh --port {port + 1}')


def _check_frontend_built() -> CheckResult:
    # Check both build/ (vite default) and dist/ (alternate)
    for folder in ('build', 'dist'):
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', folder, 'index.html'
        )
        frontend_path = os.path.normpath(frontend_path)
        if os.path.isfile(frontend_path):
            return CheckResult(
                'Frontend build', True, f'frontend/{folder}/index.html exists'
            )
    return CheckResult(
        'Frontend build',
        False,
        'frontend/build/ not found',
        'Run: cd frontend && npm install && npm run build',
    )


# ─── Doctor command ──────────────────────────────────────────────────────────


def cmd_doctor() -> None:
    """Check all dependencies and print diagnostic report."""
    print(_bold('\nWren Doctor\n'))

    checks = [
        _check_python_version(),
        _check_package('uvicorn'),
        _check_package('fastapi'),
        _check_package('pydantic'),
        _check_node(),
        _check_npm(),
        _check_playwright(),
        _check_port_available(int(os.getenv('BACKEND_PORT', '3000'))),
        _check_frontend_built(),
    ]

    passed = sum(1 for c in checks if c.ok)
    total = len(checks)

    for c in checks:
        print(str(c))
        if not c.ok and c.fix:
            print(f'    {_yellow("fix:")} {c.fix}')

    print()
    if passed == total:
        print(_green(f"  All {total} checks passed. You're good to go."))
    else:
        print(_yellow(f'  {passed}/{total} checks passed.'))
        failed = [c for c in checks if not c.ok]
        if failed:
            print(_bold('\n  Quick fix:'))
            for c in failed:
                if c.fix:
                    print(f'    {c.fix}')
    print()


# ─── Health command ──────────────────────────────────────────────────────────


def cmd_health(host: str, port: int) -> None:
    """Check if a running server is healthy."""
    import urllib.request
    import urllib.error

    url = f'http://{host}:{port}'
    print(_bold(f'\nChecking {url}...\n'))

    # Try health endpoint
    try:
        req = urllib.request.Request(f'{url}/api/health', method='GET')
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read().decode()
            print(_green(f'  ✓ Server is healthy (HTTP {resp.status})'))
            if data.strip():
                print(f'    Response: {data.strip()[:200]}')
    except urllib.error.HTTPError as e:
        print(_red(f'  ✗ Server returned HTTP {e.code}'))
    except urllib.error.URLError as e:
        print(_red(f'  ✗ Cannot connect: {e.reason}'))
        print('    Is the server running? Start with: oh')
    except Exception as e:
        print(_red(f'  ✗ Error: {e}'))

    # Try root endpoint
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(_green(f'  ✓ Root endpoint responding (HTTP {resp.status})'))
    except Exception:
        pass

    print()


# ─── Server start ────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='oh',
        description='Wren — Code Less, Make More',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              oh                      Start server on port 3000
              oh --port 8080          Custom port
              oh doctor               Check dependencies
              oh build-web "my site"  Build a website
        """),
    )
    sub = parser.add_subparsers(dest='command')

    # Doctor
    sub.add_parser('doctor', help='Check dependencies and diagnose issues')

    # Health
    health_p = sub.add_parser('health', help='Check if a running server is healthy')
    health_p.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
    )
    health_p.add_argument(
        '--port',
        type=int,
        default=int(os.getenv('BACKEND_PORT', '3000')),
    )

    # Chat (TUI)
    chat_p = sub.add_parser('chat', help='Open the TUI chat interface')
    chat_p.add_argument(
        '--url',
        type=str,
        default=None,
        help='Wren backend URL (default: http://localhost:3000)',
    )

    # Code (agentic coding)
    from wren.cli.code_command import register_code_subcommand

    register_code_subcommand(sub)

    # Build subcommands
    from wren.cli.build_commands import register_build_subcommands

    register_build_subcommands(sub)

    # Server options
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.getenv('BACKEND_PORT', '3000')),
        help='Port to bind the backend server (default: 3000)',
    )
    parser.add_argument(
        '--host',
        type=str,
        default=os.getenv('BACKEND_HOST', '127.0.0.1'),
        help='Host to bind the backend server (default: 127.0.0.1)',
    )
    parser.add_argument(
        '--no-browser',
        action='store_true',
        default=False,
        help='Do not auto-open browser after startup',
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        default=False,
        help='Enable debug logging',
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}',
    )
    return parser


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
    )


def _set_solo_mode_env() -> None:
    os.environ.setdefault('APP_MODE', 'oss')
    os.environ.setdefault('ENABLE_BILLING', 'false')
    os.environ.setdefault('SERVE_FRONTEND', 'true')


def _check_port(host: str, port: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.bind((host, port))
        sock.close()
    except OSError as e:
        if e.errno == errno.EADDRINUSE:
            logger.error(
                'Port %d is in use. Use --port <other> or kill the process.',
                port,
            )
            # Try to show what's using it
            try:
                result = subprocess.run(
                    ['lsof', '-i', f':{port}', '-t'],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    logger.error('  Processes: %s', ', '.join(pids))
            except Exception:
                pass
            sys.exit(1)
        elif e.errno == errno.EACCES:
            logger.error(
                'Permission denied on port %d. Ports <1024 need root.',
                port,
            )
            sys.exit(1)
        else:
            logger.error('Cannot bind %s:%d: %s', host, port, e)
            sys.exit(1)


def _check_dependencies_hard() -> None:
    """Hard fail if critical packages missing."""
    missing = []
    for pkg in ['uvicorn', 'fastapi']:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(_red(f'\n  Missing: {", ".join(missing)}'))
        print(_yellow(f'  Install: pip install {" ".join(missing)}'))
        print(_yellow('  Or:      poetry install'))
        print()
        sys.exit(1)


def _open_browser(host: str, port: int, delay: float = 2.0) -> None:
    import threading

    def _do_open():
        time.sleep(delay)
        url = f'http://{host}:{port}'
        try:
            webbrowser.open(url)
            logger.info('Browser → %s', url)
        except Exception as e:
            logger.warning('Could not open browser: %s', e)

    threading.Thread(target=_do_open, daemon=True).start()


def _setup_signal_handlers() -> None:
    def _handler(signum, frame):
        print()  # newline after ^C
        logger.info('Shutting down...')
        sys.exit(0)

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


def _first_run_message() -> None:
    """Show first-run guidance if no config exists."""
    config_dir = os.path.expanduser('~/.config/wren')
    marker = os.path.join(config_dir, '.first-run-done')
    if os.path.exists(marker):
        return

    print()
    print(_bold('  Welcome to Wren!'))
    print('  First time? Run ')
    print(_cyan('    oh doctor'))
    print('  to check your setup.\n')

    os.makedirs(config_dir, exist_ok=True)
    with open(marker, 'w') as f:
        f.write(str(int(time.time())))


def cmd_chat(args) -> None:
    """Open the TUI chat interface."""
    url = args.url or f'http://{args.host}:{args.port}'

    # Check if textual is installed
    try:
        import textual  # noqa: F401
    except ImportError:
        print(_red('\n  textual is required for the TUI'))
        print(_yellow('  Install: pip install textual'))
        print()
        sys.exit(1)

    # Check if backend is running
    import urllib.request
    import urllib.error

    try:
        req = urllib.request.Request(f'{url}/api/v1/health', method='GET')
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status != 200:
                raise Exception('not healthy')
    except Exception:
        print(_yellow(f'\n  Backend not running at {url}'))
        print(f'  Start it first: {_cyan("oh")}')
        print()
        sys.exit(1)

    # Launch TUI
    from wren.tui.app import WrenTUI

    app = WrenTUI(base_url=url)
    app.run()


def cmd_start(args) -> None:
    """Start the backend server."""
    _set_solo_mode_env()
    _check_dependencies_hard()
    _check_port(args.host, args.port)

    print()
    print(_bold('  Wren') + f'  v{__version__}')
    print(f'  Backend:   {_cyan(f"http://{args.host}:{args.port}")}')
    print(f'  Frontend:  {_cyan("served by backend")}')
    print('  Mode:      solo (no auth)')
    print()

    if not args.no_browser:
        _open_browser(args.host, args.port)

    try:
        import uvicorn
    except ImportError:
        logger.error('uvicorn not installed. Run: pip install uvicorn')
        sys.exit(1)

    try:
        uvicorn.run(
            'wren.app_server.app:app',
            host=args.host,
            port=args.port,
            log_level='debug' if args.verbose else 'info',
            reload=False,
        )
    except KeyboardInterrupt:
        print()
        logger.info('Shutting down...')
    except Exception as e:
        logger.error('Server error: %s', e)
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)

    # Route to subcommands
    if args.command == 'doctor':
        cmd_doctor()
        return
    if args.command == 'health':
        cmd_health(args.host, args.port)
        return
    if args.command == 'chat':
        cmd_chat(args)
        return

    # Code command
    if args.command == 'code':
        from wren.cli.code_command import cmd_code

        import asyncio

        asyncio.run(cmd_code(args))
        return

    # Build commands
    build_commands = {
        'build-app',
        'build-web',
        'build-mobile',
        'build-api',
        'build-desktop',
        'build-cli',
    }
    if args.command in build_commands:
        from wren.cli.build_commands import cmd_build

        cmd_build(args)
        return

    # Default: start server
    _first_run_message()
    _setup_signal_handlers()
    cmd_start(args)


if __name__ == '__main__':
    main()
