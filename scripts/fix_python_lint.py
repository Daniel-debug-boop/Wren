#!/usr/bin/env python3
"""Auto-fix Python lint issues: unused imports (F401), unused variables (F841)."""

import re
import subprocess
import sys

FIXES = {
    # F401: unused imports
    "wren/app_server/design_analyzer.py": [
        ("^import asyncio\n", ""),
    ],
    "wren/app_server/file_discovery.py": [
        ("from dataclasses import field\n", ""),
        ("from typing import Sequence\n", ""),
    ],
    "wren/app_server/git/git_chunked_commits.py": [
        ("^import re\n", ""),
        ("from typing import Sequence\n", ""),
    ],
    "wren/app_server/github/issue_to_pr_router.py": [
        ("from typing import Annotated\n", ""),
    ],
    "wren/app_server/middleware.py": [
        ("^import asyncio\n", ""),
    ],
    "wren/app_server/orchestration/goal_detector.py": [
        ("^import json\n", ""),
        ("from pathlib import Path\n", ""),
    ],
    "wren/app_server/orchestration/hooks.py": [
        ("^import os\n", ""),
        ("^import time\n", ""),
        ("from wren.app_server.orchestration.working_memory import WorkingMemory\n", ""),
    ],
    "wren/app_server/orchestration/router.py": [
        ("^import asyncio\n", ""),
        ("from fastapi.responses import HTMLResponse\n", ""),
        ("from wren.app_server.orchestration.manager import SubTask\n", ""),
    ],
    "wren/app_server/orchestration/sub_agent_service.py": [
        ("^import json\n", ""),
        ("^import uuid\n", ""),
    ],
    "wren/app_server/sandbox/sandbox_pool.py": [
        ("from typing import AsyncIterator\n", ""),
    ],
    "wren/app_server/settings/provider_router.py": [
        ("from pathlib import Path\n", ""),
    ],
    # F841: unused variables
    "wren/app_server/design_analyzer.py": [
        ("            weights\s*=[^;]*\n", "\n"),
    ],
    "wren/app_server/tool_registry/inventory.py": [
        ("            skill_type\s*=[^;]*\n", ""),
        ("            agent\s*=\s*[^;]*\n", ""),
    ],
    # F541: f-strings without placeholders
    "wren/app_server/orchestration/hooks.py": [
        ('            f"\\n",', '            "\\n",'),
    ],
    "wren/app_server/tool_registry/scraper.py": [
        ('                    f"                ",', '                    "                ",'),
        ('                    f"                    ",', '                    "                    ",'),
        ('                    f"                    "', '                    "                    "'),
    ],
}

for filepath, replacements in FIXES.items():
    try:
        with open(filepath) as f:
            content = f.read()
        
        original = content
        for old, new in replacements:
            if isinstance(old, str):
                content = re.sub(old, new, content, flags=re.MULTILINE)
            else:
                content = content.replace(old, new)
        
        if content != original:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"✓ Fixed: {filepath}")
        else:
            print(f"  No changes needed: {filepath}")
    except FileNotFoundError:
        print(f"  Not found: {filepath}")

print("\nDone! Run 'flake8 wren/app_server/ --select=F401,F841,F541 --statistics' to verify.")
