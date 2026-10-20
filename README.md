# Conforma Agent Skills

Reusable, Markdown-based agent instructions for Conforma policy work, Jira sprint workflows, and repository maintenance. The skill content does not depend on a particular model or agent harness. Harness-specific discovery, invocation, permissions, and MCP configuration remain the responsibility of the client.

## Use the skills

Clone the collection:

```bash
git clone https://github.com/conforma/agent-skills.git
```

Preserve the complete `skills/` tree, including each skill's references, templates, examples, and helper scripts. Install it in a directory supported by your agent harness. There is no single discovery path shared by all harnesses.

If your harness does not discover Agent Skills, give any tool-capable agent the path to the relevant `SKILL.md` and ask it to read and follow the instructions. For example:

> Read `/path/to/agent-skills/skills/ec-policy-debugging/SKILL.md` and use it to investigate `validation.log`.

The collection follows the `SKILL.md` name/description convention. Some clients discover skills automatically; others require a client-specific install location or an explicit file path. Check the active harness documentation for discovery and invocation behavior. Resource links are relative to each skill file, not the current working directory.

When installing a subset, include linked resources and skills: `ec-debug-violations` uses `ec-policy-debugging` and `ec-setup`; `ec-policy-debugging` links to `ec-setup`; `groom` uses the sprint-triage reference; and `renovate-act` uses the Renovate triage rules reference.

### Client-specific examples

These examples describe client installation, not alternate skill implementations:

- **Codex** ([skills documentation](https://developers.openai.com/codex/skills)): its documented project skill directory is `.agents/skills/`. Create it if needed, then copy the linked skill directories there, for example `mkdir -p /path/to/project/.agents/skills && cp -R /path/to/agent-skills/skills/ec-policy-debugging /path/to/agent-skills/skills/ec-setup /path/to/project/.agents/skills/`.
- **Pi:** load a specific skill with `pi --skill /path/to/agent-skills/skills/ec-policy-debugging/SKILL.md`.
- **Claude Code:** copy complete skill directories to the project or user skill location supported by your installed version. The former repository layout used `.claude/skills/`; that client directory is no longer the source layout here.

Client conventions change. Confirm native discovery paths and command syntax in current client documentation. A skill can also be invoked by file path where the harness permits local file access.

## Skills

| Skill | Purpose | Additional requirements |
|---|---|---|
| [`capture-context`](skills/capture-context/SKILL.md) | Record reusable subsystem knowledge after implementation. | Repository file access |
| [`ec-debug-violations`](skills/ec-debug-violations/SKILL.md) | Analyze Conforma validation logs and investigate violations. | Python 3; `kubectl` for TaskRun logs; policy access tools as needed |
| [`ec-policy-debugging`](skills/ec-policy-debugging/SKILL.md) | Understand a policy rule by inspecting its source, metadata, tests, and input data. | Python 3 for the bundled log summarizer; `pytest` to run its tests |
| [`ec-setup`](skills/ec-setup/SKILL.md) | Prepare a local reproduction from a Conforma validation log. | Conforma CLI and `conftest`; registry access for OCI policy sources |
| [`generate-policy`](skills/generate-policy/SKILL.md) | Create and verify Conforma policy rules, configuration, and tests. | Conforma CLI and OPA; image/key/registry access when validating an image |
| [`groom`](skills/groom/SKILL.md) | Assess one Jira story and, after confirmation, post a review and readiness label. | Jira MCP capabilities for reading, commenting, and updating labels |
| [`mid-sprint-add`](skills/mid-sprint-add/SKILL.md) | Record a mid-sprint addition and optionally move the issue into the sprint. | Jira MCP capabilities |
| [`renovate-act`](skills/renovate-act/SKILL.md) | Revalidate and carry out user-approved Renovate triage actions. | Authenticated GitHub CLI (`gh`) |
| [`renovate-triage`](skills/renovate-triage/SKILL.md) | Categorize automated dependency-update pull requests and produce a report. | Authenticated GitHub CLI (`gh`); `skopeo` is optional |
| [`scaffold-repo`](skills/scaffold-repo/SKILL.md) | Assess a repository with AgentReady and guide approved improvements. | AgentReady CLI |
| [`sprint-report`](skills/sprint-report/SKILL.md) | Report mid-sprint additions, with optional Slack posting. | Jira MCP; Slack MCP for posting |
| [`sprint-triage`](skills/sprint-triage/SKILL.md) | Assess Jira stories in the current sprint for implementation readiness. | Existing MCP tools `mcp__work-assistant__jira_sprint_issues` and `mcp__work-assistant__jira_get_issue` |
| [`write-rule`](skills/write-rule/SKILL.md) | Write a Rego policy rule and tests from a requirements file. | OPA and Conforma policy references |

The skills specify their inputs, outputs, and required operations. They do not grant tool access. Configure MCP servers, credentials, command execution, file access, and user approvals in the active harness. Jira and Slack MCP tool names and calls are retained as documented in the skills.

## Generated reports

The Renovate and sprint-report skills write reports under `.conforma/reports/` in the current project. Renovate's `--report <path>` option can still read and update an existing report at another path, including `.claude/reports/`; the skills do not move or delete old reports automatically.

## Migration from `conforma/claude-skills`

The canonical repository is now `conforma/agent-skills`. Replace the old clone and install the complete directories from `skills/` into your harness's skill location. Do not copy the old `.claude/` tree from a prior checkout. If you have local reports under `.claude/reports/`, keep them and pass their JSON path to `renovate-act --report <path>` when needed.

The old slash-command entry points are now named skills. Provide their existing inputs in your request or use the invocation syntax supported by your harness. Their domain workflow and confirmation steps remain in each `SKILL.md`.

## Contributing

- Put reusable instructions in `skills/<name>/SKILL.md`; keep names lowercase and hyphenated, with a clear description.
- Keep references, examples, templates, and scripts beside the skill that uses them. Link resources relatively to `SKILL.md` and do not rely on the caller's working directory.
- State inputs, prerequisites, outputs, missing-input behavior, and failure paths.
- Do not require model-specific features, client tool names, or harness settings in shared skill content. Keep client installation examples optional and outside the workflow instructions.
- Preserve approval gates, trust boundaries, and MCP tool identifiers/calls when updating service workflows.
- Run the local checks described in the pull request workflow before submitting changes.

## License

Apache 2.0
