---
name: godot-mcp-tool
type: repo
version: 1.0.0
agent: CodeActAgent
triggers:
  - godot mcp
  - edit scene
  - open scene
  - godot editor
  - visual editor
  - modify scene
  - add node
  - remove node
  - edit node
  - configure project
  - godot gui
  - scene tree
  - godot project
  - export preset
  - connect signal
  - manage project
mcp_tools:
  stdio_servers:
    - name: "godot-mcp"
      command: "python3"
      args: ["skills/godot-mcp-server.py"]
---

# 🎮 Godot MCP — Full Editor Control

This MCP tool gives the agent **full programmatic control** over Godot Engine projects — scene editing, node manipulation, signal connections, export management, and project validation — all without needing the Godot editor GUI.

## How It Works

The custom Godot MCP server (`skills/godot-mcp-server.py`) works by:
1. **Reading/writing .tscn files directly** — Godot scenes are plain text, so we manipulate them directly
2. **Running Godot headless** — For validation, export, and testing
3. **Managing GDScript files** — Creating, reading, and writing scripts

This gives the agent the SAME capabilities as the Godot editor GUI, just through code.

## Available Tools (30+)

### Project Management
| Tool | Description |
|------|-------------|
| `project_info` | Get full project status (scenes, scripts, presets, validation) |
| `validate_project` | Open project headless to check for errors |
| `list_scenes` | List all scenes with node counts and root types |
| `list_scripts` | List all GDScript files |
| `list_resources` | List all asset files (scenes, scripts, images, audio, models) |

### Scene Editing
| Tool | Description |
|------|-------------|
| `read_scene` | Read full scene structure with all nodes and properties |
| `create_scene` | Create new scene with chosen root type |
| `add_node` | Add any node type (Sprite2D, CharacterBody2D, Camera3D, etc.) |
| `remove_node` | Remove node + all children |
| `edit_property` | Set any property (position, scale, visible, script, etc.) |
| `connect_signal` | Connect signals between nodes |

### Export Management
| Tool | Description |
|------|-------------|
| `export_build` | Export for any configured platform preset |
| `create_export_preset` | Create export preset for a platform |
| `list_export_presets` | List all configured export presets |

### Script Management
| Tool | Description |
|------|-------------|
| `read_script` | Read any GDScript file |
| `write_script` | Write/create any GDScript file |
| `run_tests` | Run GUT unit tests |

## What This Enables

Without this tool, the agent could only:
- Write code files manually
- Hope the .tscn edits are correct

With this tool, the agent can:
- ✅ **Read any scene** and understand its full structure
- ✅ **Create new scenes** with proper node hierarchies
- ✅ **Add/edit/remove nodes** in any scene
- ✅ **Connect signals** between nodes
- ✅ **Set properties** on any node
- ✅ **Export builds** for any platform
- ✅ **Validate** the project after every change
- ✅ **Run tests** to verify functionality

## Integration with Existing Godot MCP Tools

If you have the Godot Editor running locally, you can also use these community MCP tools:

| Tool | Requires | Provides |
|------|----------|----------|
| **bradypp/godot-mcp** | Godot Editor open + plugin | Visual scene editing through EditorInterface |
| **Raunaksplanet/godot-mcp-server** | Godot Editor open + plugin | 40+ tools, production-ready |
| **Godot MCP Pro** | Godot Editor + purchase | 160+ tools, UndoRedo, animation |
| **Our Custom MCP (this)** | **Nothing but Godot CLI** | Full control via .tscn + headless |

**Our custom MCP is the only one that doesn't need the Godot Editor GUI running.** It works entirely in the sandbox environment.

## Typical Workflow

```
1. project_info → Understand current project state
2. create_scene → Create a new scene
3. add_node → Add CharacterBody2D (player)
4. add_node → Add Sprite2D (player sprite), CollisionShape2D
5. write_script → Write player controller GDScript
6. edit_property → Attach script to player node
7. validate_project → Check for errors
8. export_build → Export for target platform
```
