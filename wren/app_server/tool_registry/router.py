"""FastAPI router for the Tool Registry.

Exposes REST endpoints for:
- GET  /api/tool-registry/inventory        - List all installed capabilities
- POST /api/tool-registry/ensure           - Ensure capabilities exist (scrape+install)
- POST /api/tool-registry/analyze          - Analyze a task for needed tools
- POST /api/tool-registry/install          - Install a specific tool by name
- POST /api/tool-registry/install-mcp      - Install an MCP server
- DELETE /api/tool-registry/skills/{name}  - Uninstall a skill
- GET  /api/tool-registry/marketplace      - List installable MCP servers
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from wren.app_server.tool_registry.inventory import ToolInventory
from wren.app_server.tool_registry.installer import ToolInstaller
from wren.app_server.tool_registry.orchestrator import ToolOrchestrator
from wren.app_server.tool_registry.scraper import ToolScraper
from wren.app_server.utils.dependencies import get_dependencies

_logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/tool-registry',
    tags=['Tool Registry'],
    dependencies=get_dependencies(),
)


class EnsureCapabilitiesRequest(BaseModel):
    capabilities: list[str] = Field(
        ..., description='Capability keywords to ensure are installed'
    )
    auto_install: bool = Field(True, description='Auto-install missing tools from web')
    max_tools: int = Field(
        3, description='Maximum tools to install per run', ge=1, le=10
    )


class AnalyzeTaskRequest(BaseModel):
    task: str = Field(..., description='Task description to analyze')
    auto_install: bool = Field(True, description='Auto-install missing tools from web')


class InstallMcpRequest(BaseModel):
    name: str = Field(..., description='MCP server name')
    command: str = Field(..., description='Command to run the server')
    args: list[str] = Field(
        default_factory=list, description='Arguments for the command'
    )


class InstallSkillRequest(BaseModel):
    name: str = Field(..., description='Skill name')
    content: str = Field(..., description='Full markdown content with frontmatter')
    target: str = Field('user', description="Target directory: 'user' or 'global'")


def _get_orchestrator() -> ToolOrchestrator:
    return ToolOrchestrator(
        inventory=ToolInventory(),
        scraper=ToolScraper(),
        installer=ToolInstaller(),
    )


@router.get('/inventory')
async def get_inventory():
    """List all installed capabilities from local inventory."""
    orch = _get_orchestrator()
    summary = orch.inventory.capability_summary()
    return summary


@router.post('/ensure')
async def ensure_capabilities(req: EnsureCapabilitiesRequest):
    """Ensure capabilities exist, scraping and installing if needed."""
    orch = _get_orchestrator()
    result = await orch.ensure_capabilities(
        required_capabilities=req.capabilities,
        auto_install=req.auto_install,
        max_tools=req.max_tools,
    )
    return result


@router.post('/analyze')
async def analyze_task(req: AnalyzeTaskRequest):
    """Analyze a task description and ensure necessary tools exist."""
    orch = _get_orchestrator()
    result = await orch.analyze_task_for_tools(
        task_description=req.task,
        auto_install=req.auto_install,
    )
    return result


@router.post('/install-mcp')
async def install_mcp(req: InstallMcpRequest):
    """Install an MCP server by registering it as a skill."""
    installer = ToolInstaller()
    try:
        skill_path = installer.install_mcp_server(
            name=req.name,
            command=req.command,
            args=req.args,
        )
        return {'success': True, 'path': skill_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/install-skill')
async def install_skill(req: InstallSkillRequest):
    """Install a custom skill from provided markdown content."""
    installer = ToolInstaller()
    try:
        path = installer.install_skill(
            name=req.name,
            content=req.content,
            target_dir=req.target,
        )
        return {'success': True, 'path': str(path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/skills/{name}')
async def uninstall_skill(name: str):
    """Remove an installed skill by name."""
    installer = ToolInstaller()
    removed = installer.uninstall_skill(name)
    if not removed:
        raise HTTPException(
            status_code=404,
            detail=f'Skill "{name}" not found',
        )
    return {'success': True, 'removed': name}


@router.get('/marketplace')
async def list_marketplace():
    """List well-known installable MCP servers."""
    installer = ToolInstaller()
    servers = installer.list_installable_mcp_servers()
    return {'servers': servers, 'count': len(servers)}


@router.post('/refresh')
async def refresh_inventory():
    """Force refresh the inventory cache."""
    inventory = ToolInventory()
    inventory.invalidate_cache()
    summary = inventory.capability_summary()
    return {'success': True, 'inventory': summary}
