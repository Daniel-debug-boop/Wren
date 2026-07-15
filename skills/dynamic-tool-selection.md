---
name: dynamic-tool-selection
type: repo
version: 1.0.0
agent: CodeActAgent
triggers:
  - tool selection
  - missing tool
  - capability not found
  - install tool
  - dynamic skill
  - tool registry
  - discover tools
  - missing capability
---

# Dynamic Tool Selection & Auto-Installation

Wren has a **Dynamic Tool Registry** that can automatically detect
missing capabilities, search for open-source tools, and install them
as skills or MCP servers.

## How it works

1. When you need a capability that isn't available locally, the Tool
   Registry checks its inventory of installed skills and MCP servers.
2. If the capability is missing, it uses web search to find open-source
   tools (MCP servers, CLI tools, libraries) that provide it.
3. The best-matching tool is automatically installed as a skill file
   in `~/.wren/microagents/`, with optional MCP server registration.

## REST API Endpoints

Use these endpoints to manage tools dynamically:

### Check Inventory
```
GET /api/v1/tool-registry/inventory
```
Returns all installed capabilities, skills, and MCP servers.

### Ensure Capabilities
```
POST /api/v1/tool-registry/ensure
{
  "capabilities": ["postgres", "docker", "kubernetes"],
  "auto_install": true
}
```
Checks if capabilities exist, scrapes web for missing ones, installs them.

### Analyze Task
```
POST /api/v1/tool-registry/analyze
{
  "task": "I need to deploy a PostgreSQL database with Docker",
  "auto_install": true
}
```
Extracts capability keywords from a task description and ensures tools exist.

### Install MCP Server
```
POST /api/v1/tool-registry/install-mcp
{
  "name": "postgres",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-postgres"]
}
```
Registers an MCP stdio server as an installable skill.

### Install Custom Skill
```
POST /api/v1/tool-registry/install-skill
{
  "name": "my-skill",
  "content": "---\nname: my-skill\ntype: knowledge\n---\n# My Skill\n..."
}
```
Installs a custom skill from markdown content.

### Browse Marketplace
```
GET /api/v1/tool-registry/marketplace
```
Lists well-known installable MCP servers.

### Uninstall Skill
```
DELETE /api/v1/tool-registry/skills/{name}
```

## Trigger Keywords

The dynamic tool selection is triggered when:
- A tool or capability is not found locally
- A task mentions specific technologies (docker, k8s, postgres, etc.)
- The agent encounters an "unknown tool" or "command not found" error
- A user explicitly asks to install or discover tools

## Auto-Generated Skills

When a tool is discovered and installed, a skill file is auto-generated
with:
- YAML frontmatter including name, triggers, and MCP server config
- Description of what the tool does
- Installation and usage instructions
- Links to the source repository
