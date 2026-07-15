# Changelog

All notable changes to Wren will be documented in this file.

## [0.2.0] - 2026-07-11

### Fixed
- CircuitBreaker `T` undefined reference in `meta_orchestrator.py` — telemetry import moved inside `call()` to avoid NameError at runtime
- `analyze_screenshot` endpoint using `__wrapped__` bypass — now saves uploaded image to temp file and calls `analyze_screenshot(Path)` properly
- `InMemoryRateLimiter` using naive `datetime.now()` — switched to timezone-aware `datetime.now(timezone.utc)` for correct cross-worker behavior

### Changed
- Deprecated `wren.server.app`, `wren.server.middleware`, `wren.server.listen`, `wren.server.types` re-exports now emit `DeprecationWarning` at import time
- Updated all internal importers (`wren.analytics`, `tests`, `enterprise`, `scripts`) to import directly from `wren.app_server`
- CORS middleware warning strengthened with explicit "SECURITY RISK" message for production
- Legacy env var fallbacks (`RUNTIME`, `SANDBOX_HOST_PORT`, `SANDBOX_CONTAINER_URL_PATTERN`) now emit `DeprecationWarning`

### Added
- 14 unit tests for middleware: `CacheControlMiddleware`, `InMemoryRateLimiter`, `RateLimitMiddleware`, `LocalhostCORSMiddleware`

## [0.1.0] - 2025-07-04

### Added
- Wren branding (renamed from OpenHands)
- AI-generated wren bird logo (amber on dark charcoal)
- 6 native MCP servers: fetch, filesystem, chrome-devtools, scrapling, ponytail, nano-banana
- 12 knowledge skills: chrome-devtools, scrapling, penpot, vibesec, ponytail, nano-banana, skill-triggering, copyright-compliance, file-creation, refusal-handling, tone-formatting, product-guardrails
- `oh` CLI v0.2.0 with `oh doctor`, `oh health`, first-run welcome
- Intent understanding system (psychology-first approach)
- Self-teaching skill synthesis
- Design analyzer (CSS/image analysis)
- Token cost tracker
- Theme system (dark/light/system)
- 113 unit tests

### Changed
- Frontend title: "Wren"
- CLI description: "Wren — AI software engineer"
- All user-facing text: OpenHands → Wren
- Translation strings: 1136 occurrences replaced

### Removed
- Tauri desktop app (wrong approach)
- Old OpenHands placeholder logos
