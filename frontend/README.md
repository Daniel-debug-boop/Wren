<div align="center">
  <br/>
  <h1 align="center" style="margin: 0; font-size: 2rem; letter-spacing: -0.02em;">
    Wren · Frontend
  </h1>
  <p align="center" style="font-size: 1.05rem; color: #666; max-width: 500px; margin: 8px auto;">
    A premium browser-based AI coding workspace.<br/>
    Chat, code, review, and debug — all from one interface.
  </p>
  <br/>
</div>

---

## Overview

The Wren frontend is a **React Single Page Application** that delivers a full-featured AI coding environment in the browser. It combines a conversational chat interface with a built-in IDE workspace, code review tools, debugger, terminal emulator, and chain-of-thought transparency — all powered by WebSocket-driven agent communication.

Built with React 19, TypeScript, Tailwind CSS, and Monaco Editor, it's designed for speed, extensibility, and a premium user experience.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Framework** | React 19.2 · React Router 7 (SPA Mode) |
| **Language** | TypeScript (strict) |
| **Styling** | Tailwind CSS 4 · CSS custom properties (`tokens.css`) |
| **State** | Zustand 5 · React Context · TanStack Query 5 |
| **Animation** | Framer Motion 12 |
| **Editor** | Monaco Editor 0.55 (`@monaco-editor/react`) |
| **Terminal** | xterm.js 6 |
| **Icons** | Lucide React |
| **WebSocket** | Native WebSocket API |
| **i18n** | i18next 25 · react-i18next 16 |
| **Testing** | Vitest · React Testing Library · MSW |
| **Build** | Vite 6 · `@react-router/dev` |

---

## Getting Started

### Prerequisites

- **Node.js** 22.12.x or later
- **npm**, **bun**, or any compatible package manager

### Installation

```bash
cd wren/frontend
npm install
```

### Development

```bash
# Start with mock backend (MSW)
npm run dev:mock

# Start with real backend
npm run dev

# Start with SaaS mock
npm run dev:mock:saas
```

The application runs on **`http://localhost:3001`** by default. Set `VITE_FRONTEND_PORT` to change the port.

### Production Build

```bash
npm run build
```

Output is written to `build/client/` — a static SPA ready to serve behind any web server.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_BACKEND_HOST` | `127.0.0.1:3000` | Backend API host and port |
| `VITE_BACKEND_BASE_URL` | `localhost:3000` | Backend host for WebSocket connections |
| `VITE_USE_TLS` | `false` | Enable HTTPS/WSS for API and WebSocket |
| `VITE_FRONTEND_PORT` | `3001` | Frontend dev server port |
| `VITE_INSECURE_SKIP_VERIFY` | `false` | Skip TLS certificate verification |
| `VITE_MOCK_API` | `false` | Enable MSW API mocking |
| `VITE_MOCK_SAAS` | `false` | Simulate SaaS mode in development |

Copy `.env.sample` to `.env` and adjust as needed.

---

## Project Structure

```
frontend/
├── __tests__/              # Vitest test suite
│   ├── components/         # Component tests
│   └── e2e/                # Playwright E2E tests
├── public/                 # Static assets (favicon, icons, MSW)
├── src/
│   ├── api/                # Data access layer (REST clients)
│   │   ├── conversation-service/
│   │   ├── settings-service/
│   │   ├── api-keys-service/
│   │   └── orchestration-service/
│   ├── components/         # React components by domain
│   │   ├── conversation/   # Chat bubbles, input actions
│   │   ├── ide/            # Monaco editor, file tree, terminal
│   │   ├── layout/         # Shell, sidebar, artifacts drawer
│   │   └── ui/             # Shared primitives (buttons, cards, timeline)
│   ├── hooks/              # Custom React hooks
│   │   ├── query/          # TanStack Query hooks
│   │   ├── mutation/       # TanStack Mutation hooks
│   │   └── use-conversation-websocket.ts
│   ├── routes/             # Page components (file-based routing)
│   ├── types/              # TypeScript type definitions
│   ├── utils/              # Helpers, verified models, theme
│   ├── i18n/               # Internationalization (JSON)
│   ├── root.tsx            # App entry point
│   ├── routes.ts           # Route configuration
│   └── index.css           # Global styles + Tailwind
├── tokens.css              # Design token definitions
├── tsconfig.json
├── vite.config.ts          # Vite + React Router plugin + Vitest config
└── playwright.config.ts    # Playwright E2E test configuration
```

### Component Organization

Components are organized by **domain** and **reusability**:

```
components/
├── conversation/     # Chat-specific (MessageBubble, InputActionButton)
├── ide/              # IDE workspace (MonacoEditor, FileTree, Terminal)
├── layout/           # App shell (Sidebar, TopBar, ArtifactsDrawer, DesktopShell)
└── ui/               # Shared primitives (Button, Card, AgentTimeline, ThinkingPanel)
```

---

## Features

### 💬 Conversational Coding
- Multi-turn chat with AI agents
- Automatic mode detection and suggestion
- Real-time WebSocket streaming
- Rich message rendering (mode badges, action tags, loading states)
- **Chain-of-Thought panel** — transparent agent reasoning display

### 🖥️ IDE Workspace (Code / Vibe Code Modes)
- **Monaco Editor** — Full code editor with syntax highlighting, multi-cursor, bracket matching
- **Inline Completions** — Ghost text suggestions with Tab-to-accept
- **File Tree** — Live workspace explorer
- **Terminal** — Interactive terminal emulator with command history
- **Agent Timeline** — Event log of agent actions

### 📋 Plan → Code → Review → Debug
- **Plan Mode** — Structured execution plans with approve/reject
- **Review Mode** — Diff scanning, inline comments, batch approval
- **Debug Mode** — Stack trace viewer, error analysis, fix suggestions
- **Autonomous Mode** — Self-driving agent execution without approval

### 🧩 Artifacts Drawer
- Code snippets, diffs, terminal output, and HTML previews
- Auto-opens when agent produces output
- Tabbed interface with line counts

### 🧠 Thinking Panel
- Real-time Chain-of-Thought transparency
- Auto-expanding reasoning steps
- Timestamps, duration tracking, auto-scroll
- Categorizes thoughts: reasoning, observation, decision, tool call, error

---

## Data Flow

```
User Input → Chat Textarea
    ↓
sendMessage() → REST API (POST /api/conversations/:id/messages)
    ↓
WebSocket ← Agent Server streams events
    ↓
Event Router → onMessage → MessageBubble
             → onTimelineEvent → AgentTimeline
             → onThinkingStep → ThinkingPanel
             → onTerminalLine → Terminal
             → onWorkspaceFile → FileTree
             → onArtifactsCode → ArtifactsDrawer
```

All agent communication flows through a single WebSocket connection managed by `useConversationWebSocket` hook. The hook parses incoming events (messages, actions, observations, errors, status) and dispatches to registered handlers.

---

## Testing

### Unit Tests (Vitest + React Testing Library)

```bash
# Run all tests
npm run test

# Run with coverage
npm run test:coverage

# Run specific test
npm run test -- -t "ComponentName"
```

### E2E Tests (Playwright)

```bash
npx playwright test
```

### Best Practices

1. **Component tests** — Use `renderWithProviders()` from `test-utils.tsx` for consistent provider wrapping
2. **Mock API calls** — Use MSW handlers for backend-dependent tests
3. **User interactions** — Use `@testing-library/user-event` for realistic simulation
4. **Test IDs** — Add `data-testid` attributes sparingly for hard-to-query elements
5. **Coverage** — Focus on critical flows: conversation, mode switching, WebSocket events

---

## Routing

Routes are defined in `src/routes.ts` using React Router's file-based system:

| Route | Page | Purpose |
|-------|------|---------|
| `/` | `home.tsx` | Landing page with suggested tasks |
| `/conversations/new` | `new-conversation.tsx` | Start a new conversation |
| `/conversations/:id` | `conversation.tsx` | Main chat/IDE workspace |
| `/settings` | `settings.tsx` | LLM config, preferences |
| `/settings/integrations` | integrations page | Git provider setup |
| `/api-keys` | `api-keys.tsx` | API key management |
| `/orchestration` | `orchestration.tsx` | Autonomous orchestrator UI |
| `/modes` | `modes.tsx` | Mode configuration |
| `/login` | `login.tsx` | Authentication |
| `/onboarding` | `onboarding.tsx` | First-run setup |

Each route is automatically code-split at build time by the React Router Vite plugin.

---

## State Management

| Concern | Solution |
|---------|----------|
| **Server state** | TanStack Query (cache, refetch, mutations) |
| **UI state** | React Context (Mode, Artifacts, AgentStatus) |
| **WebSocket state** | Hook-local refs + useState callbacks |
| **Persistent state** | localStorage (mode preference, auth token) |

---

## Internationalization

```bash
# Generate i18n declaration file
npm run make-i18n

# Translation files
src/i18n/translation.json
```

The app uses `i18next` with `react-i18next`. New UI strings should be added to the translation files and referenced via `useTranslation()` or the `t()` function.

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) and [Development.md](../Development.md) for detailed guidelines.

Key checks before submitting:
```bash
npm run lint:fix       # Fix auto-fixable lint issues
npx tsc --noEmit       # TypeScript type check
npm run build          # Production build
npm run test           # Test suite
```
