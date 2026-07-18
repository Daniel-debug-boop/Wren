# Theme System — Dark/Light Mode

Wren supports dark and light themes with system preference detection.

## Usage

1. Open **Settings** → **Application**
2. Toggle between **Dark**, **Light**, and **System** modes
3. Preference persists across sessions (localStorage)

## How It Works

### Theme Architecture

```
Primitive tokens (raw hex values)
    ↓
Semantic tokens (bg-surface-base, text-text-primary)
    ↓
Component tokens (specific component overrides)
```

### Token Categories

| Category | Prefix | Examples |
|----------|--------|----------|
| Surface | `bg-surface-*` | `bg-surface-base`, `bg-surface-secondary` |
| Border | `border-border-*` | `border-border-default`, `border-border-strong` |
| Text | `text-text-*` | `text-text-primary`, `text-text-secondary` |
| Accent | `text-accent-*` | `text-accent-brand`, `text-accent-success` |
| Status | `bg-status-*` | `bg-status-error`, `bg-status-success` |

### Flash Prevention

An inline `<script>` in `root.tsx` applies the theme before React hydrates, preventing a flash of wrong theme.

### System Preference Detection

When set to **System**, the theme follows `prefers-color-scheme` and updates automatically if the OS setting changes.

## For Developers

### Adding New Tokens

1. Add to `frontend/src/tailwind.css` `@theme` block:
   ```css
   --color-my-new-token: #value;
   ```

2. Add light override in `.light` class:
   ```css
   --color-my-new-token: #light-value;
   ```

3. Use in components:
   ```tsx
   <div className="bg-my-new-token">
   ```

### Migrating Hardcoded Colors

Replace:
```tsx
<div style={{ backgroundColor: '#1a1a2e' }}>
```

With:
```tsx
<div className="bg-surface-base">
```

### Brand-Specific Colors

Some colors stay hardcoded (GitHub blue, Microsoft red, Stripe purple) — these are brand identity, not design tokens.
