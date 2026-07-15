---
name: file-creation
description: Rules for when to create files vs inline responses. Clear triggers for output format.
triggers:
  - create file
  - write file
  - save file
  - output format
  - inline response
---

# File Creation Triggers

## Purpose
Determine when to create files vs respond inline based on content type and user intent.

## Decision Matrix

### CREATE FILES when:

| Trigger | Example |
|---------|---------|
| >10 lines of code | Any script/module/component |
| Blog post/article | "write a blog post about..." |
| Documentation | "create docs for..." |
| Configuration file | "create a config for..." |
| Script | "write a script that..." |
| Component | "build a React component..." |
| Module | "create a module for..." |
| Report | "generate a report on..." |
| Test file | "write tests for..." |

### RESPOND INLINE when:

| Trigger | Example |
|---------|---------|
| Simple explanation | "what is a closure?" |
| Quick answer | "how do I center a div?" |
| Code snippet <10 lines | "show me a for loop" |
| Conceptual question | "explain recursion" |
| Opinion/recommendation | "which framework is best?" |
| Debugging help | "why is this error?" |

## Rules

### 1. Code Files
```python
# >10 lines → Create file
# <=10 lines → Inline
```

### 2. Documentation
```markdown
# "write docs" → Create file
# "explain this" → Inline
```

### 3. Creative Content
```markdown
# Blog post → Create file
# Quick thought → Inline
```

### 4. Configuration
```yaml
# Config file → Always create file
# Config explanation → Inline
```

## File Naming

When creating files:
- Use descriptive names: `auth-middleware.js` not `temp.js`
- Use appropriate extensions: `.py`, `.js`, `.tsx`, `.md`
- Place in logical location based on project structure

## Examples

| User Request | Response Type | Reason |
|--------------|---------------|--------|
| "Write a Python function to sort a list" | Inline (5 lines) | Simple, under 10 lines |
| "Create a REST API in Flask" | File | Multiple endpoints, >10 lines |
| "What is Docker?" | Inline | Conceptual question |
| "Write a Dockerfile for Node.js" | File | Configuration file |
| "Explain this error" | Inline | Debugging help |
| "Create a React component" | File | Component creation |
| "How do I use useEffect?" | Inline | Quick explanation |
| "Write a test suite" | File | Multiple tests, >10 lines |

## Best Practices
- When in doubt, create a file (users can always copy content)
- Always explain what you're creating and why
- Offer to adjust format if user prefers different output