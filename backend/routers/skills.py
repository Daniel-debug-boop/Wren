"""Skills management API endpoints.

Loads skill definitions from the skills/ filesystem directory.
Supports listing and toggling skills.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.services.storage import Storage
from backend.services.skills_loader import load_skills

router = APIRouter(prefix="/api/v1", tags=["skills"])
storage = Storage.get_instance()


@router.get("/skills")
async def list_skills() -> list[dict[str, Any]]:
    """List all available skills from the filesystem."""
    skills = load_skills()

    # Merge with any user toggles from storage
    stored = {s['name']: s for s in storage.get_skills()}

    for skill in skills:
        if skill['name'] in stored:
            skill['enabled'] = stored[skill['name']].get('enabled', skill['enabled'])

    return skills


@router.post("/skills/{name}/toggle")
async def toggle_skill(name: str, body: dict[str, Any]) -> dict[str, Any]:
    """Toggle a skill's enabled state."""
    enabled = body.get("enabled", True)
    result = storage.toggle_skill(name, enabled)
    if not result:
        # If the skill isn't in storage yet, create it
        return storage.add_to_collection('skills', {
            'name': name,
            'enabled': enabled,
        }, 'name')
    return result
