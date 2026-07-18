# Skills & MCP Tools Reference

Wren ships with 44+ skills and 5 native MCP servers.

## MCP Servers (Auto-Booted)

| Server | Purpose | Tools |
|--------|---------|-------|
| `fetch` | HTTP requests | `fetch` |
| `filesystem` | File operations | `read_file`, `write_file`, `list_dir` |
| `chrome-devtools` | Browser automation | `take_snapshot`, `navigate`, `click`, `type` |
| `scrapling` | Anti-bot scraping | `get`, `fetch`, `stealthy_fetch`, `screenshot`, `open_session` |
| `ponytail` | Lazy senior dev patterns |
| `nano-banana` | Image generation (Gemini) | YAGNI ladder, scope discipline |

All MCP servers are native — no user configuration required.

## Skills (Trigger-Activated)

### Security
| Skill | Triggers | Purpose |
|-------|----------|---------|
| `vibesec` | `security`, `injection`, `xss`, `auth` | Security rules |
| `cso` | `security audit`, `pentest` | Infrastructure security |

### Product
| Skill | Triggers | Purpose |
|-------|----------|---------|
| `product-guardrails` | `build`, `wrap`, `desktop`, `our own` | Auto-challenge bad product decisions |
| `ponytail` | `yagni`, `scope`, `less code` | Lazy senior dev philosophy |

### Design
| Skill | Triggers | Purpose |
|-------|----------|---------|
| `emil-design-eng` | `design quality`, `polish`, `animation` | Design philosophy |
| `animation-vocabulary` | `animation`, `easing`, `spring` | 50+ animation terms |
| `review-animations` | `review animation`, `animation quality` | 10 non-negotiable standards |
| `penpot` | `penpot`, `design tokens`, `design system` | Design platform |

### Scraping
| Skill | Triggers | Purpose |
|-------|----------|---------|
| `scrapling` | `scrape`, `cloudflare bypass`, `stealth` | Anti-bot scraping |

### Image Generation
| Skill | Triggers | Purpose |
|-------|----------|---------|
| `nano-banana` | `generate image`, `draw`, `mockup`, `illustration` | Gemini image gen |

### Behavior Enhancement
| Skill | Triggers | Purpose |
|-------|----------|---------|
| `skill-triggering` | auto | Auto-activate skills |
| `copyright-compliance` | `copyright`, `quote` | Content rules |
| `file-creation` | auto | File vs inline decisions |
| `refusal-handling` | auto | When to refuse |
| `tone-formatting` | auto | Communication style |

### Planning & Review
| Skill | Triggers | Purpose |
|-------|----------|---------|
| `gstack` | `gstack` | Route to right skill |
| `plan-ceo-review` | `think bigger`, `scope` | CEO-mode review |
| `investigate` | `debug`, `fix bug` | Root cause analysis |

## Adding New Skills

1. Create `skills/my-skill.md` with frontmatter:
   ```yaml
   ---
   name: my-skill
   description: What it does
   triggers:
     - keyword1
     - keyword2
   ---
   ```

2. Add content with instructions

3. Auto-registered by ToolInventory scanner

## Adding MCP Servers

1. Add to `skills/default-tools.md`:
   ```yaml
   ## stdio_servers
   - name: my-server
     command: npx
     args:
       - my-mcp-server
   ```

2. Auto-registered by ToolInventory scanner
