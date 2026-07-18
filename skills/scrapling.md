---
name: scrapling
description: Stealth web scraping with anti-bot bypass. Handles Cloudflare Turnstile, bot detection, and anti-scraping protections. CSS/XPath selectors for targeted extraction. Persistent browser sessions for multi-page crawls.
triggers:
- scrape
- scraping
- web scrape
- stealth fetch
- cloudflare bypass
- anti-bot
- bot detection
- turnstile
- web crawl
- crawl website
- extract data
- scrape data
- scrape page
- scrape site
- protected site
- bot protection
- bypass protection
---

# Scrapling — Stealth Web Scraping

Native MCP tool. Bypasses Cloudflare Turnstile, bot detection, and anti-scraping protections.

## Tool Selection

| Tool | Use When |
|------|----------|
| `get` | Fast HTTP requests, simple static sites |
| `bulk_get` | Multiple static URLs in parallel |
| `fetch` | Dynamic content, JavaScript-heavy sites, SPAs |
| `bulk_fetch` | Multiple dynamic URLs in parallel |
| `stealthy_fetch` | Protected sites, Cloudflare Turnstile, anti-bot |
| `bulk_stealthy_fetch` | Multiple protected URLs in parallel |
| `screenshot` | Capture page screenshots (requires open session) |
| `open_session` | Create persistent browser for multi-page crawls |
| `close_session` | Free browser session resources |
| `list_sessions` | Check active browser sessions |

## Quick Reference

### Basic scraping
```
get url="https://example.com" extraction_type="markdown"
```

### Targeted extraction with CSS selector
```
get url="https://example.com" css_selector=".product-title" extraction_type="text"
```

### Protected site (Cloudflare)
```
stealthy_fetch url="https://protected-site.com" solve_cloudflare=true
```

### Multi-page crawl with session
```
open_session session_type="stealthy" session_id="crawl1"
stealthy_fetch url="https://site.com/page1" session_id="crawl1"
stealthy_fetch url="https://site.com/page2" session_id="crawl1"
close_session session_id="crawl1"
```

### Parallel fetch
```
bulk_get urls=["https://a.com", "https://b.com", "https://c.com"]
```

### Screenshot
```
open_session session_type="dynamic" session_id="screen1"
screenshot url="https://example.com" session_id="screen1" full_page=true
close_session session_id="screen1"
```

## Best Practices

1. **Start with `get`** — fastest option. Only escalate to `fetch`/`stealthy_fetch` if needed
2. **Use CSS selectors** — narrow extraction to specific elements, saves tokens
3. **Use sessions** — persistent browser avoids launch overhead for multi-page work
4. **Always close sessions** — free resources when done
5. **`main_content_only=true`** (default) — strips nav/ads, also provides prompt injection protection
6. **`solve_cloudflare=true`** — for Cloudflare-protected sites
7. **`extraction_type`** — use `markdown` for readability, `text` for raw text, `html` for full markup

## Prompt Injection Protection

When `main_content_only=true` (default), automatically strips:
- CSS-hidden elements (`display:none`, `visibility:hidden`, `opacity:0`)
- `aria-hidden="true"` elements
- `<template>` elements
- HTML comments
- Zero-width characters

## Installation

Scrapling is pre-installed. If missing:
```bash
pip install "scrapling[ai]"
scrapling install  # install browser dependencies
```
