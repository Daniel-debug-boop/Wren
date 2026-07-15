# Wren Design System — Premium Dark-Tech GUI

## Identity
- **Vibe**: Developer-tool SaaS, premium dark-first, editorial clarity
- **Archetype**: Dark Tech + Editorial Minimal hybrid
- **Tone**: Confident, warm, precise — not sterile, not corporate

## Typography
| Role | Font | Weight | Notes |
|---|---|---|---|
| Display/Headings | `Geist` (variable) | 600–700 | Tight tracking `-0.03em` |
| Body UI | `Geist` (variable) | 400–500 | `-0.01em` tracking |
| Mono/Code | `Geist Mono` (variable) | 400–500 | Must match line height |
| Hero/CTA Large | `Geist` 800 | | Letter-spacing `-0.04em` |

**Banned**: Inter, Roboto, Arial, Helvetica, Open Sans, system-ui fallback only for missing glyphs.

## Color Palette
```
--surface-base:  #0c0e12     (deep charcoal, not pure #000)
--surface-raised: #14161b    (cards, panels)
--surface-overlay: #1c1f26   (hovered cards, dropdowns)
--surface-glass: rgba(20,22,27,0.75)  (glass-morphism)
--border-subtle: rgba(255,255,255,0.06)
--border: rgba(255,255,255,0.10)
--border-strong: rgba(255,255,255,0.18)
--text-primary: #f0f2f5
--text-secondary: #a0a5b0
--text-tertiary: #6b7080
--accent: #c9b974           (gold — kept from existing brand)
--accent-soft: rgba(201,185,116,0.15)
--accent-glow: rgba(201,185,116,0.08)
--danger: #e76a5e
--success: #5ee7a5
--info: #5ea5e7
```

## Layout
- **Sidebar**: 64px wide, vertical, glass-morphism. Logo top, nav middle, user bottom. Hover expands tooltips.
- **Content**: Full-height scrollable container. Max-width 1200px on conversation pages.
- **Settings**: Left nav (220px) + right content area with max-width 800px.
- **Spacing**: 4px base unit. Cards use 16-24px padding. Section spacing 32-48px.

## Components

### GlassCard
- `bg-surface-glass backdrop-blur-xl border border-border-subtle rounded-xl`
- Optional: `shadow-accent-glow` on hover

### PremiumButton
- Primary: `bg-accent text-black font-medium hover:brightness-110 transition-all`
- Secondary: `border-border text-text-primary hover:bg-surface-overlay`
- Ghost: `text-text-secondary hover:text-text-primary`

### Input
- `bg-surface-raised border-border text-text-primary rounded-lg px-4 py-2.5`
- Focus: `ring-1 ring-accent/30 border-accent/50`

### Chat Bubble
- User: `bg-accent/10 border border-accent/20 text-text-primary`
- Agent: `bg-surface-raised border-border-subtle`
- System: `bg-surface-glass text-text-secondary text-sm`

## Motion
- Duration: `150ms` (micro), `300ms` (standard), `500ms` (enter/exit)
- Easing: `cubic-bezier(0.16, 1, 0.3, 1)` — custom spring-like
- Page transitions: fade + slide-up
- Sidebar: width animation on hover
- Chat messages: fadeIn + slideUp on appearance

## Glass Effects
- Sidebar uses `backdrop-blur-xl` with `bg-black/30`
- Modals use `backdrop-blur-sm` with `bg-black/50`
- Cards use `bg-white/[0.03]` with `backdrop-blur-lg`

## Icon Set
- Use `react-icons/pi` (Phosphor Light) for UI navigation
- Use `react-icons/lu` for action items
- **Banned**: lucide-react (except for backward compat)

## Page Layouts

### Home
- Full-bleed dark background with subtle grid pattern
- Center-aligned hero: logo + tagline + CTA
- Two-column below: new conversation input + recent conversations
- Bottom row: task suggestions by repo

### Conversation
- Top bar: conversation name + status pill + tab selector
- Chat area: full-height scrollable, bubbles aligned left (agent) / right (user)
- Input bar: fixed bottom, glass-morphism with file attach and send
- Right panel (toggleable): tabs for Planner, Code, Terminal, Browser

### Settings
- Left: nav items with icons, active state has accent left border
- Right: scrollable content area
- Sections separated by subtle dividers
