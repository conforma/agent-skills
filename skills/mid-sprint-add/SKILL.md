---
name: mid-sprint-add
description: Record a Jira issue as a mid-sprint addition with a tagged reason and, when needed, add it to the active sprint.
---

# Mid-Sprint Add

Tag a Jira issue as a mid-sprint addition with a structured comment and optionally move it into the current active sprint.

## Prerequisites

This skill requires access to Jira through an MCP server (for example, mcp-atlassian) or an equivalent configured integration. If no Jira integration is available, stop and tell the user:

> This skill requires a Jira integration to be configured.
> Configure a Jira integration (MCP server or equivalent) using your harness's setup instructions.
>
> You can manually add this comment to the Jira issue:
> ```text
> [MID-SPRINT-ADD] reason: <your reason here>
> ```

## Inputs

Identify the Jira issue key (for example, `EC-1234`) and optional reason from the user's request. Treat text after the key as the reason. Ask for a missing issue key or reason.

## Step 1: Look Up the Active Sprint

Find the current active sprint for the Conforma team board:

1. Get sprints from board ID `10131` with state `active`
2. There should be exactly one active sprint. If none, tell the user there's no active sprint. If multiple, list them and ask which one.
3. Record the sprint name, ID, and start date.

## Step 2: Validate the Issue

Fetch the issue details using the provided issue key. If the issue does not exist or is inaccessible, report the error and stop.

If valid, note:
- Current status
- Whether it's already in the active sprint

## Step 3: Get the Reason

If the user provided a reason, use it. Otherwise, ask for one.

The reason must be a single line — strip or reject any newlines/carriage returns. If the user provides a multiline reason, collapse it to one line.

> What's the reason for adding this issue mid-sprint?
> Examples:
> - customer escalation from KFLUXSPRT-7872
> - unplanned dependency for EC-1881
> - pulled from backlog, team has capacity

## Step 4: Check for Existing Marker

Before adding a comment, check the issue's existing comments for a `MID-SPRINT-ADD` entry with the same reason. If an identical marker already exists, skip adding a duplicate and proceed to Step 6.

Note: Jira's API may strip square brackets from comment bodies. Match on `MID-SPRINT-ADD` rather than `[MID-SPRINT-ADD]`.

## Step 5: Add the Structured Comment

If no duplicate marker was found, add a comment to the issue with this exact format:

```text
[MID-SPRINT-ADD] reason: <the reason>
```

Do not add any other text to the comment. The author and timestamp are captured automatically by Jira.

If adding the comment fails, report the error and stop — do not proceed to sprint movement.

## Step 6: Move to Sprint (if needed)

If the issue is not already in the active sprint:
1. Tell the user: "This issue is not currently in sprint {sprint name}. Moving it now."
2. Add the issue to the active sprint using the sprint ID.
3. If the move fails, report the partial failure: "Comment was added but moving to sprint failed. Move the issue manually."

If the issue is already in the sprint:
1. Tell the user: "This issue is already in sprint {sprint name}. Comment added."

## Step 7: Confirm

Present a summary:

```text
Mid-sprint addition recorded:
- Issue: {KEY} — {summary}
- Sprint: {sprint name}
- Reason: {reason}
- Comment: {Added / Already existed (skipped)}
- Sprint membership: {Moved to sprint / Already in sprint / FAILED — move manually}
```
