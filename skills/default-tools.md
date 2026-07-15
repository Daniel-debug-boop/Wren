---
# This is a repo microagent that is always activated
# to include necessary default tools implemented with MCP
name: default-tools
type: repo
version: 1.0.0
agent: CodeActAgent
mcp_tools:
  stdio_servers:
    - name: "fetch"
      command: "uvx"
      args: ["mcp-server-fetch"]
    - name: "filesystem"
      command: "uvx"
      args: ["@modelcontextprotocol/server-filesystem", "/workspace"]
    - name: "chrome-devtools"
      command: "npx"
      args: ["-y", "chrome-devtools-mcp@latest", "--headless", "--isolated"]
    - name: "scrapling"
      command: "scrapling"
      args: ["mcp"]
    - name: "ponytail"
      command: "npx"
      args: ["-y", "@dietrichgebert/ponytail-mcp"]
    - name: "nano-banana"
      command: "npx"
      args: ["-y", "nano-banana-mcp"]
      env:
        GEMINI_API_KEY: "${GEMINI_API_KEY}"
# We leave the body empty because MCP tools will automatically add the
# tool description for LLMs in tool calls, so there's no need to add extra descriptions.
---
