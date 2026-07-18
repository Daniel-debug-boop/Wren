---
name: meshy-ai-3d
type: repo
version: 1.0.0
agent: CodeActAgent
triggers:
  - meshy
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
  - 3d print
  - model rig
  - animate model
mcp_tools:
  stdio_servers:
    - name: "meshy-ai"
      command: "npx"
      args: ["-y", "@meshy-ai/meshy-mcp-server"]
      env:
        MESHY_API_KEY: "${MESHY_API_KEY}"
---

# 🎨 Meshy AI — 3D Model Generation

This tool enables the agent to generate high-quality 3D models from text descriptions or images using Meshy AI's API, with 24+ tools for generation, refinement, rigging, animation, and 3D printing.

## Setup

1. Get your API key from https://www.meshy.ai/api
2. Configure the API key:
   - **In Settings**: Add `MESHY_API_KEY` in the Wren Settings UI under Environment Variables
   - **Or via CLI**: `export MESHY_API_KEY="msy_YOUR_API_KEY"`
   - **In config**: Add to your Wren config file: `MESHY_API_KEY: msy_YOUR_API_KEY`
3. Alternative install (standalone, not needed for Wren):
   ```bash
   npx add-mcp @meshy-ai/meshy-mcp-server --env MESHY_API_KEY=msy_YOUR_API_KEY
   ```

## When to Use Meshy AI vs Tripo AI

| For... | Use | Reason |
|-------|-----|--------|
| Animated game characters | **Meshy AI** | Built-in rigging + animation presets |
| 3D printing | **Meshy AI** | Dedicated printability and repair tools |
| Quick static props | **Tripo AI** | Faster for simple objects |
| Image-to-3D with multiple views | **Tripo AI** | Multi-view input support |
| Full character pipeline | **Meshy AI** | Text → model → rig → animate all in one |
| Game-ready assets | **Either** | Both export GLTF/GLB for Godot |

## Available Tools

### 3D Generation
| Tool | Description |
|------|-------------|
| `text_to_3d` | Generate 3D model from text prompt (2-step: preview → refine) |
| `image_to_3d` | Generate 3D model from an image |
| `multi_image_to_3d` | Generate from multiple view images |

### Post-Processing
| Tool | Description |
|------|-------------|
| `remesh` | Optimize mesh topology for game engines |
| `retexture` | Apply new textures to existing models |
| `rig` | Set up skeleton/armature for animation |
| `animate` | Apply predefined animations to rigged models |

### 3D Printing
| Tool | Description |
|------|-------------|
| `printability_analysis` | Check if model is 3D-printable |
| `auto_repair` | Fix mesh issues for printing |
| `convert_to_3mf` | Export for multi-color 3D printing |

### Task Management
| Tool | Description |
|------|-------------|
| `get_task` | Check status of any generation task |
| `list_tasks` | View all recent generation tasks |
| `cancel_task` | Cancel a running task |
| `get_credits` | Check remaining API credits |

## Usage in Game Development

### Full Character Pipeline
```
1. text_to_3d: "stylized low-poly warrior woman with armor and spear, game-ready, PBR textures"
   → Wait for preview task to complete
   
2. remesh: preview_task_id, target_count: 5000
   → Optimize for game engine (reduce polygon count)
   
3. rig: remeshed_task_id
   → Add skeleton for animation
   
4. animate: rigged_task_id, animation: "running"
   → Or: "walking", "jumping", "attacking", "idle"
   
5. Download: Get GLTF/GLB file → Import into Godot
   → Create AnimationTree with blend spaces
```

### Quick Prop Generation
```
1. image_to_3d: "sword_design.png"
2. remesh: task_id, target_count: 2000
3. Convert to GLB → Import as MeshInstance3D in Godot
4. Add collision shape for interaction
```

### Environment Assets
```
text_to_3d: "fantasy environment pack: trees, rocks, bushes, flowers, low-poly style, 500-2000 triangles each"
→ Generate multiple assets in batch
→ Import each as separate scene in Godot
→ Place in world using MultiMeshInstance3D for performance
```

## Integration with Godot

```bash
# After generating a model:
# 1. Export as GLB/GLTF from Meshy
# 2. Place in Godot project: art/models/character.glb
# 3. Create MeshInstance3D node referencing the resource
# 4. Add CollisionShape3D for physics
# 5. If rigged and animated, create AnimationTree + AnimationPlayer

# For performance on mobile:
# - Use remesh to keep triangles under 5000 per character
# - Use texture atlases for multiple models
# - Enable LOD in Godot's import settings
```

## Credit Usage

Each generation consumes credits. Free tier typically includes 100-200 credits.
Check remaining credits: `get_credits` tool
