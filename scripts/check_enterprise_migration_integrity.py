#!/usr/bin/env python3
"""Check enterprise Alembic migration static integrity.

Validates migration filename prefixes, revision IDs,
down_revision chains, and head singletons without
requiring a live database connection.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERSIONS_DIR = ROOT / 'enterprise' / 'migrations' / 'versions'
MIGRATION_FILENAME_RE = re.compile(r'^(?P<prefix>\d+)_.+\.py$')
MISSING = object()


def _literal_assignment(module: ast.Module, name: str) -> Any:
    """Extract literal value of module-level assignment."""
    for node in module.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue

        if any(
            isinstance(target, ast.Name) and target.id == name for target in targets
        ):
            return ast.literal_eval(node.value)

    return MISSING


def _format_paths(paths: list[Path]) -> str:
    """Format list of paths as comma-separated filenames."""
    return ', '.join(path.name for path in sorted(paths))


def _down_revisions(value: Any, path: Path, errors: list[str]) -> list[str]:
    """Parse down_revision value into list of revisions."""
    if value is MISSING:
        errors.append(f'{path.name}: missing down_revision')
        return []
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        if all(isinstance(item, str) for item in value):
            return list(value)

    errors.append(
        f'{path.name}: down_revision must be None, a string, or a sequence of strings'
    )
    return []


def _parse_migration_file(
    path: Path,
    errors: list[str],
    prefixes: defaultdict[str, list[Path]],
    revisions: defaultdict[str, list[Path]],
) -> dict[str, Any] | None:
    """Parse migration file and extract metadata."""
    match = MIGRATION_FILENAME_RE.match(path.name)
    prefix = match.group('prefix') if match else None
    if prefix is None:
        errors.append(
            f'{path.name}: migration filename must start with a numeric prefix'
        )
        return None

    prefixes[prefix].append(path)

    try:
        module = ast.parse(
            path.read_text(encoding='utf-8'),
            filename=str(path),
        )
    except SyntaxError as exc:
        errors.append(f'{path.name}: cannot parse migration: {exc}')
        return None

    revision = _literal_assignment(module, 'revision')
    if not isinstance(revision, str):
        errors.append(f'{path.name}: revision must be a string')
        return None

    revisions[revision].append(path)
    if prefix is not None and prefix != revision:
        errors.append(
            f'{path.name}: Filename prefix {prefix} does not match revision {revision}'
        )

    down_revision = _literal_assignment(module, 'down_revision')
    down_revs = _down_revisions(down_revision, path, errors)

    return {
        'path': path,
        'revision': revision,
        'down_revisions': down_revs,
    }


def _check_duplicate_prefixes(
    prefixes: defaultdict[str, list[Path]],
) -> list[str]:
    """Check for migration files sharing a prefix."""
    errors: list[str] = []
    for prefix, paths in sorted(prefixes.items()):
        if len(paths) > 1:
            errors.append(
                f'Duplicate migration filename prefix {prefix}: {_format_paths(paths)}'
            )
    return errors


def _check_duplicate_revisions(
    revisions: defaultdict[str, list[Path]],
) -> list[str]:
    """Check for migrations sharing a revision ID."""
    errors: list[str] = []
    for revision, paths in sorted(revisions.items()):
        if len(paths) > 1:
            errors.append(
                f'Duplicate migration revision {revision}: {_format_paths(paths)}'
            )
    return errors


def _check_down_revision_references(
    migrations: list[dict[str, Any]],
    known_revisions: set[str],
) -> list[str]:
    """Check down_revision refs are known."""
    errors: list[str] = []
    for migration in migrations:
        for down_rev in migration['down_revisions']:
            if down_rev not in known_revisions:
                errors.append(
                    f'{migration["path"].name}: '
                    f'references missing '
                    f'down_revision {down_rev}'
                )
    return errors


def _check_single_head(
    migrations: list[dict[str, Any]],
    known_revisions: set[str],
    referenced_revisions: set[str],
) -> list[str]:
    """Check migration chain has one head."""
    errors: list[str] = []
    heads = sorted(known_revisions - referenced_revisions)
    if migrations and len(heads) != 1:
        joined = ', '.join(heads) if heads else '<none>'
        errors.append(
            f'Expected exactly one migration head, found {len(heads)}: {joined}'
        )
    return errors


def check_migration_integrity(
    versions_dir: Path = DEFAULT_VERSIONS_DIR,
) -> list[str]:
    """Run all migration integrity checks."""
    all_errors: list[str] = []
    migrations: list[dict[str, Any]] = []
    prefixes: defaultdict[str, list[Path]] = defaultdict(list)
    revisions: defaultdict[str, list[Path]] = defaultdict(list)
    referenced_revisions: set[str] = set()

    if not versions_dir.exists():
        return [f'Migration versions directory does not exist: {versions_dir}']

    for path in sorted(versions_dir.glob('*.py')):
        if path.name == '__init__.py':
            continue

        migration = _parse_migration_file(path, all_errors, prefixes, revisions)
        if migration is not None:
            referenced_revisions.update(migration['down_revisions'])
            migrations.append(migration)

    all_errors.extend(_check_duplicate_prefixes(prefixes))
    all_errors.extend(_check_duplicate_revisions(revisions))

    known_revisions = set(revisions)
    all_errors.extend(_check_down_revision_references(migrations, known_revisions))
    all_errors.extend(
        _check_single_head(
            migrations,
            known_revisions,
            referenced_revisions,
        )
    )

    return all_errors


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=('Check enterprise Alembic migration static integrity.')
    )
    parser.add_argument(
        '--versions-dir',
        type=Path,
        default=DEFAULT_VERSIONS_DIR,
        help=('Path to the enterprise Alembic versions directory.'),
    )
    return parser.parse_args()


def main() -> int:
    """Run migration integrity check."""
    args = parse_args()
    errors = check_migration_integrity(args.versions_dir)
    if errors:
        print(
            'Enterprise migration integrity check failed:',
            file=sys.stderr,
        )
        for error in errors:
            print(f'  - {error}', file=sys.stderr)
        return 1

    print('Enterprise migration integrity checks passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
