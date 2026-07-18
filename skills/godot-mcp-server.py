#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           WREN CUSTOM GODOT MCP SERVER v2                   ║
║  Full programmatic control of Godot Engine projects         ║
║  - Read/write .tscn files via proper Godot-format parsing   ║
║  - Run Godot headless for validation, export, testing       ║
║  - Manage scenes, nodes, signals, resources                 ║
║  - No Godot plugin needed — works entirely via CLI + files  ║
╚══════════════════════════════════════════════════════════════╝
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

# ─── MCP Protocol ────────────────────────────────────────────

SERVER_NAME = "wren-godot-mcp"
SERVER_VERSION = "2.0.0"

_current_request_id: str | None = None


def mcp_send(msg: dict) -> None:
    """Send a JSON-RPC message (newline-delimited JSON) to the MCP client."""
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def mcp_respond(result: Any, request_id: str) -> None:
    mcp_send({"jsonrpc": "2.0", "result": result, "id": request_id})


def mcp_error(code: int, message: str, request_id: str) -> None:
    mcp_send({"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": request_id})


def mcp_notification(method: str, params: dict | None = None) -> None:
    msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
    if params:
        msg["params"] = params
    mcp_send(msg)


# ─── Godot Project Management ─────────────────────────────────

def _format_tscn_value(key: str, value: str) -> str:
    """Format a .tscn property value according to Godot's expected format.

    Only string values get quoted. Numbers, booleans, vectors, colors,
    and resource refs stay unquoted.
    """
    stripped = value.strip()
    # Already a Godot-native literal (Vector2, Color, etc.)
    if stripped.startswith("Vector") or stripped.startswith("Color") or \
       stripped.startswith("Transform") or stripped.startswith("Rect") or \
       stripped.startswith("Quaternion") or stripped.startswith("Plane") or \
       stripped.startswith("AABB") or stripped.startswith("Basis") or \
       stripped.startswith("NodePath") or stripped.startswith("RID") or \
       stripped.startswith("Packed") or stripped.startswith("Array") or \
       stripped.startswith("Dictionary"):
        return stripped
    # Resource references
    if stripped.startswith("SubResource") or stripped.startswith("ExtResource"):
        return stripped
    # Booleans
    if stripped.lower() in ("true", "false"):
        return stripped.lower()
    # Numeric
    if re.match(r'^-?\d+(\.\d+)?([eE][+-]?\d+)?$', stripped):
        return stripped
    # Null
    if stripped == "null":
        return stripped
    # Groups
    if stripped.startswith("[") and stripped.endswith("]"):
        return stripped
    # Strings get quoted
    return f'"{stripped}"'


class GodotProject:
    """Manages a Godot project: reading .tscn files, running headless commands."""

    def __init__(self, project_path: str | None = None):
        self.project_path = Path(project_path or os.getcwd()).resolve()

    def initialize(self) -> dict[str, Any]:
        """Ensure the project exists, creating a minimal one if needed."""
        project_file = self.project_path / "project.godot"
        created = False
        if not project_file.exists():
            project_file.write_text(
                "; Engine configuration file.\n"
                "[application]\n"
                f'config/name="{self.project_path.name}"\n'
                'run/main_scene="res://scenes/main.tscn"\n'
            )
            for d in ["scenes", "scripts", "art", "audio"]:
                (self.project_path / d).mkdir(exist_ok=True)
            created = True
        return {
            "project_path": str(self.project_path),
            "name": self.project_path.name,
            "created": created,
            "valid": self.validate_project().get("success", False),
        }

    def _run_godot(self, args: list[str], timeout: int = 60) -> dict[str, Any]:
        """Run a Godot headless command and return the result."""
        if not self._godot_installed():
            return {"success": False, "error": "Godot not found. Install with the 'godot-installer' skill."}
        cmd = ["godot", "--headless", "--path", str(self.project_path)] + args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:2000],
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {timeout}s"}
        except FileNotFoundError:
            return {"success": False, "error": "Godot command not found"}

    @staticmethod
    def _godot_installed() -> bool:
        try:
            subprocess.run(["godot", "--version"], capture_output=True, timeout=5)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    # ─── Project Info ──────────────────────────────────────

    def project_info(self) -> dict[str, Any]:
        """Get comprehensive project information."""
        info = {
            "project_path": str(self.project_path),
            "project_name": self.project_path.name,
            "project_file_exists": (self.project_path / "project.godot").exists(),
            "godot_installed": self._godot_installed(),
            "scenes": len(list(self.project_path.rglob("*.tscn"))),
            "scripts": len(list(self.project_path.rglob("*.gd"))),
        }
        if self._godot_installed():
            validation = self._run_godot(["--quit"], timeout=15)
            info["project_valid"] = validation.get("success", False)
        else:
            info["project_valid"] = False
            info["godot_version"] = "Not installed"
        return info

    def validate_project(self) -> dict[str, Any]:
        """Open the project headless to check for errors."""
        return self._run_godot(["--quit"], timeout=15)

    # ─── Scene Operations ──────────────────────────────────

    def _parse_tscn(self, path: Path) -> list[dict[str, Any]]:
        """Parse a .tscn file into a dict with preamble, nodes, and postamble.

        Preserves non-node lines (extresources, subresources, connections)
        so the round-trip doesn't lose data.
        """
        nodes: list[dict[str, Any]] = []
        preamble: list[str] = []  # Lines before first node
        postamble: list[str] = []  # Non-node lines interleaved with nodes
        current_node: dict[str, Any] | None = None
        in_resource = False

        text = path.read_text(encoding="utf-8") if path.exists() else ""

        for line in text.split("\n"):
            stripped = line.strip()

            # Track resource blocks
            if stripped.startswith("[resource"):
                in_resource = True
                if current_node:
                    current_node.get("_raw_lines", []).append(line)
                elif not nodes:
                    preamble.append(line)
                continue
            if stripped.startswith("[/resource"):
                in_resource = False
                if current_node:
                    current_node.get("_raw_lines", []).append(line)
                elif not nodes:
                    preamble.append(line)
                continue

            # Track node definitions
            if stripped.startswith("[node"):
                if current_node:
                    nodes.append(current_node)
                # Parse node attributes from the declaration line
                attrs = {}
                for match in re.finditer(r'(\w+)\s*=\s*("[^"]*"|[^\s]+)', line):
                    key = match.group(1)
                    val = match.group(2).strip('"')
                    attrs[key] = val
                current_node = {
                    "name": attrs.get("name", "Unknown"),
                    "type": attrs.get("type", "Node"),
                    "parent": attrs.get("parent", "."),
                    "groups": attrs.get("groups", ""),
                    "properties": {},
                    "_raw_lines": [line],
                }
                in_node_block = True
                continue

            if current_node:
                current_node["_raw_lines"].append(line)
                # Parse key=value pairs
                if "=" in line and not stripped.startswith("[") and not in_resource:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"')
                    if key and not key.startswith("_"):
                        current_node["properties"][key] = value
            elif not nodes:
                preamble.append(line)
            else:
                postamble.append(line)

        if current_node:
            nodes.append(current_node)

        return {
            "preamble": preamble,
            "nodes": nodes,
            "postamble": postamble,
            "raw": text,
        }

    def _serialize_tscn(self, parsed: dict) -> str:
        """Serialize parsed scene data back to .tscn format.

        Preserves original formatting as much as possible by using
        _raw_lines. For new/modified nodes, generates fresh output.
        """
        lines = []

        # Preamble (extresources, subresources, format)
        for line in parsed.get("preamble", []):
            lines.append(line)

        # Nodes
        for node in parsed.get("nodes", []):
            raw = node.get("_raw_lines")
            if raw:
                # If we have the original raw lines, use them (preserves formatting)
                # But update the declaration line if properties changed
                lines.extend(raw)
            else:
                # Generate fresh node definition
                attr_parts = [f'name="{node["name"]}"', f'type="{node["type"]}"']
                if node.get("parent") and node["parent"] != ".":
                    attr_parts.append(f'parent="{node["parent"]}"')
                if node.get("groups"):
                    attr_parts.append(f'groups={node["groups"]}')
                decl = f'[node {" ".join(attr_parts)}]'
                lines.append(decl)
                for key, value in node.get("properties", {}).items():
                    formatted = _format_tscn_value(key, value)
                    lines.append(f'{key} = {formatted}')

        # Postamble (connections, etc.)
        for line in parsed.get("postamble", []):
            lines.append(line)

        return "\n".join(lines) + ("\n" if lines else "")

    def list_scenes(self) -> list[dict[str, Any]]:
        scenes = []
        for f in sorted(self.project_path.rglob("*.tscn")):
            if ".godot/" in str(f):
                continue
            relative = str(f.relative_to(self.project_path))
            try:
                parsed = self._parse_tscn(f)
                root = parsed["nodes"][0] if parsed["nodes"] else None
                scenes.append({
                    "path": relative,
                    "node_count": len(parsed["nodes"]),
                    "root_type": root["type"] if root else "None",
                    "root_name": root["name"] if root else "None",
                    "size": f.stat().st_size,
                })
            except Exception as e:
                scenes.append({"path": relative, "error": str(e)})
        return scenes

    def read_scene(self, scene_path: str) -> dict[str, Any]:
        full_path = self.project_path / scene_path
        if not full_path.exists():
            scenes = [s["path"] for s in self.list_scenes()]
            return {"error": f"Scene not found: {scene_path}", "available_scenes": scenes}
        parsed = self._parse_tscn(full_path)
        return {
            "path": scene_path,
            "node_count": len(parsed["nodes"]),
            "nodes": parsed["nodes"],
            "preamble": len(parsed.get("preamble", [])),
        }

    def create_scene(self, scene_path: str, root_type: str = "Node",
                     root_name: str = "Root") -> dict[str, Any]:
        full_path = self.project_path / scene_path
        if full_path.exists():
            return {"error": f"Scene already exists: {scene_path}"}
        full_path.parent.mkdir(parents=True, exist_ok=True)
        parsed = {
            "preamble": ['[gd_scene format=3 uid="uid://new_scene"]'],
            "nodes": [{"name": root_name, "type": root_type, "parent": ".", "properties": {}, "_raw_lines": None}],
            "postamble": [],
        }
        full_path.write_text(self._serialize_tscn(parsed), encoding="utf-8")
        return {"success": True, "path": scene_path, "root_type": root_type, "root_name": root_name}

    def add_node(self, scene_path: str, node_name: str, node_type: str,
                 parent: str = ".", properties: dict | None = None) -> dict[str, Any]:
        full_path = self.project_path / scene_path
        if not full_path.exists():
            return {"error": f"Scene not found: {scene_path}"}
        parsed = self._parse_tscn(full_path)
        new_node = {
            "name": node_name,
            "type": node_type,
            "parent": parent,
            "properties": properties or {},
            "_raw_lines": None,  # Will be serialized fresh
        }
        parsed["nodes"].append(new_node)
        full_path.write_text(self._serialize_tscn(parsed), encoding="utf-8")
        return {"success": True, "node": new_node, "total_nodes": len(parsed["nodes"])}

    def remove_node(self, scene_path: str, node_name: str) -> dict[str, Any]:
        full_path = self.project_path / scene_path
        if not full_path.exists():
            return {"error": f"Scene not found: {scene_path}"}
        parsed = self._parse_tscn(full_path)
        # Find all names to remove (node + children)
        to_remove = {node_name}
        changed = True
        while changed:
            changed = False
            for n in parsed["nodes"]:
                if n.get("parent", ".") in to_remove and n["name"] not in to_remove:
                    to_remove.add(n["name"])
                    changed = True
        original = len(parsed["nodes"])
        parsed["nodes"] = [n for n in parsed["nodes"] if n["name"] not in to_remove]
        full_path.write_text(self._serialize_tscn(parsed), encoding="utf-8")
        return {
            "success": True,
            "removed": list(to_remove),
            "removed_count": original - len(parsed["nodes"]),
            "remaining_count": len(parsed["nodes"]),
        }

    def edit_node_property(self, scene_path: str, node_name: str,
                           key: str, value: str) -> dict[str, Any]:
        full_path = self.project_path / scene_path
        if not full_path.exists():
            return {"error": f"Scene not found: {scene_path}"}
        parsed = self._parse_tscn(full_path)
        for n in parsed["nodes"]:
            if n["name"] == node_name:
                n["properties"][key] = value
                n["_raw_lines"] = None  # Force re-serialization
                full_path.write_text(self._serialize_tscn(parsed), encoding="utf-8")
                return {"success": True, "node": node_name, "property": key, "new_value": value}
        return {"error": f"Node not found: {node_name}"}

    def connect_signal(self, scene_path: str, source_node: str,
                       signal_name: str, target_node: str,
                       method_name: str) -> dict[str, Any]:
        """Connect a signal using a temporary Godot script."""
        if not self._godot_installed():
            return {"success": False, "error": "Godot not installed"}
        # Instead, add the connection directly to the scene file
        full_path = self.project_path / scene_path
        if not full_path.exists():
            return {"error": "Scene not found"}
        text = full_path.read_text(encoding="utf-8")
        conn = f'[connection signal="{signal_name}" from="{source_node}" to="{target_node}" method="{method_name}"]'
        text += "\n" + conn
        full_path.write_text(text, encoding="utf-8")
        return {"success": True, "connection": f"{signal_name}: {source_node} → {target_node}.{method_name}"}

    # ─── Export ────────────────────────────────────────────

    def list_export_presets(self) -> list[str]:
        presets_file = self.project_path / "export_presets.cfg"
        if not presets_file.exists():
            return []
        presets = []
        for line in presets_file.read_text().split("\n"):
            if line.startswith("name="):
                presets.append(line.split("=", 1)[1].strip().strip('"'))
        return presets

    def create_export_preset(self, preset_name: str, platform: str) -> dict[str, Any]:
        presets_file = self.project_path / "export_presets.cfg"
        existing = presets_file.read_text() if presets_file.exists() else ""
        # Count existing presets
        count = existing.count("[preset.")
        preset_entry = f"""
[preset.{count}]
name="{preset_name}"
platform="{platform}"
runnable=true
export_filter="all_resources"
include_filter=""
exclude_filter=""
custom_features=""
"""
        with open(presets_file, "a") as f:
            f.write(preset_entry)
        return {"success": True, "preset": preset_name, "platform": platform}

    def export_build(self, preset: str, output_path: str | None = None) -> dict[str, Any]:
        args = ["--export-release", preset]
        if output_path:
            args.append(output_path)
        return self._run_godot(args, timeout=300)

    # ─── Script Operations ─────────────────────────────────

    def list_scripts(self) -> list[dict[str, Any]]:
        scripts = []
        for f in sorted(self.project_path.rglob("*.gd")):
            if ".godot/" in str(f):
                continue
            relative = str(f.relative_to(self.project_path))
            scripts.append({
                "path": relative,
                "size": f.stat().st_size,
                "lines": len(f.read_text(encoding="utf-8").split("\n")),
            })
        return scripts

    def read_script(self, script_path: str) -> dict[str, Any]:
        full_path = self.project_path / script_path
        if not full_path.exists():
            return {"error": f"Script not found: {script_path}"}
        return {"path": script_path, "content": full_path.read_text(encoding="utf-8")}

    def write_script(self, script_path: str, content: str) -> dict[str, Any]:
        full_path = self.project_path / script_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return {"success": True, "path": script_path}

    # ─── Resource Listing ──────────────────────────────────

    def list_resources(self) -> list[dict[str, Any]]:
        resources = []
        extensions = {".tscn", ".gd", ".tres", ".res", ".png", ".jpg", ".jpeg",
                      ".ogg", ".wav", ".mp3", ".glb", ".gltf", ".ttf", ".otf",
                      ".svg", ".webp", ".bmp", ".ktx", ".dds"}
        for f in sorted(self.project_path.rglob("*")):
            if f.suffix.lower() in extensions and ".godot/" not in str(f):
                relative = str(f.relative_to(self.project_path))
                resources.append({"path": relative, "type": f.suffix, "size": f.stat().st_size})
        return resources


# ─── MCP Server Engine ────────────────────────────────────────

class MCPServer:
    """MCP protocol server that handles initialize, tools/list, tools/call, etc."""

    def __init__(self):
        self.project = GodotProject()
        self._tools: dict[str, dict] = {}
        self._initialized = False
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all available tools with their schemas."""
        self._tools = {
            "project_info": {
                "description": "Get project info: path, name, scene count, script count, validation status",
                "inputSchema": {"type": "object", "properties": {}},
            },
            "initialize_project": {
                "description": "Initialize/create a Godot project in the current directory",
                "inputSchema": {"type": "object", "properties": {}},
            },
            "validate_project": {
                "description": "Open the project headless to check for errors (catches problems early)",
                "inputSchema": {"type": "object", "properties": {}},
            },
            "list_scenes": {
                "description": "List all .tscn scene files with node counts and root types",
                "inputSchema": {"type": "object", "properties": {}},
            },
            "read_scene": {
                "description": "Read a scene file and get its full node tree structure",
                "inputSchema": {
                    "type": "object",
                    "properties": {"path": {"type": "string", "description": "Scene path relative to project root (e.g., scenes/main.tscn)"}},
                    "required": ["path"],
                },
            },
            "create_scene": {
                "description": "Create a new scene file with a root node",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Scene path (e.g., scenes/level1.tscn)"},
                        "root_type": {"type": "string", "description": "Root node type (Node2D, Node3D, Control, Node)", "default": "Node"},
                        "root_name": {"type": "string", "description": "Root node name", "default": "Root"},
                    },
                    "required": ["path"],
                },
            },
            "add_node": {
                "description": "Add a node to an existing scene",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "scene_path": {"type": "string", "description": "Scene file path"},
                        "node_name": {"type": "string", "description": "Name for the new node"},
                        "node_type": {"type": "string", "description": "Godot node type (e.g., Sprite2D, CharacterBody2D, Camera2D, Node2D)"},
                        "parent": {"type": "string", "description": "Parent node name ('.' for root)", "default": "."},
                        "properties": {"type": "object", "description": "Node properties as key:value pairs", "default": {}},
                    },
                    "required": ["scene_path", "node_name", "node_type"],
                },
            },
            "remove_node": {
                "description": "Remove a node and all its children from a scene",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "scene_path": {"type": "string", "description": "Scene file path"},
                        "node_name": {"type": "string", "description": "Name of the node to remove"},
                    },
                    "required": ["scene_path", "node_name"],
                },
            },
            "edit_node_property": {
                "description": "Set a property on a node (e.g., position, scale, visible, script, modulate)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "scene_path": {"type": "string", "description": "Scene file path"},
                        "node_name": {"type": "string", "description": "Node name"},
                        "key": {"type": "string", "description": "Property name (position, scale, rotation, visible, script, modulate)"},
                        "value": {"type": "string", "description": "Property value (use Godot format: Vector2(100,200), true, 'res://script.gd')"},
                    },
                    "required": ["scene_path", "node_name", "key", "value"],
                },
            },
            "connect_signal": {
                "description": "Connect a signal between two nodes in a scene",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "scene_path": {"type": "string", "description": "Scene file path"},
                        "source_node": {"type": "string", "description": "Source node name"},
                        "signal_name": {"type": "string", "description": "Signal name (e.g., pressed, body_entered, timeout)"},
                        "target_node": {"type": "string", "description": "Target node name"},
                        "method_name": {"type": "string", "description": "Method to call on target (e.g., _on_button_pressed)"},
                    },
                    "required": ["scene_path", "source_node", "signal_name", "target_node", "method_name"],
                },
            },
            "list_scripts": {
                "description": "List all GDScript (.gd) files in the project",
                "inputSchema": {"type": "object", "properties": {}},
            },
            "read_script": {
                "description": "Read a GDScript file's content",
                "inputSchema": {
                    "type": "object",
                    "properties": {"path": {"type": "string", "description": "Script path (e.g., scripts/player.gd)"}},
                    "required": ["path"],
                },
            },
            "write_script": {
                "description": "Write or overwrite a GDScript file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Script path"},
                        "content": {"type": "string", "description": "GDScript code content"},
                    },
                    "required": ["path", "content"],
                },
            },
            "list_resources": {
                "description": "List all resource/asset files (scenes, scripts, images, audio, models, fonts)",
                "inputSchema": {"type": "object", "properties": {}},
            },
            "list_export_presets": {
                "description": "List configured export presets (platform targets)",
                "inputSchema": {"type": "object", "properties": {}},
            },
            "create_export_preset": {
                "description": "Create a new export preset for a platform",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "preset_name": {"type": "string", "description": "Preset name (e.g., Android, Windows Desktop, macOS, Linux/X11)"},
                        "platform": {"type": "string", "description": "Godot platform ID (e.g., Android, Windows, macOS, Linux)"},
                    },
                    "required": ["preset_name", "platform"],
                },
            },
            "export_build": {
                "description": "Export the project for a platform using a configured preset (requires export templates)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "preset": {"type": "string", "description": "Export preset name (e.g., Android, Windows Desktop)"},
                        "output_path": {"type": "string", "description": "Custom output path (optional)"},
                    },
                    "required": ["preset"],
                },
            },
            "run_tests": {
                "description": "Run GDScript unit tests using the GUT framework",
                "inputSchema": {"type": "object", "properties": {}},
            },
        }

    # ─── Request Handlers ──────────────────────────────────

    def handle_initialize(self, params: dict, req_id: str) -> None:
        """Handle the MCP initialize request."""
        mcp_respond({
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {tool_name: schema for tool_name, schema in self._tools.items()},
            },
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        }, req_id)

    def handle_tools_list(self, params: dict, req_id: str) -> None:
        """Handle tools/list request — return all available tools."""
        tools_list = [{"name": name, "description": info["description"],
                       "inputSchema": info["inputSchema"]}
                      for name, info in self._tools.items()]
        mcp_respond({"tools": tools_list}, req_id)

    def handle_tools_call(self, params: dict, req_id: str) -> None:
        """Handle tools/call request — execute a tool."""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        handlers = {
            "project_info": lambda: self.project.project_info(),
            "initialize_project": lambda: self.project.initialize(),
            "validate_project": lambda: self.project.validate_project(),
            "list_scenes": lambda: {"scenes": self.project.list_scenes()},
            "read_scene": lambda: self.project.read_scene(arguments["path"]),
            "create_scene": lambda: self.project.create_scene(arguments["path"],
                                                              arguments.get("root_type", "Node"),
                                                              arguments.get("root_name", "Root")),
            "add_node": lambda: self.project.add_node(arguments["scene_path"], arguments["node_name"],
                                                      arguments["node_type"], arguments.get("parent", "."),
                                                      arguments.get("properties")),
            "remove_node": lambda: self.project.remove_node(arguments["scene_path"], arguments["node_name"]),
            "edit_node_property": lambda: self.project.edit_node_property(arguments["scene_path"],
                                                                          arguments["node_name"],
                                                                          arguments["key"], arguments["value"]),
            "connect_signal": lambda: self.project.connect_signal(arguments["scene_path"], arguments["source_node"],
                                                                  arguments["signal_name"], arguments["target_node"],
                                                                  arguments["method_name"]),
            "list_scripts": lambda: {"scripts": self.project.list_scripts()},
            "read_script": lambda: self.project.read_script(arguments["path"]),
            "write_script": lambda: self.project.write_script(arguments["path"], arguments["content"]),
            "list_resources": lambda: {"resources": self.project.list_resources()},
            "list_export_presets": lambda: {"presets": self.project.list_export_presets()},
            "create_export_preset": lambda: self.project.create_export_preset(arguments["preset_name"], arguments["platform"]),
            "export_build": lambda: self.project.export_build(arguments["preset"], arguments.get("output_path")),
            "run_tests": lambda: self.project._run_godot(["-s", "addons/gut/gut_cmdln.gd"], timeout=120),
        }

        handler = handlers.get(tool_name)
        if handler:
            try:
                result = handler()
                mcp_respond({"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}, req_id)
            except Exception as e:
                mcp_respond({"content": [{"type": "text", "text": json.dumps({"error": str(e)})}]}, req_id)
        else:
            mcp_error(-32601, f"Unknown tool: {tool_name}", req_id)

    def handle_notifications(self, method: str, params: dict) -> None:
        """Handle notifications (no response needed)."""
        if method == "notifications/initialized":
            self._initialized = True

    def handle_request(self, msg: dict) -> None:
        """Route an incoming JSON-RPC message to the right handler."""
        method = msg.get("method", "")
        params = msg.get("params", {})
        req_id = msg.get("id")

        # Notifications have no id
        if req_id is None:
            self.handle_notifications(method, params)
            return

        # Before initialized, only accept initialize
        if not self._initialized and method != "initialize":
            mcp_error(-32000, "Server not initialized. Send initialize first.", req_id)
            return

        handlers = {
            "initialize": self.handle_initialize,
            "tools/list": self.handle_tools_list,
            "tools/call": self.handle_tools_call,
        }

        handler = handlers.get(method)
        if handler:
            handler(params, req_id)
        else:
            mcp_error(-32601, f"Method not found: {method}", req_id)

    def run(self) -> None:
        """Main server loop — reads JSON-RPC messages from stdin."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                self.handle_request(msg)
            except json.JSONDecodeError:
                # If we have an id, send error; otherwise ignore
                mcp_error(-32700, f"Parse error: invalid JSON", None)


# ─── Entry Point ─────────────────────────────────────────────

def main():
    server = MCPServer()
    server.run()


if __name__ == "__main__":
    main()
