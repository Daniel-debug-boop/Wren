# Dynamic Tool Selection + Manager Orchestration

## What Wren Can Now Do (Honest)

### Auto-Enforced (No Agent Choice)
| Feature | Enforced By | How |
|---|---|---|
| **Filesystem MCP server** | `skills/default-tools.md` | Loaded every agent start via `uvx @modelcontextprotocol/server-filesystem /workspace` |
| **Goal detection → manager mode** | `GoalDetector` in `_build_start_conversation_request_for_user()` | Pre-processes initial message for complex-project keywords (patterns + tech triggers). If score ≥3, injects manager-mode system instruction into agent context. **Agent cannot skip this** — it's in the system prompt before the agent starts. |
| **Working memory auto-population** | `WorkingMemoryProcessor` (EventCallbackProcessor) | Registered on every conversation start. Listens to ALL events: auto-records agent thoughts as decisions/progress, errors as error entries, status transitions as progress. |
| **Auto-reflection on terminal state** | `ReflectionProcessor` (EventCallbackProcessor) | Registered on every conversation start. When conversation reaches ERROR/COMPLETED/STOPPED, reads working memory, extracts lessons, stores in FableMemory. Cross-session learning. |
| **Background tool check** | `asyncio.ensure_future` in `_load_skills_and_update_agent()` | Async task logs missing capabilities at startup. Non-blocking. |

### Agent-Guided (Skill Instructions, Agent Must Follow)
| Feature | How Triggered | Reliance |
|---|---|---|
| Sub-agent delegation | `manager-agent.md` skill triggers on "/manager", "massive project", etc. | Skill content says "use task() sub-agent". Agent decides. |
| Self-reflection per sub-task | Same skill | Skill says "reflect after each sub-task". Agent decides. |
| Tool registry API calls | `dynamic-tool-selection.md` skill | Skill says "POST /api/v1/tool-registry/analyze". Agent decides. |

### REST API (Available for Manual/Agent Use)
| Endpoint | Purpose |
|---|---|
| `POST/GET/DELETE /api/orchestration/memory/*` | Working memory CRUD |
| `POST /api/orchestration/manager/init` | Start project goal |
| `POST /api/orchestration/manager/decompose` | Register sub-tasks |
| `POST /api/orchestration/manager/finalize` | Finalize + reflect |
| `POST /api/orchestration/reflect` | One-shot reflection |
| `GET /api/orchestration/lessons` | Recent learnings |
| `GET/POST /api/v1/tool-registry/*` | Tool discovery/install |

### Files Created
```
wren/app_server/orchestration/
├── __init__.py              — Package exports
├── manager.py               — ManagerAgent: decompose, delegate, track
├── working_memory.py         — JSON-backed session memory
├── self_memory_loop.py       — Reflection + FableMemory integration
├── goal_detector.py          — Pre-start goal analysis + auto-decomposition
├── hooks.py                  — EventCallbackProcessors (auto WM + reflection)
└── router.py                 — REST endpoints

skills/
├── manager-agent.md          — Manager mode skill instructions
└── dynamic-tool-selection.md — Tool registry skill instructions
```

### Files Modified
```
skills/default-tools.md                          — +filesystem MCP server
wren/app_server/v1_router.py                — +orchestration router
wren/app_server/app_conversation/            — goal detector + processors
  live_status_app_conversation_service.py          in request builder
wren/app_server/app_conversation/            — background tool check
  app_conversation_service_base.py
```

### Gap Status
| Gap | Status |
|---|---|
| Agent doesn't respect skill triggers | **FIXED** — goal detector injects context pre-start |
| No auto working memory | **FIXED** — WorkingMemoryProcessor on every event |
| No auto reflection | **FIXED** — ReflectionProcessor on terminal state |
| No sub-agent spawning from code | **PARTIAL** — REST API + skill instructions available. True sub-conversation spawning requires SDK agent-server changes (external package). |
| Background tool check is passive | **FIXED** — runs async on every agent init, logs missing capabilities |
