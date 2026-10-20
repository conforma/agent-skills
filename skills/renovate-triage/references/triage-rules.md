# Renovate PR Triage Rules

Triage and manage automated dependency update PRs across the conforma and enterprise-contract GitHub orgs. Categorizes PRs by risk, verifies Go container image availability, detects merge cascades, and coordinates approved actions (approve + auto-merge, or close with comment).

## When to Use

- Managing Renovate or red-hat-konflux PR backlog
- Triaging automated dependency updates across the org
- Checking which dependency PRs are safe to merge
- Cleaning up stale or abandoned automated PRs

## Skills

- `renovate-triage` — Analyze open automated PRs, categorize them, and write a triage report.
- `renovate-act` — Execute user-approved actions from a triage report.

## Categorization Rules

Each PR is classified into exactly one category. Categories are evaluated in priority order — first match wins.

### Priority 1: Abandoned Branch

**Signal:** PR targets a branch outside Renovate's `baseBranchPatterns` (primary), or PR title ends with `- abandoned` (secondary).

**Action:** Close with comment.

**How to detect:** Parse the shared Renovate config from `conforma/.github/config/renovate/renovate.json` and extract `baseBranchPatterns`. Current patterns target `main` and `release-v0.7+`. Compare each PR's `baseRefName` against these patterns. A PR targeting `release-v0.5` or `release-v0.6` is on an abandoned branch.

**Fetch the config:**
```bash
gh api /repos/conforma/.github/contents/config/renovate/renovate.json --jq '.content' | base64 -d
```

**Check per-repo overrides** (repos may extend or narrow the shared config):
```bash
gh api /repos/<OWNER>/<REPO>/contents/renovate.json --jq '.content' | base64 -d
```

The Renovate config is a strong heuristic, not gospel truth. Always explain the derivation in the report so the user can override.

### Priority 2: Superseded

**Signal:** Another open PR updates the same dependency group on the same base branch to a higher version.

**Action:** Close the older PR with comment referencing the newer one.

**Detection rules:**
1. Match on `(repo, base_branch, dependency_group)`:
   - Extract the dependency group from the **PR title** (preferred) or Renovate head branch name if available
   - From titles: "Update go modules ..." → `go-modules`, "Update module github.com/go-git/go-billy/v5 ..." → `go-billy`, "Update GitHub Actions ..." → `github-actions`
   - **Disambiguation:** Match the full dependency name, not substrings. `golang` (Go compiler) and `golangci-lint` (linter) are different groups. `go-git` and `go-billy` are different groups even though both are go-git org packages.
2. Compare versions from PR titles:
   - `(patch)` < `(minor)` < `(major)`
   - Explicit versions like `v5.8.0` < `v5.9.0` — use semver comparison
3. Tie-breaking: if versions can't be compared, the older PR (by `createdAt`) is superseded

**Konflux PRs:** `red-hat-konflux` may use different branch naming. If a Konflux PR can't be matched to a Renovate branch pattern, skip superseded detection for that PR — it falls through to a lower category.

### Priority 3: Security Update

**Signal:** Title contains `[SECURITY]` (case-insensitive — some repos like `go-gather` use lowercase `[security]`), or PR has a `security` label.

**Action:** Approve + enable auto-merge.

**CI reclassification:** If a security PR has failing CI for 7+ days, reclassify it as "Needs review" (Priority 8) with reason "Security update with CI failing {age} days — requires manual investigation". Use `age_days` (from `createdAt`) as a proxy for CI failure duration.

### Priority 4: Go Version Bump

**Signal:** PR title matches any of:
- `Update dependency golang to ...`
- `Update docker.io/library/golang Docker tag to ...`
- `Update registry.access.redhat.com/ubi9/go-toolset ...`
- `Update go toolchain directive to ...`
- `Update go version ...`
- `fix(deps): update go version ...`

**Action:** Verify container image availability, then flag for manual review with verification results.

**Verification procedure:**

1. Fetch the PR's changed files:
```bash
gh pr diff <NUMBER> --repo <REPO> --name-only
```

2. Classify the risk:
   - **Dockerfile/Containerfile changes** → Higher risk. Must verify container image exists.
   - **go.mod/go.sum only** → Lower risk. CI uses `actions/setup-go`.
   - **Both** → Treat as higher risk.

3. If Dockerfile changes, read the diff to find the target image:
```bash
gh pr diff <NUMBER> --repo <REPO>
```
   Look for `FROM` lines referencing `golang` or `go-toolset` images.

4. Verify image availability:
```bash
# For Red Hat registry
skopeo inspect docker://registry.access.redhat.com/ubi9/go-toolset:<version> 2>&1

# For Docker Hub
skopeo inspect docker://docker.io/library/golang:<version> 2>&1
```

5. Report result:
   - Exit 0 → `✅ Image verified`
   - "manifest unknown" or "not found" → `❌ Image not available`
   - Connection/auth error → `⚠️ Verification failed (registry unreachable)`

**If `skopeo` is not installed:** Log a warning and skip verification. Flag all Go version PRs as "verification skipped — skopeo not available" in the report.

### Priority 5: Major Version Bump

**Signal:** Title starts with `🚨` or contains `(major)`, or PR has a `major` label.

**Action:** Flag for manual review.

### Priority 6: Routine Patch/Minor

**Signal:** Title contains `(patch)` or `(minor)`, doesn't match any higher-priority category, and CI has NOT been failing for 7+ days.

**Action:** Approve + enable auto-merge. CI status is also re-checked at action time (in the act phase).

**CI reclassification:** If a PR would be routine but has failing CI for 7+ days, reclassify it as "Needs review" (Priority 8) with reason "CI failing, PR open {age} days". Use `age_days` as a proxy for CI failure duration.

### Priority 7: Stale

**Signal:** PR has been open for 120+ days (based on `createdAt`). Use age as the primary signal — checking for recent commits or reviews is optional and rarely changes the outcome for PRs this old.

**Action:** Recommend close. Renovate will re-create the PR with the latest version after closure.

### Priority 8: Needs Review

**Signal:** Everything that doesn't match categories 1-7.

**Action:** Present to user for manual decision.

## Cascade Detection

PRs on the same `(repo, base_branch)` that update the same dependency ecosystem will merge sequentially — each triggering a rebase + CI cycle for the next.

**Ecosystem taxonomy:**
- `go-modules`: PRs updating Go module dependencies (titles containing "go modules", "module github.com/...")
- `go-version`: PRs updating Go version, toolchain, or Go Docker images
- `github-actions`: PRs updating GitHub Actions (titles containing "GitHub Actions", action names)
- `docker-images`: PRs updating Docker/container image digests or tags
- `npm`: PRs updating npm/Node.js dependencies
- `konflux`: PRs updating Konflux references or RPM lockfiles
- `other`: Everything else

**Detection:** Group PRs by `(repo, base_branch, ecosystem)`. Groups with 2+ PRs are cascade groups.

**Recommended merge order within a cascade:** Security updates first, then patches, then minor, then major. Within the same update type, smaller PRs first.

## API Constraints

**`gh search prs` does not support `headRefName` or `baseRefName` fields.** Extract the base branch from:
1. **Labels (primary):** Renovate adds `{{baseBranch}}` as a label (e.g., `main`, `release-v0.8`)
2. **Title parenthetical (fallback):** e.g., `(release-v0.8)` at the end of the title

**Konflux author search may fail.** The `red-hat-konflux` bot account cannot always be searched via `--author`. Fall back to label-based search or skip with a warning.

**CI status fetching:** Only fetch CI for security and routine PRs (the categories needing CI reclassification). Do not fetch CI for all PRs — it's unnecessary API overhead.

## Report Location

Reports are written under `.conforma/reports/` in the current project directory:
- `.conforma/reports/renovate-triage-{YYYY-MM-DD}.json` — structured data for the `renovate-act` skill.
- `.conforma/reports/renovate-triage-{YYYY-MM-DD}.md` — human-readable report.

This directory is gitignored. By default, the `renovate-act` skill reads the latest JSON from this directory; a user-provided report path may point elsewhere.

## Close Comment Templates

**Abandoned branch:**
> Closed by automated triage: this PR targets branch `{branch}` which is no longer actively maintained. If this update is still needed, please open a new PR targeting an active branch (main, release-v0.7, or release-v0.8).

**Superseded:**
> Closed by automated triage: this PR has been superseded by #{newer_pr} which updates to a higher version of the same dependency group.

**Stale:**
> Closed by automated triage: this PR has been open for {age} days with no activity. If this dependency update is still needed, Renovate will re-create a fresh PR with the latest version.
