---
name: tripo-ai-3d
type: repo
version: 1.0.0
agent: CodeActAgent
triggers:
  - tripo
  - 3d model
  - 3d asset
  - generate 3d
  - create model
  - text to 3d
  - image to 3d
  - model generation
  - 3d art
  - game asset
  - 3d character
  - 3d object
  - 3d prop
  - game model
mcp_tools:
  stdio_servers:
    - name: "tripo-ai"
      command: "npx"
      args: ["-y", "tripo-ai-mcp-server"]
      env:
        TRIPO_API_SECRET: "${TRIPO_API_SECRET}"
---

# 🎨 Tripo AI — 3D Model Generation

This tool enables the agent to generate 3D models from text descriptions or images using Tripo AI's API.

## Setup

1. Get your API key from https://platform.tripo3d.ai/
2. Configure the API key:
   - **In Settings**: Add `TRIPO_API_SECRET` in the Wren Settings UI under Environment Variables
   - **Or via CLI**: `export TRIPO_API_SECRET="your_api_key_here"`
   - **In config**: Add to your Wren config file: `TRIPO_API_SECRET: your_api_key_here`

## When to Use Tripo AI vs Meshy AI

| For... | Use | Reason |
|-------|-----|--------|
| Quick static props | **Tripo AI** | Faster generation, good for simple objects |
| Animated characters | **Meshy AI** | Built-in rigging and animation pipeline |
| Text-to-3D prototyping | **Either** | Both support text prompts well |
| Image-to-3D | **Tripo AI** | Better multi-view to 3D support |
| 3D printing | **Meshy AI** | Dedicated printability analysis tools |
| Game-ready low-poly | **Either** | Both support remeshing |

## Available Tools

| Tool | Description |
|------|-------------|
| `text_to_3d` | Generate a 3D model from a text prompt |
| `image_to_3d` | Generate a 3D model from an image |
| `multiview_to_3d` | Generate a 3D model from multiple images |
| `refine_model` | Improve the quality of a draft model |
| `texture_model` | Apply or re-texture a model |
| `stylize_model` | Apply styles (Lego, voxel, Minecraft) |
| `convert_model` | Export to GLTF, FBX, OBJ, STL, USDZ, 3MF |
| `rig_model` | Set up a model for animation |
| `retarget_animation` | Apply preset animations |
| `get_task_status` | Check generation progress |

## Usage in Game Development

### Generate a 3D Character
```
text_to_3d with prompt: "low-poly stylized knight character with sword and shield, game-ready, 1000 triangles"
→ Convert to GLTF → Import into Godot scene
```

### Generate a 3D Prop
```
text_to_3d with prompt: "fantasy treasure chest with gold trim, PBR texture, 500 triangles"
→ Refine model → Convert to GLB → Add to game world
```

### Generate from Concept Art
```
image_to_3d with image: "concept_art.png"
→ Generate → Refine → Convert to Godot-compatible format
```

## Export for Godot

```bash
# After generation, convert to Godot-compatible format
# Tripo supports: GLTF, FBX, OBJ, STL, USDZ, 3MF
# For Godot, use GLTF or GLB:
convert_model with format: "glb"
# Then import into Godot project and create MeshInstance3D
```

## Credit Requirement

Each generation uses credits from your Tripo account. Check balance:
```bash
# Check remaining credits via the API dashboard
```
