---
name: skill-triggering
description: Automatic skill activation based on context matching. Triggers skills when conversation matches trigger keywords or intent.
triggers:
  - skill activation
  - trigger matching
  - context matching
  - automatic loading
---

# Skill Triggering Pattern

## Purpose
Automatically activate relevant skills when conversation context matches trigger conditions.

## How It Works

### 1. Trigger Keywords
Each skill defines trigger keywords in its frontmatter:
```yaml
triggers:
  - keyword1
  - keyword2
  - phrase match
```

### 2. Context Matching
When a user message arrives:
1. Scan all skill trigger lists
2. Match against user message content
3. Load matching skills automatically
4. Present relevant skills to agent

### 3. Priority Levels
- **Exact match** → Load immediately
- **Partial match** → Suggest to agent
- **Intent match** → Load if agent needs it

## Implementation

### For Skills
Add triggers to skill frontmatter:
```yaml
---
name: my-skill
description: What this skill does
triggers:
  - exact phrase
  - keyword1
  - keyword2
---
```

### For Agents
When processing user input:
1. Check trigger keywords against message
2. If match found, load skill automatically
3. Apply skill instructions to current task

## Examples

| User Message | Matching Skill | Trigger |
|--------------|----------------|---------|
| "fix this bug" | investigate | `bug`, `debug`, `error` |
| "review this PR" | review | `review`, `PR`, `diff` |
| "deploy to production" | ship | `deploy`, `ship`, `production` |
| "write tests" | tdd | `test`, `TDD`, `test-first` |
| "let's build a desktop app" | product-guardrails | `build`, `wrapper`, `desktop`, `wrap` |

## Best Practices
- Keep triggers concise (1-3 words each)
- Use synonyms (bug = issue = defect)
- Include both technical and natural language triggers
- Test trigger accuracy regularly