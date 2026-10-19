# Claude EC Skills

Claude Code skills and commands for [Conforma](https://github.com/conforma/cli) policy debugging, vulnerability patching, and sprint management.

## Overview

These tools help you:

- Debug and resolve Conforma/EC validation failures
- Assess Jira stories for implementation readiness before backlog grooming
- Track mid-sprint story additions with structured tagging
- Generate sprint reports surfacing unplanned work
- Prepare verified Conforma CLI vulnerability patches for UBI RPMs and Go modules

## Installation

Copy the `.claude` directory to your project or home directory:

```bash
# Clone this repo
git clone https://github.com/conforma/claude-skills.git

# Copy to your project
cp -r claude-skills/.claude /path/to/your/project/

# Or copy to home directory for global access
cp -r claude-skills/.claude ~/
```

## Commands

### `/groom`

Assess one Jira story for implementation readiness and preview a structured
Automated Grooming Review before posting it and applying a readiness label.

```bash
/groom EC-1234
/groom EC-1234 --force  # Explicitly reassess a previously reviewed story
```

The command evaluates clarity, testability, information completeness,
dependencies, and scope. It requires Jira MCP capabilities for reading issues
and comments, posting comments, and updating labels.

### `/ec-setup`

Set up a local debugging environment from a Conforma validation log.

```bash
/ec-setup logs/validation.log
```

This command:
1. Extracts the policy configuration from the log
2. Saves the public key for signature verification
3. Pulls the policy OCI bundle
4. Generates a `run.sh` script to reproduce the validation locally

### `/ec-debug-violations`

Parse a log file and debug all policy violations.

```bash
/ec-debug-violations logs/validation.log
```

This command:
1. Extracts all unique violation codes from the log
2. Looks up each rule's metadata (title, description, solution)
3. Analyzes affected components and error messages
4. Provides root cause analysis and recommended actions
5. Generates a prioritized summary

### `/mid-sprint-add`

Tag a Jira issue as a mid-sprint addition with a structured comment.

```bash
/mid-sprint-add EC-1234 customer escalation from KFLUXSPRT-7872
```

This command:
1. Looks up the current active sprint for the Conforma team
2. Adds a `[MID-SPRINT-ADD] reason: ...` comment to the issue
3. Moves the issue into the active sprint if not already there

### `/sprint-report`

Generate a report of all mid-sprint story additions.

```bash
/sprint-report          # Current/most recent sprint
/sprint-report --post   # Generate and post to #team-conforma
```

This command:
1. Queries all issues in the sprint
2. Detects mid-sprint additions via JQL (newly created issues) and changelog analysis (pre-existing issues moved in)
3. Enriches with `[MID-SPRINT-ADD]` comment reasons when available
4. Generates a report: which stories were added, by whom, when, and why
5. Optionally posts to the team Slack channel

## Skills

### `ec-policy-debugging`

Core skill for investigating individual policy violations. Automatically invoked when asking about EC violations.

**Example prompts:**
- "Why did `olm.unmapped_references` fail?"
- "What does the `rpm_packages.unique_version` rule check?"
- "Debug this EC validation error: [paste error]"

### `vuln-patcher`

Prepare verified UBI RPM or Go-module patches for Conforma CLI vulnerability tickets. It uses Jira read access and a validated CLI checkout. If no checkout is available, it asks whether to use a supplied path or clone the user's personal fork. It stops before pushing or opening a PR until approved.

The skill follows the Agent Skills format. Other compatible harnesses may need their skill loader pointed at `.claude/skills`.

**Example prompts:**
- "Assess EC-1234 as a Conforma vulnerability and prepare a patch."
- "Check RHSA 172528 against current Conforma releases."

## File Structure

```text
.claude/
├── commands/
│   ├── ec-setup.md              # /ec-setup command
│   ├── ec-debug-violations.md   # /ec-debug-violations command
│   ├── groom.md                 # /groom command
│   ├── mid-sprint-add.md        # /mid-sprint-add command
│   └── sprint-report.md         # /sprint-report command
├── references/
│   └── sprint-triage-reference.md # Shared readiness-assessment heuristics
├── reports/                     # Generated sprint reports
├── skills/
│   ├── ec-policy-debugging/
│   │   ├── SKILL.md             # Skill definition
│   │   ├── debugging.md         # Full debugging reference
│   │   └── summarize_violations.py  # Log parsing utility
│   └── vuln-patcher/
│       ├── SKILL.md
│       └── scripts/
│           ├── active-release-branches.sh
│           └── assess.sh
└── settings.local.json          # Claude Code settings
```

## Requirements

- [Claude Code](https://claude.ai/claude-code) CLI
- [ec-cli](https://github.com/conforma/cli) (for local validation)
- [conftest](https://www.conftest.dev/) (for pulling policy bundles)
- [cosign](https://github.com/sigstore/cosign) (for downloading attestations)
- [crane](https://github.com/google/go-containerregistry/tree/main/cmd/crane) (for inspecting images)

## Example Workflow

1. **Get a validation log** from a failed Konflux/Conforma pipeline

2. **Set up debugging environment:**
   ```bash
   /ec-setup logs/my-validation.log
   ```

3. **Debug all violations:**
   ```bash
   /ec-debug-violations logs/my-validation.log
   ```

4. **Investigate specific violations:**
   ```text
   "Why is olm.unmapped_references failing for the operator bundle?"
   ```

5. **Run validation locally** (after setup):
   ```bash
   cd release-policies-myimage-amd64/
   ./run.sh
   ```

## License

Apache 2.0
