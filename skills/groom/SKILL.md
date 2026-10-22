---
name: groom
description: Assess one Jira story for implementation readiness and prepare an explicitly confirmed review and label update.
---

# Groom Story

Assess one Jira story for implementation readiness, let the user review the
assessment, and—with explicit confirmation—post it to Jira and apply a
readiness label.

Read the [sprint-triage reference](../sprint-triage/references/sprint-triage-reference.md) before assessing the story.
Use its information-availability framework, ambiguity words, scope signals,
and dependency heuristics. Adapt those signals into actionable suggestions for
one story rather than producing a sprint triage report.

## Jira capabilities

Use the available Jira MCP capabilities to:

- fetch an issue with its comments, labels, components, and linked issues;
- add a comment; and
- update labels.

Choose tools by their described capabilities. Do not assume or hardcode an MCP
server name, tool name, or prefix. If comments are not returned with the issue,
use an available Jira capability to fetch them separately.

Before starting, confirm that all three operations are available. If any are
missing, stop and name the missing capability. Do not mutate Jira or fall back
to an unrelated CLI.

## Inputs

Identify exactly one Jira issue key, such as `EC-1234`, and an optional `--force` flag in the user's request. The flag may appear before or after the key. Ask for a missing issue key; reject malformed keys, unknown flags, or multiple issue keys and state the expected input: `EC-1234 [--force]`.

## Step 1: Fetch and display the story

Fetch the complete issue. If it is inaccessible or does not exist, report the
error and stop. If its issue type is not Story, explain that this skill supports
Jira stories and stop.

Use a dedicated acceptance-criteria field when one is returned. Otherwise,
extract a clearly named acceptance-criteria section from the description for
display without removing it from the displayed description. If neither exists,
show `Not provided`.

Before assessing it, display:

```text
<KEY> — <summary>
Status: <status>
Labels: <labels, or None>
Components: <components, or None>

Description
<description, or Not provided>

Acceptance criteria
<acceptance criteria, or Not provided>
```

Preserve the issue content as returned; do not silently fill in missing fields.

## Step 2: Check for an earlier review

Search all existing comments, following pagination when necessary, for the
substring `GROOMING-REVIEW`. Match the substring without requiring square
brackets because Jira may strip them.

If a match exists and `--force` was not supplied, report that the story has
already been assessed and stop without reassessing, commenting, or changing
labels. Tell the user that providing `--force` requests an explicit
reassessment.

If `--force` was supplied, continue and create a new review based on the
current issue state.

## Step 3: Assess readiness

Actively interrogate the story: generate the questions an implementer would
need answered, then classify their answers as **Provided**, **Findable**, or
**Missing** using the sprint-triage reference. A claim is Findable only when a
single, specific codebase search can answer it; do not perform a broad
investigation merely to avoid identifying a gap.

Evaluate these dimensions:

1. **Clarity** — Is there a clear problem statement, desired outcome, and
   enough context to make implementation decisions?
2. **Testability** — Are acceptance criteria present, unambiguous, and
   objectively verifiable? Apply the ambiguity-word checks from the reference.
3. **Information completeness** — Are entry points, examples, data shapes,
   domain references, or analogous implementations provided or concretely
   findable?
4. **Dependencies** — Are unresolved linked blockers, unmerged prerequisite
   work, cross-team dependencies, or pending decisions preventing work? Fetch
   the current status of linked blocking issues when it is not included in the
   original issue response.
5. **Scope** — Is there a clear stopping point, and can the work reasonably be
   delivered in one pull request?

Select exactly one result using this precedence:

| Result | Label | Rule |
|---|---|---|
| Blocked | `grooming:blocked` | A hard external dependency prevents implementation. |
| Needs work | `grooming:needs-work` | Required information is missing or acceptance criteria are unclear or non-testable. |
| Needs decomposition | `grooming:needs-decomposition` | The overall intent is workable, but the scope is too broad for one pull request. |
| Ready | `grooming:ready` | The story is clear, testable, sufficiently complete, bounded, and unblocked. |

Blocked takes precedence over needs work, which takes precedence over needs
decomposition, which takes precedence over ready. Missing helpful signals alone
do not prevent a Ready result; note concrete searches the implementer will need
instead.

Do not estimate story points.

## Step 4: Draft and preview the Jira comment

Draft the comment in this structure:

```markdown
[GROOMING-REVIEW]

## Automated Grooming Review

**Assessment:** <Ready | Needs work | Needs decomposition | Blocked>

<one or two sentences summarizing the readiness assessment>

### What's already clear
- <positive, story-specific signal>

### Suggested improvements
- **<dimension>:** <specific gap>. **Suggestion/question:** <concrete action or answerable question>

### Suggested breakdown
1. <independently implementable story>
```

Always include the marker, heading, assessment, summary, and “What's already
clear” section. Include “Suggested improvements” only when there are gaps or
helpful additions to suggest. Include “Suggested breakdown” only for Needs
decomposition, and make every proposed story independently implementable.

Frame gaps as suggestions or answerable questions for the reporter. Be
specific, constructive, and concise. The review prepares the story for a
grooming discussion; it does not replace that discussion or direct the team.

Display the complete proposed comment and the exact readiness label in the
terminal. Then ask:

> Post this Automated Grooming Review and apply `<label>` to `<KEY>`?

Do not post the comment or change labels until the user explicitly confirms.
If the user declines, stop and report that Jira was not changed.

## Step 5: Post and label

After confirmation:

1. Post the displayed comment without changing its contents.
2. If commenting fails, report the error and stop without changing labels.
3. Construct the new label set from the issue's current labels:
   - preserve every label except a recognized grooming readiness label;
   - remove any existing `grooming:ready`, `grooming:needs-work`,
     `grooming:needs-decomposition`, or `grooming:blocked` label; and
   - add the one selected readiness label.
4. Update the issue with that complete label set.

Do not remove unrelated labels and do not leave more than one recognized
grooming readiness label. If label updating fails after the comment succeeds,
report the partial failure and the exact label that must be applied manually;
do not post a duplicate comment or retry indefinitely.

## Step 6: Confirm the result

Report:

```text
Grooming review completed:
- Issue: <KEY> — <summary>
- Assessment: <result>
- Comment: Posted
- Readiness label: <label applied, or FAILED — apply manually>
```
