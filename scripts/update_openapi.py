#!/usr/bin/env python3
"""Regenerate the bundled OpenAPI schema.

Writes the JSON representation produced by the FastAPI
application to ``openapi.json`` at the repository root.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'openapi.json'


def generate_schema() -> dict:
    """Import the app and return its OpenAPI dict."""
    from wren.app_server.app import app  # noqa: E501

    return app.openapi()


def write_schema(schema: dict) -> None:
    """Write the schema dict to OUTPUT."""
    OUTPUT.write_text(
        json.dumps(schema, indent=2) + '\n',
        encoding='utf-8',
    )


def main() -> int:
    """Generate and write the OpenAPI schema."""
    try:
        schema = generate_schema()
    except Exception as exc:
        print(
            f'Failed to generate schema: {exc}',
            file=sys.stderr,
        )
        return 1

    write_schema(schema)
    print(f'Wrote {OUTPUT}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
