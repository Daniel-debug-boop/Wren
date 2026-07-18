---
name: chrome-devtools
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - browser
  - chrome
  - screenshot
  - dom
  - css
  - inspect
  - visualize
  - render
  - webpage
  - website
---

# Chrome DevTools MCP - Visual Intelligence

This skill provides deep browser integration via Chrome DevTools Protocol.
The chrome-devtools-mcp server is always running in the background.

## Available Tools

### Navigation & Screenshots
- `chrome_navigate` - Navigate to a URL
- `chrome_screenshot` - Take a screenshot of the current page
- `chrome_get_styles` - Get computed styles for an element

### DOM Inspection
- `chrome_snapshot` - Get accessibility tree (a11y) of the page
- `chrome_evaluate` - Evaluate JavaScript in the page context
- `chrome_select` - Select an element using CSS selector

### Interaction
- `chrome_click` - Click an element (by selector or coordinates)
- `chrome_fill` - Fill a form field
- `chrome_press` - Press a keyboard key
- `chrome_hover` - Hover over an element

### Network & Performance
- `chrome_network_requests` - List network requests
- `chrome_performance_metrics` - Get performance metrics

## Usage Patterns

### 1. Visual Verification
After making UI changes, take a screenshot to verify:
```
chrome_screenshot → verify visual output
```

### 2. DOM Analysis
Inspect page structure for debugging:
```
chrome_snapshot → get a11y tree → find elements
chrome_get_styles → check CSS properties
```

### 3. Form Testing
Test form interactions:
```
chrome_fill → fill input field
chrome_click → submit button
chrome_screenshot → verify result
```

### 4. Performance Analysis
Check page performance:
```
chrome_performance_metrics → get Core Web Vitals
chrome_network_requests → check resource loading
```

## Best Practices

1. **Take screenshots frequently** - Visual verification is key
2. **Use a11y tree** - More reliable than CSS selectors for finding elements
3. **Check computed styles** - Understand why elements look a certain way
4. **Monitor network** - Debug loading issues
5. **Use headless mode** - Server runs in headless by default

## Common Workflows

### Bug Investigation
1. Navigate to the page
2. Take screenshot to see current state
3. Get a11y tree to understand structure
4. Check console for errors
5. Inspect network requests

### UI Testing
1. Navigate to the feature
2. Interact with elements (click, fill)
3. Take screenshots at each step
4. Verify expected state

### Performance Audit
1. Navigate to the page
2. Get performance metrics
3. Check network requests
4. Identify bottlenecks
