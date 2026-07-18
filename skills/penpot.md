---
# Penpot design platform MCP integration
name: penpot
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - penpot
  - design tokens
  - design system
  - design to code
  - figma
  - design file
  - components
  - variants
  - design tokens
  - ui design
  - wireframe
  - prototype
---

# Penpot Design Platform Integration

## What is Penpot?
Penpot is the open-source design platform (like Figma but open source). It connects to Wren via MCP for design-to-code workflows.

## Setup (User Required)
Penpot MCP requires user configuration. The user must:
1. Have a Penpot account (self-hosted or design.penpot.app)
2. Enable MCP in Penpot: **Your account → Integrations → MCP Server**
3. Generate an MCP key
4. Configure in Wren settings under MCP Servers

### Connection Modes

**Remote MCP (recommended):**
- URL: `https://<penpot-domain>/mcp/stream?userToken=<MCP_KEY>`
- Auth: MCP key in URL

**Local MCP (advanced):**
- URL: `http://localhost:4401/mcp`
- Auth: uses active Penpot browser session
- Run: `npx -y @penpot/mcp@stable`

## Agent Capabilities

When Penpot MCP is connected, the agent can:

### Read Operations (safe)
- `high_level_overview` — Get design file structure overview
- `penpot_api_info` — Get API information
- List pages, components, styles, design tokens

### Write Operations (use with caution)
- `execute_code` — Execute code against the design file
- `export_shape` — Export shapes as SVG/images
- `import_image` — Import images (local mode only)
- Create/modify components, styles, tokens

## Design-to-Code Workflow

1. Agent reads design structure from Penpot
2. Extracts layout, colors, typography, spacing
3. Generates semantic HTML/CSS or React components
4. Uses Wren' existing token system for consistency

## Design Token Extraction

The agent can extract from Penpot:
- Color palettes → CSS custom properties
- Typography → font families, sizes, weights
- Spacing → margins, paddies, gaps
- Components → reusable UI patterns

## Safety Notes
- Start with read-only operations first
- Agent should describe changes before applying them
- Prefer small, reversible steps
- Never auto-apply large design refactors without user confirmation
