---
name: asset-library-sources
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - free assets
  - free models
  - game assets
  - asset library
  - find assets
  - 3d models free
  - sprites free
  - audio free
  - music free
  - sfx free
  - asset pack
  - download assets
  - sketchfab
  - kenney
  - opengameart
  - itch.io assets
  - get art
  - get models
  - get sprites
  - get audio
---

# 📦 Game Asset Library — Free Sources

This skill provides access to thousands of free 2D, 3D, and audio assets for game development. Use these sources when you need art, models, sounds, or music for your game.

---

## 🟢 TIER 1: CURATED FREE SOURCES (Best Quality)

### 1. Kenney.nl — 🏆 Best for Game Development
**URL**: https://kenney.nl/assets  
**License**: CC0 (Public Domain — no attribution needed)  
**Format**: PNG, SVG, 3D (GLTF), Audio (WAV)  
**Content**: 40,000+ sprites, 3D models, UI packs, fonts, sounds

**Download via CLI**:
```bash
# Kenney provides direct download links
# Example: download a specific asset pack
wget "https://kenney.nl/assets/platformer-pack-industrial" -O kenney_platformer.zip
unzip kenney_platformer.zip -d art/kenney_platformer/

# Or use the Kenney asset list
curl -s "https://kenney.nl/assets" | grep -oP 'href="/assets/[^"]*"' | cut -d'"' -f2
```

**Best Packs for Games**:
| Pack | Type | Use For |
|------|------|---------|
| Platformer Pack | Sprites + tiles | 2D platformers |
| Top-down Shooter | Sprites + effects | 2D action games |
| RPG Pack | Characters + items | 2D RPGs |
| Space Kit | Ships + planets | Space games |
| UI Pack | Buttons + panels | Menu/HUD |
| Racing Pack | Cars + tracks | Racing games |
| Audio Pack | SFX + music | Sound effects |

### 2. OpenGameArt.org — 🏆 Largest Collection
**URL**: https://opengameart.org  
**License**: Varies (CC0 mostly, check each asset)  
**Format**: PNG, JPEG, OGG, WAV, BLEND, FBX

**Download via CLI**:
```bash
# Search OpenGameArt via their API
curl -s "https://opengameart.org/api/v1/search?q=2d+platformer&page=1" | python3 -m json.tool

# Download a specific asset pack
# OpenGameArt has direct download links in each asset page
```

**Quick Search Links**:
- 2D Characters: https://opengameart.org/art-search?keys=&title=&field_art_tags_tid_op=and&field_art_tags_tid[]=Character&sort_by=download_count&sort_order=DESC
- 3D Models: https://opengameart.org/art-search-3d
- Sound Effects: https://opengameart.org/art-search-sound
- Music: https://opengameart.org/art-search-music

### 3. Itch.io Free Assets
**URL**: https://itch.io/game-assets/free  
**License**: Varies (check individual packs)

**Best Free Packs**:
| Pack | Creator | Type |
|------|---------|------|
| Free Pixel Art Pack | Various | Sprites |
| Free Sound Effects Pack | Various | SFX |
| Free 3D Model Pack | Various | 3D Models |
| Free UI Pack | Various | Buttons/panels |

---

## 🟡 TIER 2: API-ACCESSIBLE SOURCES (Programmatic)

### 4. Sketchfab Download API
**URL**: https://sketchfab.com/developers/download-api  
**License**: CC (Creative Commons — check each model)  
**Format**: GLTF, GLB, USDZ  
**Models**: 1,000,000+ free models

**Setup**:
```bash
export SKETCHFAB_API_KEY="your_api_key_here"  # Get from sketchfab.com/settings/password
```

**Search & Download Script**:
```bash
#!/bin/bash
# Search Sketchfab for free 3D models
QUERY="$1"
API_URL="https://api.sketchfab.com/v3/search?type=models&q=$QUERY&downloadable=true&archives_flavors=gltf"

curl -s "$API_URL" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data.get('results', []):
    print(f\"{r['name']} — Downloads: {r['vertexCount']} vertices — UID: {r['uid']}\")
"

# Download a model (requires API key and authentication)
# Model UID is from the search results
MODEL_UID="$2"
DOWNLOAD_URL="https://api.sketchfab.com/v3/models/$MODEL_UID/download"
curl -s -H "Authorization: Token $SKETCHFAB_API_KEY" "$DOWNLOAD_URL"
```

**Usage**: Search for "low poly tree", "fantasy sword", "medieval house", "space ship", etc.

---

## 🔵 TIER 3: GENERATED ASSETS (AI-Powered)

### 5. Tripo AI (MCP Tool)
**Requires**: API key from https://platform.tripo3d.ai/  
**Generates**: 3D models from text prompts  
**Integration**:
```bash
npm install -g tripo-ai-mcp-server
# Configure with: export TRIPO_API_SECRET="your_key"
# Then use text_to_3d tool (from tripo-ai-3d skill)
```

### 6. Meshy AI (MCP Tool)
**Requires**: API key from https://www.meshy.ai/api  
**Generates**: 3D models + rigging + animation from text/images  
**Integration**:
```bash
npx @meshy-ai/meshy-mcp-server
# Configure with: export MESHY_API_KEY="msy_your_key"
# Then use text_to_3d tool (from meshy-ai-3d skill)
```

### 7. SFXR / JFXR (Sound Effects)
**URL**: https://sfxr.me/  
**Generates**: Retro sound effects programmatically  
**Usage**: Download generated WAV files and place in audio/sfx/

---

## 📦 ASSET DOWNLOAD PIPELINE

### For 2D Sprites
```bash
# 1. Check Kenney first (best quality)
wget "https://kenney.nl/assets/platformer-pack-industrial" -O /tmp/assets.zip
unzip /tmp/assets.zip -d art/sprites/

# 2. Check OpenGameArt
curl -s "https://opengameart.org/api/v1/search?q=$QUERY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data.get('results', [])[:5]:
    print(f\"  {r['title']} — {r['url']}\")
"

# 3. Generate with AI if needed (via MCP tools)
# text_to_3d: "2D spritesheet of a knight character, 4 directions, 64x64 pixels"
```

### For 3D Models
```bash
# 1. Download from Kenney 3D
wget "https://kenney.nl/assets/3d-platformer-kit" -O /tmp/3d_assets.zip
unzip /tmp/3d_assets.zip -d art/models/

# 2. Convert to Godot-compatible format (GLTF/GLB)
# Most sources already provide GLTF format

# 3. Place in project
mkdir -p art/models/characters art/models/props art/models/environment
# Copy .glb files to appropriate directories

# 4. Create MeshInstance3D in Godot scene
# (Use godot-mcp-tool: add_node with type MeshInstance3D)
```

### For Audio
```bash
# 1. Kenney Audio Pack
wget "https://kenney.nl/assets/impact-sounds" -O /tmp/audio.zip
unzip /tmp/audio.zip -d audio/sfx/

# 2. OpenGameArt Music
# Download and place in audio/music/

# 3. Generate via SFXR
# Visit https://sfxr.me/ → create sounds → save as WAV
```

---

## 📋 QUICK REFERENCE

| Need | Best Source | Format | License |
|------|-------------|--------|---------|
| 2D Sprites | Kenney | PNG | CC0 (free) |
| 2D Tilesets | Kenney / OpenGameArt | PNG | CC0 / CC-BY |
| 3D Models (static) | Sketchfab / Kenney 3D | GLB/GLTF | CC (check) |
| 3D Characters (animated) | Mixamo / Meshy AI | FBX/GLB | Free / API |
| UI Elements | Kenney UI Pack | PNG | CC0 (free) |
| Fonts | Google Fonts | TTF | Open Font License |
| Sound Effects | Kenney Audio / SFXR | WAV/OGG | CC0 (free) |
| Music | OpenGameArt / Incompetech | OGG/MP3 | CC-BY (credit) |
| Textures | OpenGameArt / CC0Textures | PNG/JPG | CC0 / CC-BY |

## 📝 Attribution Requirements

Most free assets require attribution. Keep a CREDITS.txt file in your project:

```
# CREDITS.txt
# List all asset sources and their licenses

## Kenney (CC0)
- Platformer Pack Industrial - kenney.nl/assets/platformer-pack-industrial

## OpenGameArt (CC-BY 3.0)
- [Asset Name] by [Author] - [URL]

## Fonts
- [Font Name] - Open Font License
```

For CC0 assets: No attribution needed (but appreciated).
For CC-BY assets: Must credit the author in your game credits screen.
