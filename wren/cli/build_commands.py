"""Build subcommands for the oh CLI.

Adds:
    oh build-app "prompt"     → auto-detect project type
    oh build-web "prompt"     → build a website
    oh build-mobile "prompt"  → build a mobile app
    oh build-api "prompt"     → build an API server
    oh build-desktop "prompt" → build a desktop app
    oh build-cli "prompt"     → build a CLI tool
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any

from wren.app_builder import AppBuilder
from wren.app_builder.builder import _bold, _cyan, _yellow


def register_build_subcommands(subparsers: Any) -> None:
    """Register all build-* subcommands on the given subparsers group."""

    def _add_build_parser(name: str, help_text: str, project_type: str) -> None:
        parser = subparsers.add_parser(name, help=help_text)
        parser.add_argument('prompt', help='Describe what you want to build')
        parser.add_argument(
            '--name',
            type=str,
            default='',
            help='Project name (auto-generated from prompt if omitted)',
        )
        parser.add_argument(
            '--output',
            type=str,
            default='',
            help='Output directory (default: ./wren-builds/)',
        )
        parser.add_argument(
            '--deploy',
            action='store_true',
            default=False,
            help='Auto-deploy after build (Netlify for web, GitHub for others)',
        )
        parser.add_argument(
            '--github',
            action='store_true',
            default=False,
            help='Push to GitHub and trigger CI/CD',
        )
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            default=False,
            help='Show detailed output',
        )
        # Store the project type so the handler knows it
        parser.set_defaults(_project_type=project_type)

    _add_build_parser('build-app', 'Build any app (auto-detect type)', None)
    _add_build_parser('build-web', 'Build a website', 'web')
    _add_build_parser('build-mobile', 'Build a mobile app', 'mobile')
    _add_build_parser('build-api', 'Build an API server', 'api')
    _add_build_parser('build-desktop', 'Build a desktop app', 'desktop')
    _add_build_parser('build-cli', 'Build a CLI tool', 'cli')


def cmd_build(args: argparse.Namespace) -> None:
    """Execute a build command."""
    prompt = args.prompt
    project_type: str | None = getattr(args, '_project_type', None)
    project_name: str | None = args.name or None
    output_dir: str | None = args.output or None
    auto_deploy = args.deploy
    github_push = args.github
    verbose = args.verbose

    print()
    print(f'  {_bold(_cyan("⚡ Wren App Builder"))}')
    print(f'  {_yellow("Prompt:")} {prompt[:120]}')
    print()

    # Run the build
    builder = AppBuilder(
        output_dir=output_dir,
        auto_deploy=auto_deploy,
        github_push=github_push,
        verbose=verbose,
    )

    result = asyncio.run(
        builder.build(
            prompt=prompt,
            project_type=project_type,
            project_name=project_name,
        )
    )

    if not result.success:
        sys.exit(1)
