"""Skills loader — reads skill definitions from the skills/ directory.

Each skill is either a single .md file or a directory containing SKILL.md.
Skills are loaded at startup and served via the API.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)

# Skills directory relative to project root
_SKILLS_DIR = Path(__file__).resolve().parents[2] / 'skills'


# Default skills if the directory is empty or missing
_DEFAULT_SKILLS: list[dict[str, Any]] = [
    {
        'name': 'app-builder',
        'description': 'Full-stack application generator with SQLAlchemy, JWT auth, Docker Compose, and Zustand stores.',
        'category': 'development',
        'enabled': True,
        'icon': '🏗️',
    },
    {
        'name': 'code-review',
        'description': 'Automated code review with security analysis, performance checks, and best practices enforcement.',
        'category': 'quality',
        'enabled': True,
        'icon': '🔍',
    },
    {
        'name': 'docker',
        'description': 'Docker containerization with Dockerfile generation, docker-compose setup, and multi-stage builds.',
        'category': 'devops',
        'enabled': True,
        'icon': '🐳',
    },
    {
        'name': 'github',
        'description': 'GitHub integration: repository management, PR creation, issue tracking, and CI/CD workflows.',
        'category': 'integration',
        'enabled': True,
        'icon': '🐙',
    },
    {
        'name': 'kubernetes',
        'description': 'Kubernetes deployment with manifests, Helm charts, and cluster management.',
        'category': 'devops',
        'enabled': True,
        'icon': '☸️',
    },
    {
        'name': 'godot-game-dev',
        'description': 'Godot game development with GDScript, scene management, and game logic patterns.',
        'category': 'gaming',
        'enabled': True,
        'icon': '🎮',
    },
    {
        'name': 'security',
        'description': 'Security analysis: vulnerability scanning, OWASP checks, and secure coding practices.',
        'category': 'quality',
        'enabled': True,
        'icon': '🛡️',
    },
    {
        'name': '3d-design',
        'description': '3D design and visualization with Three.js, React Three Fiber, and shader programming.',
        'category': 'design',
        'enabled': True,
        'icon': '🎨',
    },
    {
        'name': 'scrapling',
        'description': 'Anti-bot web scraping that bypasses Cloudflare and extracts content from protected sites.',
        'category': 'data',
        'enabled': True,
        'icon': '🕷️',
    },
    {
        'name': 'api-generator',
        'description': 'REST and GraphQL API generation with OpenAPI specs, validation, and error handling.',
        'category': 'development',
        'enabled': True,
        'icon': '🔌',
    },
]


def _parse_skill_file(path: Path) -> dict[str, Any] | None:
    """Parse a skill markdown file and extract metadata."""
    try:
        content = path.read_text(encoding='utf-8')
    except OSError:
        return None

    # Extract the skill name from the first heading
    name = path.stem
    description = ''
    for line in content.split('\n')[:20]:
        line = line.strip()
        if line.startswith('# '):
            name = line[2:].strip()
        elif line and not line.startswith('#') and not line.startswith('---') and not line.startswith('triggers:'):
            if not description:
                description = line
            break

    # Determine category from parent directory or content
    category = 'general'
    parent = path.parent.name
    if parent != 'skills' and parent != '':
        category = parent

    return {
        'name': name.lower().replace(' ', '-').replace('_', '-'),
        'display_name': name,
        'description': description[:200],
        'category': category,
        'enabled': True,
        'file_path': str(path.relative_to(_SKILLS_DIR.parent)),
        'size_bytes': path.stat().st_size,
    }


def load_skills() -> list[dict[str, Any]]:
    """Load all skills from the skills/ directory.

    Falls back to default skills if the directory is empty or missing.
    """
    skills: list[dict[str, Any]] = []

    if not _SKILLS_DIR.exists():
        _logger.warning('Skills directory not found: %s, using defaults', _SKILLS_DIR)
        return _DEFAULT_SKILLS

    # Walk the skills directory
    for entry in sorted(_SKILLS_DIR.iterdir()):
        if entry.name.startswith('.') or entry.name == '__pycache__':
            continue

        skill = None
        if entry.is_file() and entry.suffix == '.md':
            skill = _parse_skill_file(entry)
        elif entry.is_dir():
            skill_md = entry / 'SKILL.md'
            if skill_md.exists():
                skill = _parse_skill_file(skill_md)
            else:
                # Look for any .md file
                for md_file in entry.glob('*.md'):
                    skill = _parse_skill_file(md_file)
                    if skill:
                        break

        if skill:
            skills.append(skill)

    if not skills:
        _logger.info('No skills found in %s, using defaults', _SKILLS_DIR)
        return _DEFAULT_SKILLS

    _logger.info('Loaded %d skills from %s', len(skills), _SKILLS_DIR)
    return skills
