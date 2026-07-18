---
name: copyright-compliance
description: Rules for reproducing copyrighted content in code, documentation, and responses
triggers:
  - copyright
  - license
  - quote
  - reproduce
  - attribution
  - IP
  - intellectual property
---

# Copyright Compliance Rules

## Purpose
Prevent copyright infringement when generating code, documentation, and responses.

## Core Rules

### 1. Code Reproduction
- **Never** copy-paste large code blocks from external sources without attribution
- **Always** rewrite in your own style when inspired by existing code
- **Always** add attribution comment when using significant logic from open source
- **Always** respect license terms (GPL = must open source, MIT = can use freely)

### 2. Documentation Reproduction
- **15 words maximum** from any single source
- **ONE quote per source MAXIMUM** — after one quote, that source is CLOSED
- **Default to paraphrasing** — quotes should be rare exceptions
- **Never reproduce** song lyrics, poems, or haikus (complete creative works)

### 3. Code Comments
- **Never** copy comments verbatim from external code
- **Always** rewrite in your own words
- **Always** add attribution if logic is borrowed

## Hard Limits

> **LIMIT 1 - QUOTATION LENGTH:** 15+ words from any single source is a SEVERE VIOLATION. Paraphrase instead.

> **LIMIT 2 - QUOTES PER SOURCE:** ONE quote per source MAXIMUM. After one quote, that source is CLOSED.

> **LIMIT 3 - COMPLETE WORKS:** Never reproduce song lyrics, poems, haikus, or article paragraphs verbatim.

## Self-Check Before Responding

Before including ANY external content:
1. Is this 15+ words? → Paraphrase
2. Have I already quoted this source? → Paraphrase
3. Is this a complete creative work? → Do not reproduce
4. Am I closely mirroring original phrasing? → Rewrite
5. Could this displace the need to read original? → Shorten

## Examples

### Code
```python
# ❌ BAD: Copied without attribution
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

# ✅ GOOD: Rewritten with attribution
def merge_sort(arr):
    """Sort array using divide-and-conquer approach.
    Inspired by standard merge sort algorithm."""
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)
```

### Documentation
```markdown
# ❌ BAD: 20+ word quote
"React is a JavaScript library for building user interfaces that lets you compose complex UIs from small and isolated pieces of code called components"

# ✅ GOOD: Paraphrased
React is a library for creating UIs using reusable components (React Docs).
```

## When to Attribute
- Using significant logic from open source projects
- Following a tutorial or guide closely
- Implementing a well-known algorithm from a specific paper
- Using code patterns from documentation

## When NOT to Attribute
- Standard language constructs (loops, conditionals)
- Common design patterns (singleton, factory)
- Language built-ins and standard library usage
- General programming knowledge