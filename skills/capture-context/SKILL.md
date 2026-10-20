---
name: capture-context
description: Capture non-obvious implementation context in a subsystem design document after implementation.
---

# Capture Context

After implementing a story, extract the non-obvious knowledge you needed and persist it as a design doc in the repo. This is the hill climbing loop — each implementation makes the codebase smarter for the next one.

Read [the capture-context reference](references/capture-context-reference.md) before starting. It contains quality-bar examples, filter criteria, and subsystem categories.

## When to Use

Run this after implementation and its acceptance criteria are verified, before committing. If the task produced an `agent-context.json` sidecar, consult it as an additional source. Skip if implementation was straightforward and required no knowledge beyond the code and existing repository instructions.

**Trigger signals — run this step if any are true:**
- The user had to answer questions about how something works
- You discovered cross-repo connections by exploring multiple repos
- The triage identified "missing" context that someone had to provide
- You made implementation choices based on conventions not documented anywhere
- You spent significant time reverse-engineering a process or mechanism

## Instructions

### Step 1: Identify what was learned

Review your conversation and implementation process. For each piece of context that was essential to the implementation, ask: **"Was this findable in the codebase before I started?"**

Generate candidates by answering these questions:
- What did I need to know that wasn't in the code or existing repository instructions, such as AGENTS.md or a harness-specific equivalent?
- What questions did the user answer that a design doc should have covered?
- What cross-repo connections did I discover that aren't documented?
- What conventions or constraints shaped my approach that aren't written down?
- What would I tell the next person touching this subsystem to save them the same discovery?

For each candidate, record:
- **Knowledge**: What was learned (one sentence)
- **Source**: Where it came from (user, Jira story, exploration, external system)
- **Subsystem**: What area of the codebase it belongs to

### Step 2: Filter for persistence value

For each candidate, apply these filters. All three must pass:

| Filter | Question | If no → drop |
|--------|----------|--------------|
| **Reusable** | Would another story touching this subsystem need this? | Story-specific — belongs in PR description |
| **Non-obvious** | Can you derive this by reading the code? | Code is the source of truth — don't repeat it |
| **Stable** | Will this remain true for more than one sprint? | Too transient to persist |

Also check for duplication:
- Is this already documented in existing repository instructions? → Skip
- Is this already in an existing design doc? → Update that doc instead
- Is this better suited to AGENTS.md (implementation instructions, conventions, build commands)? → Suggest an AGENTS.md update instead

If nothing passes all three filters, report that no design doc is needed and stop.

### Step 3: Find and read existing design docs

Search the current repo for existing design docs that might already cover the subsystem:

```bash
find . -not -path './.git/*' \( -iname 'DESIGN.md' -o -iname 'design-*.md' -o -path '*/design/*.md' \) 2>/dev/null
```

The canonical location for design docs is `design/` at the repo root. Also check for `DESIGN.md` files in subdirectories (some subsystems keep them alongside the code).

**Read every doc that might overlap with your candidates.** Don't just list files — read their contents so you know what's already documented. This prevents duplicating existing knowledge and helps you decide whether to:

- **Update an existing doc** → The subsystem is already documented; add to it
- **Create a new doc** → No existing doc covers this subsystem; create it in `design/`

Name files after the subsystem or concern, not the story:
- `publishing-pipeline.md` not `EC-1942-notes.md`
- `overlay-promotion.md` not `sprint-47-context.md`
- `rule-filtering.md` not `policy-resolver-changes.md`

### Step 4: Write or update the design doc

**Format:**

```markdown
# <Subsystem/Topic Name>

<1-2 sentence overview: what this subsystem does and why it exists.>

## <Question an implementer would ask>

<Answer — the operational knowledge, design rationale, or constraint
that isn't obvious from reading the code. Focus on WHY, not WHAT.>

## <Another question>

<Answer>
```

Each section heading should be a question or concern an implementer would have. Each body answers it with the operational knowledge, design rationale, or constraint. See the reference doc for examples.

**If creating a new doc:**
- Create it in `design/` at the repo root (create the directory if it doesn't exist)
- Write a 1-2 sentence overview
- Add one section per knowledge item that passed filtering
- Keep each section focused — one concept per heading

**If updating an existing doc:**
- Read the existing doc first
- Add new sections for new knowledge
- Update sections that are now outdated
- Remove sections that are no longer accurate
- Integrate, don't append — the doc should read as a coherent whole

### Step 5: Verify the doc

Read the doc back and check each section against the quality bar:

| Check | Keep if yes | Remove if yes |
|-------|-------------|---------------|
| Tells the reader something they can't figure out from the code? | Keep | — |
| Explains WHY something is the way it is? | Keep | — |
| Just describes WHAT the code does? | — | Remove |
| Specific to one story and unlikely to matter again? | — | Remove |
| Already documented in existing repository instructions? | — | Remove |
| Uses jargon without explanation? | — | Fix or remove |

Also verify:
- The doc is under 100 lines (if longer, it's trying to cover too much — split into multiple docs)
- Section headings are questions or concerns, not generic labels ("Background", "Overview")
- No references to specific Jira stories or PRs (those rot — state the knowledge directly)

### Step 6: Report

Tell the user:
1. Which design doc was created or updated, and its path
2. What knowledge was captured — one-line summary per section added
3. What was filtered out and why (brief — just the candidates that didn't pass)
4. Whether any candidates would be better as AGENTS.md updates

The design doc should be committed with the implementation changes — it's part of the PR.

## Important Notes

- Design docs are organized by subsystem, not by story. Multiple stories may contribute to the same doc over time. A story that touches rule filtering should update `design/rule-filtering.md`, not create a new file.
- The goal is NOT comprehensive documentation. It's capturing the specific knowledge that was needed and missing. A design doc with 3 focused sections is better than one with 10 vague ones.
- If the implementation was entirely straightforward (everything was in AGENTS.md and the code), say so and skip the doc. Not every implementation produces design doc content.
- If present, an `agent-context.json` sidecar captures line-level reasoning about the diff. The design doc captures subsystem-level operational knowledge. They're complementary, not redundant.
- Never reference specific Jira stories, PR numbers, or dates in design docs. State the knowledge directly. Stories close, PRs merge, but the knowledge persists.
