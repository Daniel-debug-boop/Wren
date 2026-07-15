---
name: nano-banana
description: Image generation and editing via Gemini API. Triggers on: generate image, create image, draw, illustration, mockup, screenshot, visual, picture, photo, art, design asset, banner, icon, logo concept, wireframe, style transfer.
---

# Nano Banana — Image Generation

Generate and edit images using Google Gemini 2.5 Flash via MCP.

## Tools

| Tool | What it does |
|------|-------------|
| `generate_image` | Create new image from text prompt |
| `edit_image` | Modify existing image with text prompt |
| `continue_editing` | Continue editing the last image |
| `get_last_image_info` | Check current image state |
| `configure_gemini_token` | Set API key |
| `get_configuration_status` | Check if API key is set |

## Usage

### Generate
```
Generate an image of a sunset over mountains
```

### Edit
```
Edit this image to add birds in the sky
```

### Iterate
```
Continue editing to make it more dramatic
```

### Style Transfer
```
Generate a logo, then use a reference image to match a specific style
```

## File Storage

Images auto-save to `./generated_imgs/` (Linux/Mac) or `%USERPROFILE%\Documents\nano-banana-images\` (Windows).

Naming: `generated-[timestamp]-[id].png`, `edited-[timestamp]-[id].png`

## Tips

- Be specific in prompts: "A minimalist logo for a coffee shop, flat design, warm colors" > "a logo"
- Use `continue_editing` to iterate — don't try to get it perfect in one shot
- Reference images work for style transfer — provide a style reference with `edit_image`
- Check `get_last_image_info` to see what was generated before continuing

## API Key

Set via environment variable: `GEMINI_API_KEY`
Or use `configure_gemini_token` tool at runtime.
