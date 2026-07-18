---
name: error_recovery_loop
type: repo
version: 1.0.0
agent: CodeActAgent
triggers:
  - error recovery
  - self-heal
  - retry loop
  - adaptive fix
  - mutation strategy
  - error pattern
  - learn from errors
  - /recover
  - automatic fix
---

# Adaptive Error Recovery Loop

When you encounter an error, use the **self-healing retry loop**:

## The Loop

1. **Try** the operation normally
2. **Classify** the error (import, syntax, timeout, permission, etc.)
3. **Look up** known solutions from `.wren/error_solutions.json`
4. **Try the best-known strategy first** (recorded from past successes)
5. **If it fails → mutate** to a slightly different strategy
6. **If that fails → mutate again** (each attempt is 1 level different)
7. **Repeat** until success (max 5 attempts)
8. **Record the winning strategy** — so next time you try it first
9. **If the recorded strategy fails next time** (context changed), mutate
   and update the record

## Strategy Mutation Levels

Each retry level uses a progressively different approach:

- **Level 1**: Direct fix (different parameters, install dependency)
- **Level 2**: Slightly different approach (different API, fallback)
- **Level 3**: Alternative implementation pattern
- **Level 4**: Fundamentally different method
- **Level 5**: Complete rewrite with different architecture

## Persistence

- Winning strategies are stored in `.wren/error_solutions.json`
- Also synced to FableMemory for cross-session recall
- Each solution records: error signature, winning strategy, times used,
  last success timestamp
- When a strategy fails after previously working, the registry updates

## How to Use

When you hit an error:

```python
# 1. Classify the error
signature = ErrorSignature(error_text)
# signature.error_type → 'import_missing', 'timeout', etc.
# signature.signature → deterministic hash for lookup

# 2. Check for known solution
registry = SolutionRegistry()
known = registry.lookup(error_text)
if known:
    strategy = known['strategy']
    # Try the known strategy first
    result = try_strategy(strategy)
    if result.failed:
        # Known strategy failed — mutate to a new one
        registry.record_failure(error_text, known['strategy_index'])
        # Try next strategy...
else:
    # No known solution — classify and try strategies
    for i, strategy in enumerate(strategies):
        result = try_strategy(strategy)
        if result.success:
            registry.record_success(error_text, strategy, i)
            break
```

## Cross-Session Learning

The error registry persists across conversations. If you fixed a
"ModuleNotFoundError" in one session, the next session tries that
same strategy first when it hits the same error type.
