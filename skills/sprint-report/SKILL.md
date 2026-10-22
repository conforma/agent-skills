---
name: sprint-report
description: Report Jira issues added to a Conforma sprint after it started, with optional Slack posting.
---

# Sprint Report — Mid-Sprint Additions

Query all issues in a sprint, detect which were added after the sprint started (via changelog analysis), and generate a report showing what was added mid-sprint, by whom, when, and why. Optionally enriches with `[MID-SPRINT-ADD]` comment reasons when available.

## Prerequisites

This skill requires access to Jira through an MCP server (for example, mcp-atlassian) or an equivalent configured integration. The `--post` option additionally requires a Slack MCP server.

If no Jira MCP tools are available, stop and tell the user:

> This skill requires a Jira MCP server to be configured in the active harness.
> See https://github.com/mcp-atlassian/mcp-atlassian for setup instructions or
> use the setup instructions for your harness.
>
> To manually find tagged mid-sprint additions, search Jira with:
> ```text
> sprint = <sprint-id> AND comment ~ "MID-SPRINT-ADD"
> ```
> Note: this only finds explicitly tagged issues. The automated report also uses
> changelog analysis to detect all issues added after the sprint started.

## Inputs

Identify these optional inputs in the user's request:
- `--post [#channel ...]` — Post the report to Slack. Defaults to `#team-conforma` if no channels are specified. Can list one or more channels (for example, `--post #team-conforma #conforma-leads`).
- `--sprint <name>` — Target a sprint by name (for example, `--sprint "Conforma 26-09"`) instead of the current active sprint. Partial matches are accepted (for example, `--sprint 26-09`).

## Step 1: Identify the Sprint

1. Get all sprints from the Conforma Team board (ID: `10131`) — fetch active, then closed if needed.
2. If `--sprint` was provided, find sprints whose name contains the provided text (case-insensitive).
   - If exactly one match: use it.
   - If no matches: list available sprint names and ask the user to clarify.
   - If multiple matches: list the matching sprints (name, dates, state) and ask the user to pick one.
3. If no `--sprint` flag, use the active sprint. If multiple active sprints exist, list them and ask the user to pick. If none active, use the most recently closed sprint.
4. Record: sprint name, ID, start date, end date, goal.

## Step 2: Fetch All Sprint Issues

Get the total count of issues in the sprint to use as the denominator for percentages. Query all issues in the sprint and record:
- Total issue count
- Sum of all story points (`customfield_10028`) across the sprint (total points)

Paginate using `start_at` until all results are fetched — the Jira API returns at most 50 items per request. If any page request fails, note the report as potentially incomplete. Treat null or missing story points as 0.

## Step 3: Detect Mid-Sprint Additions

Use a two-pass approach to efficiently find all mid-sprint additions.

### Pass 1: Issues created after sprint start (JQL — cheap)

Issues that didn't exist when the sprint started are definitively mid-sprint additions:

```text
sprint = <sprint-id> AND created >= "<day-after-sprint-start>"
```

Use the **day after** the sprint start date in the JQL query (e.g. if the sprint started on `2026-07-15`, use `"2026-07-16"`). JQL only supports date precision (not datetime), so this avoids false positives for issues created on the sprint start date before the sprint actually began. Issues created on the sprint start date itself are handled by Pass 2's datetime-precise changelog check.

Paginate using `start_at` if more than 50 results are returned. For each matching issue, record:
- Issue key, summary, status, assignee
- Issue type, priority, story points (`customfield_10028`)
- **Date added**: the issue's `created` date
- **Added by**: the issue's `reporter` (creator)
- **Days after sprint start**: calculate from the sprint start date
- **Detection method**: `created-after-start`

### Pass 2: Pre-existing issues added mid-sprint (changelog — targeted)

Issues that existed before the sprint started but were moved into it later require changelog analysis. Only check issues **not** already found in Pass 1:

1. From the full issue list (Step 2), exclude any issues already identified in Pass 1.
2. For each remaining issue, fetch it with `fields="summary"` and `expand="changelog"` (minimal fields to reduce response size — issue details are already available from Step 2). Look for a changelog entry where:
   - The field is `Sprint` (or `sprint`)
   - The change **added** this sprint — check that the sprint **ID** appears in `to_id` (mcp-atlassian) or `to` (raw Jira API) but **not** in `from_id`/`from`. Match by ID, not name, to avoid substring false positives with similarly named sprints like "26-1" vs "26-10"
   - The changelog timestamp (full datetime) is **after the sprint start datetime**
3. Any issue matching these criteria was added mid-sprint. Record:
   - Issue key, summary, status, assignee
   - Issue type, priority, story points (`customfield_10028`)
   - **Date added**: the changelog timestamp
   - **Added by**: the changelog author
   - **Days after sprint start**: calculate from the sprint start date
   - **Detection method**: `changelog`

Issues where the sprint field was set **before** the sprint start datetime are considered planned — skip them.

**Edge case:** An issue created on the sprint start date with the Sprint field set at creation time may not produce a Sprint changelog entry. Pass 1's day-after filter also excludes it. Such issues (created on sprint day 1 and immediately placed in the sprint) are treated as planned, which is generally correct for sprint-planning-day activity.

### Combine results

Merge the additions from both passes into a single list, sorted by date added.

## Step 4: Enrich with Comment Data

Search for `[MID-SPRINT-ADD]` comments to add "reason" context to detected additions:

```text
sprint = <sprint-id> AND comment ~ "MID-SPRINT-ADD"
```

Paginate using `start_at` if more than 50 results are returned. The JQL search returns issue keys but **not** comment bodies. For each matching issue, fetch the full issue with comments included (e.g. `jira_get_issue` with `fields="summary,comment"` and `comment_limit=100`). Then scan the returned comments for entries containing `MID-SPRINT-ADD`. Only include comments whose creation timestamp is **on or after the sprint start date** — issues may carry tags from previous sprints.

For each qualifying comment, extract:
- **Reason**: Everything after `reason:` on the `MID-SPRINT-ADD` line (single line only)

Note: Jira's API may strip square brackets from comment bodies. Match on `MID-SPRINT-ADD` rather than `[MID-SPRINT-ADD]`.

**Merge results:**
- Start with the combined additions from Step 3 (both passes).
- For each, attach the reason from the `MID-SPRINT-ADD` comment if one exists.
- If an issue was detected in Step 3 but has no comment, set reason to `(not provided)`.
- If a comment-tagged issue was somehow missed by Step 3 (e.g. changelog data unavailable), include it with detection method `comment-only`. For these issues, use the comment's author as "Added by" and the comment's timestamp as "Date added".

**Deduplication:** Each issue appears only once. If an issue has multiple qualifying `MID-SPRINT-ADD` comments, list additional reasons comma-separated in the Reason column.

**Calculate points:**
- **Unplanned points**: sum of story points for mid-sprint addition issues only
- **Planned points**: total points (from Step 2) minus unplanned points
- **Percentage**: if total issue count is zero, report 0%

## Step 5: Generate the Report

Build a markdown report. Sanitize all Jira-derived values (summaries, authors, reasons) for markdown table rendering — escape pipe characters and strip newlines.

**Reason categorization:** Group free-text reasons into categories using keyword matching: reasons containing "escalation" or "customer" map to "Customer escalation"; "dependency" or "blocker" map to "Unplanned dependency"; "capacity" or "backlog" map to "Backlog pull"; anything else maps to "Other". Each issue's points count toward one category only.

```markdown
# Mid-Sprint Additions Report — {Sprint Name}

**Sprint:** {name} ({start_date} → {end_date})
**Goal:** {sprint goal}
**Total issues in sprint:** {n}
**Mid-sprint additions:** {n} ({percentage}%)

## Additions

| # | Issue | Summary | Added By | Date Added | Day Added | Reason | Category | Points |
|---|-------|---------|----------|------------|---------|--------|----------|--------|
| 1 | EC-1234 | Fix the thing | Rob Nester | 2026-07-18 | +3 | customer escalation | Customer escalation | 2 |
| 2 | EC-1235 | Update config | Jane Doe | 2026-07-20 | +5 | (not provided) | Other | 1 |

(Escape `|` in cell values with `\|` and strip newlines so each row stays on one line.)
(Issues with reason "(not provided)" were detected via changelog but had no `[MID-SPRINT-ADD]` comment.)

## Summary by Reason Category

Categories are assigned per the keyword mapping above. Use these exact category names:
- **Customer escalation** — reason contains "escalation" or "customer"
- **Unplanned dependency** — reason contains "dependency" or "blocker"
- **Backlog pull** — reason contains "capacity" or "backlog"
- **Other** — anything that doesn't match the above

| Category | Count | Total Points |
|----------|-------|--------------|
| Customer escalation | 2 | 5 |
| Unplanned dependency | 1 | 3 |
| Backlog pull | 1 | 1 |

## Observations

{Brief analysis: percentage of unplanned work, most common reason category, total unplanned story points vs total planned story points}
```

If no mid-sprint additions are detected (changelog found no issues added after sprint start, and no qualifying `[MID-SPRINT-ADD]` comments exist):

```markdown
# Mid-Sprint Additions Report — {Sprint Name}

No mid-sprint additions detected.

All {n} issues in this sprint were present at sprint start ({start_date}).
```

## Step 6: Save the Report

Slugify the sprint name for the filename: lowercase, replace spaces and special characters with hyphens, collapse multiple hyphens. For example, `Conforma 26-10` becomes `conforma-26-10`.

Write the report to `.conforma/reports/sprint-report-{slugified-name}.md` under the current project directory.

```bash
mkdir -p .conforma/reports
```

## Step 7: Post to Slack (if --post)

The report must be saved (Step 6) before posting.

If `--post` was specified and a Slack MCP server is available:

1. Determine target channels: use any channels listed after `--post`, or default to `#team-conforma` if none specified.
2. If the report exceeds Slack's message limit (~4000 chars), post a summary (header + additions table) and note the full report file path.
3. For each channel, look up the channel ID by name and post the report. Track success/failure per channel independently.
4. Confirm which channels received the report and note any failures.

If `--post` was specified but no Slack MCP is available, tell the user:
> No Slack MCP server is configured. Report saved locally — copy and paste it into the appropriate channel manually.

If `--post` was not specified, remind the user:
> Request `--post` the next time you run this skill to share the report in #team-conforma.

## Step 8: Present Summary

```text
Sprint report generated:
- Sprint: {name}
- Total issues: {n}
- Mid-sprint additions: {n} ({percentage}%)
- Unplanned points: {n}
- Report saved to: .conforma/reports/sprint-report-{slugified-name}.md
{- Posted to: #channel1, #channel2 (if --post)}
```
