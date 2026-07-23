"""
Project Context Analyzer — maps codebase structure, dependencies, and type relationships.

This is Wren's competitive edge over Aider and Claude Code. It builds a
comprehensive map of the codebase including:
  - File dependency graph (imports/exports between files)
  - Type/interface definitions and their relationships
  - Function signatures and their call sites
  - Component hierarchy (React component tree)
  - Database model relationships
  - API route definitions

This context is used by all agents to make informed decisions about code changes.
"""

from __future__ import annotations

import ast
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)


# ── Data models ───────────────────────────────────────────────────────────


@dataclass
class ImportInfo:
    """Information about an import statement."""

    source: str  # The module being imported from
    names: list[str]  # Specific names imported
    is_relative: bool = False
    is_type_only: bool = False


@dataclass
class ExportInfo:
    """Information about an export from a file."""

    name: str
    kind: str  # function, class, const, interface, type, enum, variable
    line: int = 0
    is_default: bool = False
    is_async: bool = False
    docstring: str = ""


@dataclass
class FileNode:
    """Represents a single file in the codebase graph."""

    path: str
    language: str  # python, typescript, javascript, etc.
    imports: list[ImportInfo] = field(default_factory=list)
    exports: list[ExportInfo] = field(default_factory=list)
    lines_of_code: int = 0
    is_test: bool = False
    is_config: bool = False


@dataclass
class DependencyGraph:
    """Complete dependency graph of the codebase."""

    files: dict[str, FileNode] = field(default_factory=dict)
    type_definitions: dict[str, str] = field(default_factory=dict)  # type_name -> file_path
    function_definitions: dict[str, str] = field(default_factory=dict)  # func_name -> file_path

    def get_dependents(self, file_path: str) -> list[str]:
        """Get all files that import from the given file."""
        dependents: list[str] = []
        for path, node in self.files.items():
            for imp in node.imports:
                # Check if source matches file_path
                if imp.source == file_path.replace(".py", "").replace("/", "."):
                    dependents.append(path)
                # Check file stem (e.g., importing 'helpers' from './helpers' matches 'helpers.py')
                if Path(imp.source).stem == Path(file_path).stem:
                    dependents.append(path)
        return dependents

    def get_dependencies(self, file_path: str) -> list[str]:
        """Get all files that the given file imports from."""
        node = self.files.get(file_path)
        if not node:
            return []
        deps: list[str] = []
        for imp in node.imports:
            for name in imp.names:
                # Try to find the file that exports this name
                target = self.type_definitions.get(name) or self.function_definitions.get(name)
                if target and target != file_path:
                    deps.append(target)
        return deps

    def to_dict(self) -> dict[str, Any]:
        return {
            "files": list(self.files.keys()),
            "total_files": len(self.files),
            "type_definitions": self.type_definitions,
            "function_definitions": self.function_definitions,
        }

    def summarize(self) -> str:
        """Produce a human-readable summary of the codebase."""
        parts: list[str] = []
        parts.append(f"Codebase: {len(self.files)} files")
        parts.append(f"Types: {len(self.type_definitions)}")
        parts.append(f"Functions: {len(self.function_definitions)}")
        parts.append("")

        # Group by directory
        dirs: dict[str, int] = {}
        for path in self.files:
            d = str(Path(path).parent)
            dirs[d] = dirs.get(d, 0) + 1

        parts.append("Directory structure:")
        for d, count in sorted(dirs.items()):
            parts.append(f"  {d}/ ({count} files)")

        parts.append("")
        parts.append("Key types:")
        for name, path in list(self.type_definitions.items())[:20]:
            parts.append(f"  {name} -> {path}")

        parts.append("")
        parts.append("Key functions:")
        for name, path in list(self.function_definitions.items())[:20]:
            parts.append(f"  {name}() -> {path}")

        return "\n".join(parts)


# ── Parsers ────────────────────────────────────────────────────────────────


def _parse_python_file(file_path: str, content: str) -> FileNode:
    """Parse a Python file to extract imports and exports."""
    imports: list[ImportInfo] = []
    exports: list[ExportInfo] = []

    try:
        tree = ast.parse(content, file_path)
    except SyntaxError:
        return FileNode(path=file_path, language="python", imports=[], exports=[], lines_of_code=len(content.split("\n")))

    for node in ast.walk(tree):
        # Import statements
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(ImportInfo(
                    source=alias.name,
                    names=[alias.asname or alias.name],
                ))
        elif isinstance(node, ast.ImportFrom):
            names = [alias.asname or alias.name for alias in node.names]
            imports.append(ImportInfo(
                source=node.module or "",
                names=names,
                is_relative=node.level > 0,
            ))

        # Export definitions (top-level functions, classes, variables)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node) or ""
            exports.append(ExportInfo(
                name=node.name,
                kind="function",
                line=node.lineno,
                is_async=isinstance(node, ast.AsyncFunctionDef),
                docstring=docstring[:100],
            ))
        elif isinstance(node, ast.ClassDef):
            docstring = ast.get_docstring(node) or ""
            exports.append(ExportInfo(
                name=node.name,
                kind="class",
                line=node.lineno,
                docstring=docstring[:100],
            ))
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    exports.append(ExportInfo(
                        name=target.id,
                        kind="variable",
                        line=node.lineno,
                    ))

    return FileNode(
        path=file_path,
        language="python",
        imports=imports,
        exports=exports,
        lines_of_code=len(content.split("\n")),
        is_test="test_" in Path(file_path).stem or "_test" in Path(file_path).stem,
        is_config=Path(file_path).name in ("__init__.py", "setup.py", "conftest.py"),
    )


def _parse_typescript_file(file_path: str, content: str) -> FileNode:
    """Parse a TypeScript/JavaScript file for imports and exports using regex."""
    imports: list[ImportInfo] = []
    exports: list[ExportInfo] = []

    # Import patterns
    import_patterns = [
        # import { X, Y } from 'module'
        re.compile(r"import\s*(?:type\s*)?\{([^}]+)\}\s*from\s*['\"]([^'\"]+)['\"]"),
        # import X from 'module'
        re.compile(r"import\s+(\w+)\s+from\s*['\"]([^'\"]+)['\"]"),
        # import * as X from 'module'
        re.compile(r"import\s+\*\s+as\s+(\w+)\s+from\s*['\"]([^'\"]+)['\"]"),
    ]

    for line in content.split("\n"):
        for pattern in import_patterns:
            match = pattern.search(line)
            if match:
                if len(match.groups()) == 2:
                    names = [n.strip() for n in match.group(1).split(",") if n.strip()]
                    names = [n.replace(" as ", ":") for n in names]
                    imports.append(ImportInfo(
                        source=match.group(2),
                        names=names,
                        is_type_only="import type" in line,
                    ))

    # Export patterns
    export_patterns = [
        (r"export\s+(?:default\s+)?(?:async\s+)?function\s+(\w+)", "function"),
        (r"export\s+(?:default\s+)?class\s+(\w+)", "class"),
        (r"export\s+(?:default\s+)?const\s+(\w+)", "const"),
        (r"export\s+(?:default\s+)?interface\s+(\w+)", "interface"),
        (r"export\s+(?:default\s+)?type\s+(\w+)", "type"),
        (r"export\s+(?:default\s+)?enum\s+(\w+)", "enum"),
        (r"export\s+default\s+(\w+)", "default"),
    ]

    for i, line in enumerate(content.split("\n"), 1):
        for pattern, kind in export_patterns:
            match = re.search(pattern, line)
            if match:
                exports.append(ExportInfo(
                    name=match.group(1),
                    kind=kind,
                    line=i,
                    is_default="default" in pattern,
                ))

    return FileNode(
        path=file_path,
        language="typescript" if file_path.endswith(".ts") else "javascript",
        imports=imports,
        exports=exports,
        lines_of_code=len(content.split("\n")),
        is_test=Path(file_path).suffix in (".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx"),
        is_config=Path(file_path).name in ("vite.config.ts", "tsconfig.json", "package.json"),
    )


# ── Context Analyzer ─────────────────────────────────────────────────────


class ProjectContextAnalyzer:
    """Analyzes a codebase to build a comprehensive dependency graph.

    Usage:
        analyzer = ProjectContextAnalyzer()
        graph = analyzer.analyze_directory("./my-project")
        print(graph.summarize())
    """

    def analyze_file(self, file_path: str, content: str | None = None) -> FileNode:
        """Analyze a single file and return its imports and exports."""
        if content is None:
            try:
                content = Path(file_path).read_text()
            except (FileNotFoundError, OSError) as e:
                _logger.warning("ContextAnalyzer: cannot read %s: %s", file_path, e)
                return FileNode(path=file_path, language="unknown")

        ext = Path(file_path).suffix.lower()
        if ext == ".py":
            return _parse_python_file(file_path, content)
        elif ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
            return _parse_typescript_file(file_path, content)
        else:
            return FileNode(
                path=file_path,
                language="other",
                lines_of_code=len(content.split("\n")),
            )

    def analyze_directory(
        self,
        directory: str | Path,
        max_files: int = 200,
        include_extensions: set[str] | None = None,
    ) -> DependencyGraph:
        """Analyze all files in a directory and build a dependency graph.

        Args:
            directory: Path to the project directory
            max_files: Maximum number of files to analyze
            include_extensions: Set of file extensions to include (None = all)

        Returns:
            DependencyGraph with all files, imports, exports
        """
        if include_extensions is None:
            include_extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}

        graph = DependencyGraph()
        dir_path = Path(directory)

        if not dir_path.exists():
            _logger.warning("ContextAnalyzer: directory not found: %s", directory)
            return graph

        files: list[Path] = []
        for ext in include_extensions:
            files.extend(dir_path.rglob(f"*{ext}"))

        # Exclude common non-source directories
        exclude_dirs = {"node_modules", "__pycache__", ".git", "venv", ".venv", "dist", "build", ".next"}
        files = [f for f in files if not any(p in f.parts for p in exclude_dirs)]

        # Limit to max_files
        files = files[:max_files]

        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                node = self.analyze_file(str(file_path), content)
                graph.files[str(file_path)] = node

                # Build lookup indices
                for export in node.exports:
                    if export.kind in ("interface", "type", "class"):
                        graph.type_definitions[export.name] = str(file_path)
                    elif export.kind in ("function", "asyncfunction", "def"):
                        graph.function_definitions[export.name] = str(file_path)

            except Exception as e:
                _logger.debug("ContextAnalyzer: error analyzing %s: %s", file_path, e)

        _logger.info(
            "ContextAnalyzer: analyzed %d files — %d types, %d functions",
            len(graph.files),
            len(graph.type_definitions),
            len(graph.function_definitions),
        )
        return graph

    def find_affected_files(
        self,
        graph: DependencyGraph,
        changed_files: list[str],
    ) -> list[str]:
        """Find all files affected by changes to the given files.

        Uses dependency graph to trace impact propagation.
        """
        affected = set(changed_files)
        queue = list(changed_files)

        while queue:
            current = queue.pop(0)
            dependents = graph.get_dependents(current)
            for dep in dependents:
                if dep not in affected:
                    affected.add(dep)
                    queue.append(dep)

        return list(affected)

    def suggest_test_files(self, graph: DependencyGraph, changed_files: list[str]) -> list[str]:
        """Suggest test files that should be run based on changed files."""
        affected = self.find_affected_files(graph, changed_files)
        test_files: list[str] = []

        for file_path in affected:
            node = graph.files.get(file_path)
            if node and node.is_test:
                test_files.append(file_path)

        # Also find test files for the changed source files
        for file_path in changed_files:
            stem = Path(file_path).stem
            parent = Path(file_path).parent
            # Look for test files with matching name
            for p in parent.glob(f"test_*.py"):
                test_files.append(str(p))
            for p in parent.glob(f"*.test.ts*"):
                test_files.append(str(p))
            for p in parent.glob(f"*.spec.ts*"):
                test_files.append(str(p))

        return list(set(test_files))
