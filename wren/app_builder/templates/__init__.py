"""Wren App Builder Templates — reusable boilerplate generators for 3D, database, auth, and more.

These templates are NOT static strings like builder.py. They are generator functions
that produce complete, customizable code based on the architecture design.
"""

from wren.app_builder.templates.three_kit import (
    generate_package_json,
    generate_tsconfig,
    generate_vite_config,
    generate_three_scene_tsx,
    generate_three_helpers_ts,
    generate_shader_glsl,
)
from wren.app_builder.templates.fullstack_kit import (
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
    "generate_package_json",
    "generate_tsconfig",
    "generate_vite_config",
    "generate_three_scene_tsx",
    "generate_three_helpers_ts",
    "generate_shader_glsl",
    "generate_sqlalchemy_base",
    "generate_user_model",
    "generate_jwt_auth",
    "generate_env_example",
    "generate_dockerfile",
    "generate_docker_compose",
    "generate_zustand_store",
    "generate_api_router",
]
