---
name: sprint-triage
description: Assess current sprint Jira stories for implementation readiness and produce a categorized report.
---

# Sprint Triage

Review all Jira stories in the current sprint that are in New/To Do status. Assess each one and produce a categorized triage report the user can work from. This can inform later implementation and context-capture work.

Read the [sprint-triage reference](references/sprint-triage-reference.md) before starting the assessment. It contains detection heuristics, ambiguity word lists, and the information availability framework needed for Step 3.

## Required MCP tools

This skill uses these existing configured MCP tools, without changing their names or calls:

- `mcp__work-assistant__jira_sprint_issues`
- `mcp__work-assistant__jira_get_issue`

Make both tools available in the active harness. If either is unavailable, stop and name the missing capability.

## Instructions

### Step 1: Fetch Sprint Issues

Use the `jira_sprint_issues` MCP tool to get all issues in the current active sprint. Filter to issues with status "New" or "To Do".

If no issues match, tell the user and stop.

### Step 2: Get Full Details for Each Issue

For each issue found in Step 1, use `jira_get_issue` to retrieve the full details (description, acceptance criteria, labels, components, linked issues, epic).

### Step 3: Assess Each Story

Evaluate each story by asking five readiness questions. The goal is to determine: **"If an LLM agent had to implement this right now with no prior knowledge beyond the codebase and this story, could it produce a correct PR?"**

For each question, classify the information as:
- **Provided** — the story gives you the information directly
- **Findable** — the story doesn't provide it, but you can find it in the codebase (greppable function names, well-known directory structures, etc.)
- **Missing** — you can't start without someone providing this

Only **missing** information blocks a story's information readiness. **Findable** information is worth noting (it adds implementation time) but is not blocking. A story can also be blocked by external dependencies (Q3) regardless of information quality — see Step 4 for bucket precedence.

#### Assessment method: Ask questions, then try to answer them

Don't passively scan for the presence of signals. Instead, **actively interrogate the story**: imagine you're about to start implementing right now. What questions would you need answered? Generate those questions, then try to answer each one from the story description and your knowledge of the codebase.

- If the story answers the question directly — it's **provided**.
- If you can answer it with a concrete, quick search (a specific grep, reading a known file) — it's **findable**.
- If answering it would require significant investigation, reverse-engineering a process, or asking someone — it's **missing**.

Be skeptical. A story that says "follow the existing pattern for X" sounds findable, but ask yourself: do you actually know what that pattern is? Could you describe it right now? If not, try to figure it out — and if that turns into a multi-step investigation rather than a quick lookup, it's not findable, it's missing.

The litmus test for "findable" is: **can you describe a single, specific search that would answer the question?** "Grep for `rekor` in ec-cli" is a specific search. "Look at the CI workflows across two repos to understand the publishing pipeline" is an investigation.

#### Question 1: Do I understand what needs to be done?

The story must communicate the problem and the desired outcome clearly enough that someone with no prior context can start working.

**Check for:**
- Is there a problem statement? (what's wrong or missing today)
- Is there a desired outcome? (what should be true when this is done)
- Are there acceptance criteria that can be objectively verified?
- Is the language unambiguous? (see the ambiguity word list in the reference doc)
- Is there enough "why" context to make judgment calls during implementation?

**Required for Act Now:**
- Clear problem statement
- Clear desired outcome
- Testable, unambiguous acceptance criteria

**Red flags:**
- Description is just the title restated or empty
- AC use subjective language: "appropriate", "better", "improved", "clean", "properly", "as needed"
- AC require human judgment to verify: "looks good", "feels right", "is user-friendly"
- Only says what to build, never why (no context for tradeoff decisions)

#### Question 2: Do I have the information I need?

Even with a clear goal, the implementer needs enough technical detail to write code.

**Check for:**
- Do I know where to start in the code? (file paths, function names, package names, CLI commands, error messages to grep for)
- Do I know what the inputs and outputs look like? (data formats, schemas, sample values)
- Are there examples? (sample input/output, before/after, test cases)
- If specs or standards are referenced, are they linked or described? A public spec without a link is only findable if the format is already used in the codebase (e.g., greppable type definitions or sample files). Otherwise, it's missing.
- If domain-specific terms are used, can I find their meaning in the codebase or are they explained?
- Are there similar implementations I can use as patterns? ("follow the pattern in X")

**These are helpful signals, not requirements.** A story with clear AC but no file paths is still Act Now if the code is findable. A story with file paths but vague AC is Clarify. Note which helpful signals are provided vs findable vs missing — this information goes in the report.

**Red flags:**
- References a system, tool, or API outside the workspace without explaining how to access it
- "Per the spec" without linking the spec
- "Similar to what we did for X" without saying what X is or where to find it
- Uses domain jargon that doesn't appear anywhere in the codebase

#### Question 3: Are there external dependencies?

Blockers that prevent starting regardless of how clear the story is.

**Check for:**
- Does this depend on work by another team that hasn't landed?
- Does this need an upstream PR to merge first?
- Are there open decisions that need to be made before implementation? (architecture choices, API designs, format decisions)
- Do the Jira linked issues include unresolved blocking relationships? (Check "is blocked by" links retrieved in Step 2 — if the linked issue is not Done/Closed, it's a blocker)

**Detection signals for Blocked:**
- Jira "is blocked by" links to issues that are not Done/Closed
- "Blocked by", "depends on", "waiting for", "after X lands" in story text
- References to unmerged PRs as the source of truth for a format/API
- "Once X is decided" or similar deferred-decision language

**Detection signals for Clarify** (not Blocked — these need information, not a dependency to resolve):
- References to systems outside the workspace without explaining how to access them
- Requires access, credentials, or infrastructure the implementer might not have, but the story doesn't explain how to obtain them
- References to external teams or people ("talk to", "check with", "coordinate with") without specifying what information is needed
- Open questions in the description ("TBD", "to be determined", question marks in key sections)

#### Question 4: Do I know where the work goes?

Which repository or repositories does the work live in?

**Keyword mapping** (from the story description and summary):

| Signal | Repo |
|--------|------|
| Policy rules, Rego, attestation validation rules, SLSA checks | `ec-policies` |
| CLI commands, flags, `ec validate`, `ec track`, verify command | `ec-cli` |
| CRD, custom resource, Kubernetes types, API types, schema | `conforma-crds` |
| Build pipeline, Tekton task (build context), PipelineRun, SLSA generator | `build-definitions` |
| Release pipeline, release task, managed pipeline, advisory | `release-service-catalog` |
| Conforma Tekton task (verify/validate context), task bundle | `conforma-tekton-catalog` |
| Acceptance tests, e2e, deployment verification | `infra-deployments-ci` |

**Architecture flow** — changes often span repos in predictable patterns:
- New policy rule -> `ec-policies` (rule + tests) and possibly `ec-cli` (if new CLI surface)
- New CRD field -> `conforma-crds` (types + generate) and `ec-cli` (if CLI consumes it)
- New build task -> `build-definitions` (task YAML + tests)
- New release task -> `release-service-catalog` (task YAML + tests)

**Other signals:**
- Components or labels on the Jira issue
- Linked issues or PRs pointing to specific repos
- Epic context

Result:
- **Known** — repo(s) identified, with parenthetical noting what work happens where
- **Unclear** — cannot determine from the story; this pushes the story toward the Clarify bucket

#### Question 5: Do I know when to stop?

Without scope boundaries, an LLM will over-build — adding error handling, abstractions, and features beyond what was asked for.

**Check for:**
- Are scope boundaries defined? (what's in scope, what's explicitly not)
- Is the work sized for a single PR, or does it need decomposition?
- Are there unbounded verbs without concrete targets? ("improve", "optimize", "clean up", "refactor" — see reference doc)

**Red flags:**
- Open-ended language: "and more", "etc.", "as needed", "other improvements", "and similar"
- "Improve" / "optimize" / "clean up" without specific measurable targets
- Story describes work that would naturally be 3+ PRs
- Story touches more than 3 repos without clear task decomposition

### Step 4: Categorize into Buckets

Based on the five questions, place each story into exactly one bucket.

**Required signals** (missing = cannot be Act Now):
- Clear problem statement
- Clear desired outcome
- Testable, unambiguous acceptance criteria

**Helpful signals** (missing = note it, but doesn't block Act Now):
- Entry points (file paths, function names, CLI commands)
- Input/output examples and data shapes
- Pattern references ("similar to X")
- Domain context links (specs, docs)
- Explicit scope boundaries

| Bucket | Criteria |
|--------|----------|
| **Act Now** | All required signals are solid. No blockers (Q3). Repo known (Q4). Helpful signals don't all need to be present, but any that are missing or only findable should be noted. **The litmus test: an LLM knows what to build and can verify when it's done.** |
| **Break Down** | Required signals are present for the overall goal, but scope (Q5) is too broad — the work spans too many files, repos, or concerns for a single implementation pass. Needs decomposition into individually-workable tasks, each of which would pass the Act Now test. |
| **Clarify** | One or more required signals missing or compromised by ambiguity. Also applies when the story references systems, repos, or tools outside the workspace without explaining how to access them, or needs access/credentials/coordination details that aren't provided. The report lists **specific, answerable questions** — not "needs more detail" but "Which parser is this referring to — the v0.2 parser or the v1.0 parser?" |
| **Blocked** | Q3 identifies a hard external dependency — unmerged upstream PR, waiting on another team's deliverable, unresolved architecture decision — regardless of how well other questions are answered. Note the specific blocker. Missing access information alone is Clarify, not Blocked. |

If a story could fit multiple buckets, use the highest-priority bucket: Blocked > Clarify > Break Down > Act Now.

### Step 5: Generate the Triage Report

Create a markdown file named `sprint-triage-<date>.md` in the current working directory (use today's date in YYYY-MM-DD format).

Use this format:

```markdown
# Sprint Triage — Sprint <sprint-name> (<date>)

## Sprint Readiness Summary

- **Ready for implementation:** <count> of <total> stories (Act Now)
- **Most common gap:** <the readiness question or signal that most stories fail on>
- **Quickest wins:** <stories that need only 1-2 questions answered to become Act Now, if any>

---

## Act Now (<count>)

### <ISSUE-KEY>: <summary>
- **Reporter:** <reporter name from Jira>
- **Summary:** <1-2 paragraph distillation of what this story is about, the problem it
  solves, and why it matters. Written from the Jira description but condensed so the
  reader can make decisions without opening Jira.>
- **Repos:** <repo-name> (<what work happens here>), <repo-name> (<what work happens here>)
- **Scope:** <concrete implementation sketch — specific code changes, files to touch,
  tests to write. NOT a time estimate.>
- **Readiness notes:** <any helpful signals that are findable but not provided — things
  that would make implementation smoother if added to the story. Omit this section if
  everything needed is provided.>
- **Bucket rationale:** <1 sentence on why this is Act Now — what makes it immediately workable>

---

## Break Down (<count>)

### <ISSUE-KEY>: <summary>
- **Reporter:** <reporter name from Jira>
- **Summary:** <same format as above>
- **Repos:** <repo(s) with parenthetical>
- **Scope:** <what's known about the work, and why it needs decomposition>
- **Suggested breakdown:** <how to split this into individually-workable tasks>
- **Bucket rationale:** <why it needs breakdown — e.g., "Spans 3 repos with 5 distinct
  work items, needs task-level decomposition">

---

## Clarify (<count>)

### <ISSUE-KEY>: <summary>
- **Reporter:** <reporter name from Jira>
- **Summary:** <same format — describe what IS known about the story>
- **Repos:** <if known, list them; if not, say "Unclear — <reason>">
- **What's clear:** <what information IS present and solid>
- **What's missing:** <specific information gaps, organized by which readiness question
  they fail. Be concrete: "AC #2 says 'appropriate error handling' — needs specific error
  scenarios" not "Needs more detail">
- **Questions to resolve:** <numbered list of specific, answerable questions that would
  move this story toward Act Now. These should be concrete enough that the reporter could
  answer each one in a sentence or two.>
- **Bucket rationale:** <why it needs clarification>

---

## Blocked (<count>)

### <ISSUE-KEY>: <summary>
- **Reporter:** <reporter name from Jira>
- **Summary:** <same format>
- **Repos:** <repo(s) if known>
- **Scope:** <implementation sketch if known>
- **Blocked on:** <specific blocker — team, PR, external dependency, decision needed>
- **Bucket rationale:** <why it's blocked>
```

### Step 6: Present the Report

After writing the file:
1. Tell the user the file path
2. Print the Sprint Readiness Summary from the top of the report
3. If there are Act Now stories, suggest which looks like the best one to start with and why

## Important Notes

- The Summary field is the most important part of each entry. The user needs enough context to make prioritization decisions without opening Jira. Distill the description — don't just copy it verbatim, and don't reduce it to one sentence.
- The Scope field describes implementation work, not time. "CLI predicate parsing for v1.1 format + 2 new policy rules + tests" not "~3 days".
- When a story touches multiple repos, list them in dependency order (what to do first).
- Use the repo keyword mapping table above, but also read the full story description for context — a story about "improving error messages" could be ec-cli, ec-policies, or both depending on the details.
- The "Questions to resolve" in Clarify stories are the most actionable part of the triage. Write them so the reporter can answer each one quickly. Bad: "Needs more detail about the approach." Good: "The story references 'the new attestation format' — is this SLSA Provenance v1.0 or v1.1? Can you link the spec or paste a sample?"
- For Act Now stories, "Readiness notes" should flag information that's findable but not provided. This isn't a blocker, but it helps the implementer know what they'll need to discover. Example: "Story doesn't name specific files, but the Rekor integration is greppable in ec-cli."
