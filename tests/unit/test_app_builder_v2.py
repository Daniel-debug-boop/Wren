"""Unit tests for the app builder v2 modules.

Tests cover:
  - Shared LLMClient
  - Validation (syntax, placeholder, 3D leak, import consistency)
  - Template generators (3D kit, full-stack kit)
  - Provider routing
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

from wren.app_builder.llm_client import LLMClient
from wren.app_builder.validators import (
    ValidationCheck,
    ValidationResult,
    check_placeholders,
    check_3d_resource_leaks,
    check_imports_against_package_json,
)
from wren.app_builder.templates.three_kit import (
    generate_package_json,
    generate_tsconfig,
    generate_vite_config,
    generate_three_scene_tsx,
    generate_three_helpers_ts,
)
from wren.app_builder.templates.fullstack_kit import (
    generate_sqlalchemy_base,
    generate_user_model,
    generate_jwt_auth,
    generate_env_example,
    generate_zustand_store,
    generate_api_router,
    generate_dockerfile,
    generate_docker_compose,
)
from wren.app_builder.providers import (
    ProviderRouter,
    RouteResult,
    BUILTIN_PROVIDERS,
)
from wren.app_builder.agents import (
    ComponentSpec,
    DataModelSpec,
    RouteSpec,
    ArchitectureDesign,
)


# ── LLMClient tests ─────────────────────────────────────────────────────


class TestLLMClient:
    """Tests for the shared LLMClient module."""

    def test_init_defaults(self):
        client = LLMClient(api_key="sk-test")
        assert client.api_key == "sk-test"
        assert client.model == "gpt-4o"
        assert client.base_url == "https://api.openai.com/v1"
        assert client.max_tokens == 16384
        assert client.temperature == 0.3

    def test_init_custom(self):
        client = LLMClient(api_key="sk-test", model="claude-sonnet-4", base_url="https://api.anthropic.com/v1", max_tokens=8192, temperature=0.1)
        assert client.model == "claude-sonnet-4"
        assert client.base_url == "https://api.anthropic.com/v1"
        assert client.max_tokens == 8192
        assert client.temperature == 0.1

    def test_init_strips_base_url(self):
        client = LLMClient(api_key="sk-test", base_url="https://api.openai.com/v1/")
        assert client.base_url == "https://api.openai.com/v1"


# ── Validation tests ────────────────────────────────────────────────────


class TestCheckPlaceholders:
    """Tests for placeholder detection."""

    def test_no_placeholders(self):
        content = "def hello():\\n    print('world')\\n"
        checks = check_placeholders(content, "test.py")
        todo_checks = [c for c in checks if "Placeholder" in c.name]
        assert len(todo_checks) == 0

    def test_detects_todo(self):
        content = "# TODO: implement this"
        checks = check_placeholders(content, "test.py")
        assert any("TODO" in c.message for c in checks)

    def test_detects_fixme(self):
        content = "# FIXME: this is broken"
        checks = check_placeholders(content, "test.py")
        assert any("FIXME" in c.message for c in checks)

    def test_detects_placeholder_text(self):
        content = "# add your code here"
        checks = check_placeholders(content, "test.py")
        assert any("placeholder" in c.message.lower() for c in checks)

    def test_detects_not_implemented(self):
        content = "raise NotImplementedError('not implemented')"
        checks = check_placeholders(content, "test.py")
        assert any("not implemented" in c.message.lower() for c in checks)


class TestCheck3DResourceLeaks:
    """Tests for Three.js resource leak detection."""

    def test_no_3d_no_issues(self):
        content = "const x = 5;"
        checks = check_3d_resource_leaks(content, "test.ts")
        assert len(checks) == 0

    def test_detects_missing_dispose(self):
        content = """
import * as THREE from 'three'
const geo = new THREE.BoxGeometry(1, 1, 1)
const mat = new THREE.MeshPhysicalMaterial()
"""
        checks = check_3d_resource_leaks(content, "test.ts")
        assert len(checks) > 0
        assert any("geometry" in c.details.lower() for c in checks)

    def test_passes_with_dispose(self):
        content = """
import * as THREE from 'three'
const geo = new THREE.BoxGeometry(1, 1, 1)
geo.dispose()
"""
        checks = check_3d_resource_leaks(content, "test.ts")
        # Should still flag material but not geometry
        geo_checks = [c for c in checks if "geometry" in c.details.lower()]
        assert len(geo_checks) == 0

    def test_no_three_no_check(self):
        content = "console.log('no three here')"
        checks = check_3d_resource_leaks(content, "test.js")
        assert len(checks) == 0


class TestCheckImportConsistency:
    """Tests for import vs package.json checks."""

    def test_missing_dependency_detected(self):
        content = "import { something } from 'missing-package'"
        package_json = {"dependencies": {"react": "^18.0.0"}}
        checks = check_imports_against_package_json(content, "test.ts", package_json)
        assert len(checks) == 1
        assert "missing-package" in checks[0].message

    def test_known_dependency_ok(self):
        content = "import React from 'react'"
        package_json = {"dependencies": {"react": "^18.0.0"}}
        checks = check_imports_against_package_json(content, "test.ts", package_json)
        assert len(checks) == 0

    def test_skips_local_imports(self):
        content = "import { helper } from './utils/helper'"
        package_json = {}
        checks = check_imports_against_package_json(content, "test.ts", package_json)
        assert len(checks) == 0

    def test_empty_package_json_ok(self):
        content = "import { x } from 'some-package'"
        checks = check_imports_against_package_json(content, "test.ts", None)
        assert len(checks) == 0


# ── Template generator tests ────────────────────────────────────────────


class TestThreeJSTemplates:
    """Tests for the 3D/WebGL template generators."""

    def test_generate_package_json(self):
        result = generate_package_json("test-project", has_3d=True)
        assert result["name"] == "test-project"
        assert "three" in result["dependencies"]
        assert "@react-three/fiber" in result["dependencies"]
        assert "@types/three" in result["devDependencies"]

    def test_package_json_no_3d(self):
        result = generate_package_json("test", has_3d=False)
        assert "three" not in result["dependencies"]

    def test_generate_tsconfig(self):
        result = generate_tsconfig()
        assert "compilerOptions" in result
        assert "strict" in result or "include" in result

    def test_generate_vite_config(self):
        result = generate_vite_config(has_3d=True)
        assert "defineConfig" in result
        assert "@vitejs/plugin-react" in result
        assert "three" in result or "r3f" in result

    def test_generate_vite_config_no_3d(self):
        result = generate_vite_config(has_3d=False)
        assert "defineConfig" in result
        assert "three" not in result

    def test_generate_scene_tsx(self):
        result = generate_three_scene_tsx()
        assert "Scene" in result
        assert "Canvas" in result
        assert "OrbitControls" in result
        assert "AmbientLight" in result or "ambientLight" in result
        assert "dispose" in result.lower() or "Dispose" in result

    def test_generate_helpers_ts(self):
        result = generate_three_helpers_ts()
        assert "disposeObject" in result
        assert "loadModel" in result
        assert "detectWebGLSupport" in result
        assert "isInFrustum" in result


class TestFullStackTemplates:
    """Tests for the full-stack template generators."""

    def test_sqlalchemy_base(self):
        result = generate_sqlalchemy_base()
        assert "sqlalchemy" in result.lower() or "SQLAlchemy" in result
        assert "DeclarativeBase" in result
        assert "get_db" in result
        assert "init_db" in result

    def test_user_model(self):
        result = generate_user_model()
        assert "User" in result
        assert "sqlalchemy" in result.lower()
        assert "password_hash" in result
        assert "to_dict" in result

    def test_jwt_auth(self):
        result = generate_jwt_auth()
        assert "jwt" in result.lower()
        assert "create_access_token" in result
        assert "verify_password" in result
        assert "get_current_user" in result
        assert "/api/auth/login" in result or "/api/auth/register" in result

    def test_env_example(self):
        result = generate_env_example(has_database=True, has_auth=True)
        assert "DATABASE_URL" in result
        assert "JWT_SECRET_KEY" in result
        assert "OPENAI_API_KEY" in result

    def test_env_example_no_db(self):
        result = generate_env_example(has_database=False, has_auth=False)
        assert "DATABASE_URL" not in result
        assert "JWT_SECRET_KEY" not in result

    def test_zustand_store(self):
        result = generate_zustand_store()
        assert "useAuthStore" in result
        assert "useUIStore" in result
        assert "apiFetch" in result
        assert "zustand" in result

    def test_api_router(self):
        result = generate_api_router()
        assert "create_crud_router" in result
        assert "APIRouter" in result
        assert "list_items" in result
        assert "create_item" in result
        assert "delete_item" in result

    def test_dockerfile(self):
        result = generate_dockerfile()
        assert "FROM python:" in result
        assert "WORKDIR /app" in result
        assert "uvicorn" in result

    def test_docker_compose(self):
        result = generate_docker_compose()
        assert "services:" in result
        assert "myapp-api" in result
        assert "postgres" in result or "healthcheck" in result


# ── Provider tests ──────────────────────────────────────────────────────


class TestProviderRouter:
    """Tests for the multi-provider router."""

    def test_builtin_providers_exist(self):
        assert "openai" in BUILTIN_PROVIDERS
        assert "anthropic" in BUILTIN_PROVIDERS
        assert "google" in BUILTIN_PROVIDERS
        assert "deepseek" in BUILTIN_PROVIDERS
        assert "local" in BUILTIN_PROVIDERS

    def test_router_not_loaded_initially(self):
        router = ProviderRouter()
        assert router.available_providers == []

    def test_configure_single_provider(self):
        router = ProviderRouter()
        router.configure(openai_api_key="sk-test")
        assert "openai" in router.available_providers

    def test_configure_multiple_providers(self):
        router = ProviderRouter()
        router.configure(openai_api_key="sk-test", anthropic_api_key="sk-ant-test")
        assert "openai" in router.available_providers
        assert "anthropic" in router.available_providers

    def test_is_configured(self):
        router = ProviderRouter()
        router.configure(openai_api_key="sk-test")
        assert router.is_configured("openai")
        assert not router.is_configured("anthropic")

    def test_route_fails_without_config(self):
        router = ProviderRouter()
        with pytest.raises(RuntimeError, match="No LLM providers configured"):
            import asyncio
            asyncio.run(router.route("system", "user"))


# ── Architecture Design tests ───────────────────────────────────────────


class TestArchitectureDesign:
    """Tests for the ArchitectureDesign data model."""

    def test_default_values(self):
        design = ArchitectureDesign(project_name="test", project_type="web", summary="A test")
        assert design.project_name == "test"
        assert design.project_type == "web"
        assert design.auth_strategy == "none"
        assert design.database_type == "none"
        assert design.has_3d is False
        assert design.components == []
        assert design.data_models == []

    def test_to_dict(self):
        design = ArchitectureDesign(
            project_name="my-app",
            project_type="3d-web",
            summary="A 3D app",
            has_3d=True,
            database_type="sqlite",
            auth_strategy="jwt",
            components=[ComponentSpec(name="Scene", path="src/Scene.tsx", purpose="3D scene", is_3d=True)],
            data_models=[DataModelSpec(name="User", fields=[{"name": "email", "type": "string"}])],
            routes=[RouteSpec(path="/api/health", purpose="Health check")],
        )
        d = design.to_dict()
        assert d["project_name"] == "my-app"
        assert d["project_type"] == "3d-web"
        assert d["has_3d"] is True
        assert d["database_type"] == "sqlite"
        assert d["auth_strategy"] == "jwt"
        assert len(d["components"]) == 1
        assert d["components"][0]["is_3d"] is True
        assert len(d["data_models"]) == 1
        assert len(d["routes"]) == 1

    def test_component_spec_defaults(self):
        c = ComponentSpec(name="Test", path="test.ts", purpose="Testing")
        assert c.props == []
        assert c.state == []
        assert c.dependencies == []
        assert c.is_3d is False
        assert c.estimated_complexity == "medium"
