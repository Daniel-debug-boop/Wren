"""Wren App Builder — turn a single prompt into a complete, deployable app.

Usage:
    oh build-app "a todo app with Firebase auth"
    oh build-web "my personal portfolio site"
    oh build-mobile "a fitness tracker with charts"

Automated multi-file runner:
    python -m wren.app_builder.automated_runner --prompt "..." --api-key "..."

V2 build orchestrator (multi-agent pipeline):
    python -m wren.app_builder.build_orchestrator --prompt "..." --api-key "..."
"""

from wren.app_builder.builder import AppBuilder, BuildResult
from wren.app_builder.automated_runner import (
    AutomatedProjectGenerator,
    ProjectResult,
    run_pipeline,
    MASTER_SYSTEM_PROMPT,
    Manifest,
    FileSpec,
    GeneratedFile,
)
from wren.app_builder.build_orchestrator import (
    BuildOrchestrator,
    OrchestratorResult,
    BuildArtifact,
    AgentResult,
)
from wren.app_builder.agents import (
    ArchitectAgent,
    ArchitectureDesign,
    ComponentSpec,
    DataModelSpec,
    RouteSpec,
)
from wren.app_builder.build_orchestrator import (
    BuildOrchestrator,
    OrchestratorResult,
    BuildArtifact,
    AgentResult,
)
from wren.app_builder.validators import (
    validate_project,
    validate_syntax,
    ValidationResult,
    ValidationCheck,
)
from wren.app_builder.providers import (
    ProviderRouter,
    RouteResult,
    OpenAIProvider,
    AnthropicProvider,
)
from wren.app_builder.templates import (
    generate_package_json,
    generate_tsconfig,
    generate_vite_config,
    generate_three_scene_tsx,
    generate_three_helpers_ts,
    generate_shader_glsl,
    generate_sqlalchemy_base,
    generate_user_model,
    generate_jwt_auth,
    generate_env_example,
    generate_dockerfile,
    generate_docker_compose,
    generate_zustand_store,
    generate_api_router,
)

__all__ = [
    'AppBuilder',
    'BuildResult',
    'AutomatedProjectGenerator',
    'ProjectResult',
    'run_pipeline',
    'MASTER_SYSTEM_PROMPT',
    'Manifest',
    'FileSpec',
    'GeneratedFile',
    'BuildOrchestrator',
    'OrchestratorResult',
    'BuildArtifact',
    'AgentResult',
    'ArchitectAgent',
    'ArchitectureDesign',
    'ComponentSpec',
    'DataModelSpec',
    'RouteSpec',
    'validate_project',
    'validate_syntax',
    'ValidationResult',
    'ValidationCheck',
    'ProviderRouter',
    'RouteResult',
    'OpenAIProvider',
    'AnthropicProvider',
    'generate_package_json',
    'generate_tsconfig',
    'generate_vite_config',
    'generate_three_scene_tsx',
    'generate_three_helpers_ts',
    'generate_shader_glsl',
    'generate_sqlalchemy_base',
    'generate_user_model',
    'generate_jwt_auth',
    'generate_env_example',
    'generate_dockerfile',
    'generate_docker_compose',
    'generate_zustand_store',
    'generate_api_router',
]
