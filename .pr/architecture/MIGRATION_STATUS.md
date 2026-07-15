# Server Migration Status: `wren/server/` → `wren/app_server/`

## Summary

The `wren/server/` directory is **fully deprecated** in favor of `wren/app_server/`. All modules explicitly emit `DeprecationWarning` on import. The migration is complete from a functionality standpoint, but cleanup remains.

## Status Per Module

| Module | Status | Active? | Notes |
|--------|--------|---------|-------|
| `wren/server/__main__.py` | 🟢 Deprecated | No | Points to `wren.server.listen:app`; comment says to use `uvicorn wren.app_server.app:app` instead |
| `wren/server/app.py` | 🟢 Deprecated | No | Re-exports from `wren.app_server.app` |
| `wren/server/listen.py` | 🟢 Deprecated | No | Re-exports from `wren.app_server.app` |
| `wren/server/middleware.py` | 🟢 Deprecated | No | Re-exports from `wren.app_server.middleware` |
| `wren/server/static.py` | 🟢 Deprecated | No | Re-exports from `wren.app_server.static` |
| `wren/server/shared.py` | 🟢 Deprecated | No | Legacy global singletons pattern |
| `wren/server/types.py` | 🟢 Deprecated | No | Legacy type definitions |
| `wren/server/config/server_config.py` | 🟢 Deprecated | No | Legacy server config |
| `wren/server/orchestrator.py` | 🟡 Keep | Partial | `ParallelAgentOrchestrator` is used by `scripts/run_parallel_agents.py`. Not the same as `wren.harness.MetaOrchestrator`. Contains ~1200 lines of legacy code. |
| `wren/server/conversation_agent.py` | 🟡 Keep | Partial | `ConversationAgentAdapter` bridges old orchestrator with new `LiveStatusAppConversationService`. Used by the old orchestrator. |
| `wren/server/memory/fable_memory.py` | 🟢 Deprecated | No | Legacy memory implementation |

## Architecture Details

### Active Application (`wren/app_server/`)

The current active server is built on:

```
wren.app_server.app:app
  ├── V1 Router (/api/v1)
  │   ├── app_conversation_router (conversation lifecycle)
  │   ├── event_router (event storage/streaming)
  │   ├── sandbox_router (sandbox management)
  │   ├── settings_router (user/app settings)
  │   ├── secrets_router (secrets management)
  │   ├── user_router (user management)
  │   ├── git_router (git integration)
  │   └── ... 8 more routers
  ├── Health routes
  ├── Orchestration routes (/api/orchestration)
  ├── Harness routes (/api/harness)
  ├── Intent router (/api/intent)
  ├── Skill synthesis routes
  ├── MCP server (mounted at /mcp)
  └── SPA static file serving
```

### Legacy Orchestrator (`wren/server/orchestrator.py`)

The `ParallelAgentOrchestrator` is a **separate system** from `wren.harness.MetaOrchestrator`:
- `ParallelAgentOrchestrator`: Task-based parallel execution with `TaskSpec`, `TaskHandle`, tenant quotas, retry loops
- `MetaOrchestrator` (v2): Goal-decomposition-based execution with child agents, task graphs, circuit breakers, message bus

Both coexist because they serve different use cases. The old orchestrator is used only by `scripts/run_parallel_agents.py`.

## Recommended Actions

### Priority 1 — Remove dead re-exports (safe)
Files that purely re-export from `wren/app_server/`:
- `wren/server/app.py`
- `wren/server/listen.py`
- `wren/server/middleware.py`
- `wren/server/static.py`
- `wren/server/shared.py`
- `wren/server/types.py`
- `wren/server/config/server_config.py`

These can be removed when the next major version is released, provided no external code imports them.

### Priority 2 — Consolidate orchestrators
The `wren/server/orchestrator.py` `ParallelAgentOrchestrator` should either be:
1. Moved to `scripts/` alongside `run_parallel_agents.py`
2. Or merged into `wren/harness/` as a parallel-mode execution path

### Priority 3 — Remove dead memory module
`wren/server/memory/fable_memory.py` is unused by any active code path.

## References

- V1 router assembly: `wren/app_server/v1_router.py`
- App entry point: `wren/app_server/app.py`
- App config factory: `wren/app_server/config.py`
- Config doc: `wren/app_server/README.md`
- New harness orchestrator: `wren/harness/meta_orchestrator.py`
