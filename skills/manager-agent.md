---
name: manager_agent
type: repo
version: 1.0.0
agent: CodeActAgent
triggers:
  - massive project
  - large goal
  - sub-agent
  - orchestrate
  - decompose
  - manager mode
  - project breakdown
  - working memory
  - self memory
  - /manager
  - reflection loop
---

# Manager Agent — Sub-Agent Orchestration + Working Memory + Self-Memory Loop

When given a **massive project goal**, you must shift into **manager mode**.

## The Manager Pattern

You are the manager. You do NOT implement everything yourself.
Instead, you decompose the goal into sub-tasks, delegate each to a
sub-agent, track progress in working memory, and learn from outcomes.

### Phase 1: Decompose

1. Read the full project goal
2. Break it into **independent, ordered sub-tasks** (5-15 is ideal)
3. Each sub-task must specify:
   - `name`: short unique label
   - `description`: what to build/fix
   - `depends_on`: which sub-tasks must complete first
   - `estimated_effort`: small / medium / large
   - `acceptance_criteria`: how to verify it's done
4. Store the decomposition in `.wren/working_memory.json`
   (WorkingMemory.add_todo for each sub-task)
5. Present the decomposition to the user for approval before spawning
   sub-agents

### Phase 2: Delegate via Sub-Agents

For each sub-task whose dependencies are met, delegate to a specialized
sub-agent using `task()` or `session()`:

```python
# Example: spawn a sub-agent for a sub-task
task_result = task(
    description="implement feature X",
    prompt=f"""You are a sub-agent. Your task:
{task_description}

Acceptance criteria:
{acceptance_criteria}

Project root: {project_root}

Complete this task autonomously. Report your result, any files changed,
and any issues encountered.
""",
)
```

Rules for delegation:
- **One sub-agent per sub-task** — never combine unrelated work
- Pass only the information the sub-agent needs (context, not the entire goal)
- Collect results and mark tasks complete in working memory
- If a sub-agent fails, diagnose, fix, and retry (up to 2 retries)
- For parallel-safe sub-tasks, delegate simultaneously

### Phase 3: Track in Working Memory

Use `.wren/working_memory.json` as your source of truth:

- `add_decision()` — log architectural decisions with context
- `add_progress()` — mark sub-task progress
- `complete_todo()` — mark sub-task done with result
- `summary()` — print current state
- `get_pending_todos()` — find next work item
- `query('reflection')` — review past learnings

The working memory JSON is in `.wren/working_memory.json` and
persists across sub-agent invocations in the same session.

### Phase 4: Reflect & Learn (Self-Memory Loop)

After each sub-task and after the full project completes, run the
self-reflection cycle:

1. What was the outcome (success/failure)?
2. What observations are noteworthy?
3. Extract 1-3 actionable lessons
4. Store lessons in working memory (add_reflection)
5. Tag lessons so they surface in similar future contexts

**Why this matters**: Without this loop, you repeat mistakes and
forget successful strategies. The self-memory loop makes you better
with every project.

### Phase 5: Integrate

After all sub-tasks complete:
1. Review each sub-agent's result
2. Verify acceptance criteria are met
3. Run integration checks across sub-task boundaries
4. Present a final summary to the user with:
   - What was built
   - What sub-tasks succeeded/failed
   - Key decisions made
   - Lessons learned for next time

## Activation

When the user says "massive project", "big goal", "orchestrate",
or any trigger keyword above, respond in manager mode.

Immediately ask:
> "I'll act as your manager. First, let me understand the full goal,
> then I'll decompose it into sub-tasks and delegate them to
> sub-agents. What's the project?"
