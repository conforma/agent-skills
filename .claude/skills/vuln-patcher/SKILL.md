---
name: vuln-patcher
description: Read Conforma vulnerability tickets, classify remediation, and prepare verified release patches for UBI RPM or Go-module fixes. Use when given a Jira vulnerability URL or engineering errata reference.
---

# Prepare a Conforma vulnerability patch

Provide a Jira browse URL or an engineering errata reference, for example:

```text
https://redhat.atlassian.net/browse/EC-2217
RHSA 172528
```

The Jira issue or complete pasted errata text is the source for the vulnerability, advisory, affected component, fixed version, and release scope. Do not infer package or module versions from an issue key or title.

This skill is written to the Agent Skills format and does not depend on a specific agent harness, tool name, or personal runtime environment variable. Use capabilities available in the user's environment. If a required capability is unavailable, stop and ask for the missing input rather than guessing or claiming verification.

The package includes `scripts/active-release-branches.sh` and `scripts/assess.sh`. In the command examples, `SKILL_DIR` means the absolute directory containing this file, and `CLI_REPO` means the verified CLI checkout. Resolve each path from the loaded skill and user input; never assume the shell working directory is either directory.

## Supported remediation classes

This workflow supports two concrete fix classes:

1. **UBI RPM:** The advisory names an exact RPM NVR. The fix is a pinned `ubi-minimal` digest update in the Conforma CLI image branches.
2. **Go module:** The advisory names a Go module and fixed version. The fix is a dependency update in affected release branches, followed by source, test, and image-revision verification.

For other source-code, product, configuration, or image vulnerabilities, classify the issue and return a remediation handoff. Do not invent a patch workflow or apply an unrelated UBI update.

## Inputs

| Input | Required | Default | Example |
|---|---:|---|---|
| Jira browse URL or RHSA reference | yes | none; ask if absent | `https://redhat.atlassian.net/browse/EC-2217` or `RHSA 172528` |
| Conforma CLI checkout | yes for patch work | use a verified checkout supplied by the user; otherwise ask whether to provide a path or authorize a clone of their personal fork | `/work/cli` |
| Release scope | confirm | current Pyxis releases plus `main` | `release-v0.7`, `release-v0.8` |
| Registry authentication | as needed | existing host login | `podman login registry.redhat.io` |

## CLI checkout and fork

Before local patch work, resolve a writable Conforma CLI checkout. If the user has not supplied a path and no valid checkout is already available, ask:

> Do you want to provide the path to an existing `conforma/cli` checkout, or authorize me to clone it? I expect your personal fork as `origin` and the Conforma CLI repository as `upstream`.

If the user provides a checkout path, verify that it is the Conforma CLI repository and inspect its remotes. If the user authorizes a clone:

- Use a verified personal fork URL as `origin`; do not guess the fork URL from a username.
- Use a writable task workspace for the clone. If no suitable destination is available, ask the user where to put it.
- Set or verify `upstream` points to `https://github.com/conforma/cli.git` or its canonical SSH equivalent.
- Do not clone the upstream repository as the user's writable `origin`.

If the authenticated environment can identify a fork, confirm that it is a fork of `conforma/cli` owned by the current user before using it. Otherwise ask the user for the exact fork URL. Never push directly to the upstream repository.

After selecting a checkout, use its absolute path as `CLI_REPO` in the command examples, or substitute the path directly. Do not proceed with branch work until the checkout and remotes are unambiguous.

## Input normalization and advisory handoff

Accept a Jira browse URL or an engineering errata reference. Normalize case, whitespace, and separators for numeric engineering references, for example:

```text
RHSA 172528
rhsa    172528
RHSA-172528
```

For an engineering number, construct:

```text
https://errata.engineering.redhat.com/errata/show_text/<number>
```

Show that URL to the user, ask them to visit it and paste the complete page, then stop and wait. Continue normal intake when the pasted content arrives. Do not claim to have read the page if the network blocks it.

Recognize published advisory identifiers such as `RHSA-2026:69126` and `RHSA-2026:67910-02` when they appear in Jira or pasted advisory content. Those identifiers are evidence to record, but they are not engineering errata numbers. If the only input is a published advisory ID, ask the user for the corresponding engineering errata number or URL rather than guessing a `show_text` path.

## Jira intake

1. Validate the URL host and extract the issue key from `/browse/<PROJECT>-<number>`. Reject non-browse URLs or missing issue keys.
2. Use an authenticated Jira read capability available in the current environment to fetch the issue, comments, attachments, links, and relevant fields. Request the full issue and complete comments in a readable format. Do not assume a particular connector or tool name.
3. Follow remote issue links when they point to an advisory, CVE record, release tracker, or related Jira issue. Read linked Jira issues as needed.
4. Read the complete issue and comments before deciding. Jira descriptions may be empty; use linked advisory data and comments as evidence. If Jira access fails, report the failed read; if required evidence is missing or truncated, ask the user for the complete issue description, comments, and linked advisory evidence.
5. Extract and record:
   - Jira key and URL
   - CVE, RHSA, or other advisory identifier
   - affected component and artifact
   - exact fixed RPM NVR, or Go module and fixed version
   - affected product releases and image tags
   - links and comments supporting the fix
6. Do not edit, comment on, transition, or otherwise write to Jira.

## Scope and repository preflight

Resolve and verify `CLI_REPO` before mutation:

- Verify `origin` is the user's personal fork and `upstream` is the intended Conforma repository by inspecting `git remote -v`.
- Require a clean worktree.
- Check `git`, `go`, `podman`, `skopeo`, `rpm`, `rpmdev-vercmp`, `jq`, `yq`, and `curl` as required by the selected remediation class.
- For RPM assessment, the bundled assessor downloads `current-release-tags.sh` and `rpm-version-checker.sh` from `https://raw.githubusercontent.com/conforma/hacks/main/` into a temporary directory and removes them on exit. No `conforma/hacks` checkout is needed.
- Fetch upstream remote-tracking refs with `git fetch upstream --prune`.
- Run the bundled release-branch helper on every invocation. It fetches the current Pyxis configuration and extracts the `rhtas/ec-rhel9` content-stream tags:

  ```bash
  bash "$SKILL_DIR/scripts/active-release-branches.sh" --repo-dir "$CLI_REPO"
  ```

- Map each Pyxis tag `X.Y` to `upstream/release-vX.Y`, verify that the ref exists, and always include `upstream/main`.
- If the Jira/advisory does not specify releases, use every branch returned by Pyxis plus `main`. Never use a cached or hard-coded release list.
- If the Jira/advisory specifies a narrower scope, present the dynamic default and ask the user to confirm or trim it.
- For RPM assessment, compare the Pyxis tags with the tags returned by the downloaded `current-release-tags.sh`; stop if they differ so the checker cannot assess a stale release set.

The release source is checked on every invocation from:

```text
https://gitlab.cee.redhat.com/releng/pyxis-repo-configs/-/raw/main/products/rhtas/rhtas.yaml
```

The bundled `scripts/active-release-branches.sh` helper prints `main` and the current `release-vX.Y` branches derived from Pyxis, verifies the upstream refs, and fails if the configuration cannot be read. It must not silently fall back to a previous result or repository branches.

Stop on a Pyxis read failure, ambiguous fork/upstream relationship, dirty worktree, missing release ref, or unresolved release mapping.

## Classify the remediation

### RPM/UBI

Require the exact RPM NVR from the advisory Builds list. Do not use a package name or a version copied from a different RHEL point-release stream.

Run the bundled assessor:

```bash
bash "$SKILL_DIR/scripts/assess.sh" \
  --repo-dir "$CLI_REPO" \
  --rpm-nvr "$TARGET_NVR"
```

The assessor must report separately:

1. Whether `registry.access.redhat.com/ubi9/ubi-minimal:latest` contains the target NVR.
2. Which in-scope RHTAS and Conforma images contain the target NVR.
3. Which images still carry an older package.
4. The digest and creation date for every checked image.

The UBI gate must pass before a digest bump is possible. A pinned product image can remain vulnerable after UBI latest is fixed. A source-RPM match such as `coreutils-single` satisfying a target named `coreutils` is valid evidence.

Use the checker's actual `rpmdev-vercmp` results:

- `0`: equal, satisfied
- `11`: installed version is older, upgrade needed
- `12`: installed version is newer, satisfied

If UBI latest lacks the target, stop and report that the base-image rebuild is not available yet. If a package is missing, check sibling subpackages and the source RPM before declaring failure.

For each confirmed branch whose image is stale:

1. Create a branch from current `upstream/<base>`.
2. From the repository root, run that branch's `hack/ubi-base-image-bump.sh --no-commit`. Do not use its default committing form because it does not include the required commit body.
3. Verify the new Dockerfile digest is the UBI digest that passed the gate.
4. Record the old and new digests and every RPM old/new pair from the staged diff.
5. Create the commit with the mandatory UBI commit template below.
6. Inspect the commit and changed files.
7. Stop before pushing; show the exact push command and rendered PR metadata for approval.

### Go module

Require the module path and fixed version from the advisory or authoritative linked evidence. Record the minimum fixed version separately from the version selected for the release.

For each affected release branch:

1. Inspect `go.mod`, `tools/go.mod`, and the relevant `go.sum` entries at the current upstream tip.
2. If the selected module version is already at or above the fixed version, inspect the published image's `org.opencontainers.image.revision` label and verify it matches the release revision containing that dependency update. Report the ticket as already fixed for that release; do not create a no-op patch.
3. Otherwise create a branch from current `upstream/<base>` and update the module with Go tooling. In the repository root, use:

   ```bash
   go get "$MODULE@$SELECTED_VERSION"
   go mod tidy
   ```

   If `tools/go.mod` exists, run the equivalent commands from `tools/`. Keep the change limited to the named module and generated module files.
4. Run `go mod verify`, the repository's focused tests, and `go test ./...`. If `tools/go.mod` exists, run its module verification and tests too. Do not skip failures.
5. Reinspect `go.mod`, `tools/go.mod`, and the image/source evidence before reporting the release fixed.
6. Create the commit with the mandatory Go-module commit template below.
7. Stop before pushing; show the exact push command and rendered PR metadata for approval.

A Go-module version in source is not by itself proof that a published image contains it. Correlate the image source-revision label with the inspected release commit, or report that artifact verification is unavailable.

## Commit and pull request templates

Use these templates for every prepared patch. Pull request 3570 is the canonical UBI example:
https://github.com/conforma/cli/pull/3570. Replace only the angle-bracket placeholders.

Set `<base>` to the affected base branch label, such as `main` or `release-v0.9`, not the temporary patch branch name. If a Jira browse URL is available, include exactly one `Ref: <JIRA_BROWSE_URL>` line in both the commit message and PR body; otherwise omit it. Do not include RHSA, engineering errata, advisory, or other non-Jira links in either artifact.

### UBI/RPM

Commit message:

```text
chore(deps): Update ubi-minimal base image

Old digest: sha256:<OLD_DIGEST>
New digest: sha256:<NEW_DIGEST>

RPM changes:

- <OLD_RPM_NVR>
+ <NEW_RPM_NVR>

Ref: <JIRA_BROWSE_URL>
```

PR title:

```text
chore(deps): Update ubi-minimal base image (<base>)
```

PR body:

````markdown
Update ubi-minimal base image to latest digest.

Old digest: `sha256:<OLD_DIGEST>`
New digest: `sha256:<NEW_DIGEST>`

### RPM changes

```diff
- <OLD_RPM_NVR>
+ <NEW_RPM_NVR>
```

Ref: <JIRA_BROWSE_URL>
````

Include only RPMs that changed, with one `-`/`+` pair per RPM.

### Go module

Use the same structure for module patches, replacing the dependency-specific values as follows.

Commit message:

```text
chore(deps): Update <DEPENDENCY>

Old version: <OLD_VERSION>
New version: <NEW_VERSION>

Go module changes:

- <MODULE> <OLD_VERSION>
+ <MODULE> <NEW_VERSION>

Ref: <JIRA_BROWSE_URL>
```

PR title:

```text
chore(deps): Update <DEPENDENCY> (<base>)
```

PR body:

````markdown
Update <DEPENDENCY> to `<NEW_VERSION>`.

Old version: `<OLD_VERSION>`
New version: `<NEW_VERSION>`

### Go module changes

```diff
- <MODULE> <OLD_VERSION>
+ <MODULE> <NEW_VERSION>
```

Ref: <JIRA_BROWSE_URL>
````

Before reporting a patch as prepared, render and inspect all three artifacts: the commit message, PR title, and PR body. Keep required lines single-line. Do not push or create the PR without approval.

## Output

Return a Jira-linked report with these sections:

1. **Ticket:** key, URL, status, advisory/CVE, and evidence sources.
2. **Classification:** `rpm/ubi`, `go-module`, `unsupported`, or `blocked`.
3. **Release matrix:**

   | Release/image | Current evidence | In scope | Action |
   |---|---|---:|---|
   | ... | fixed version, digest, or source revision | yes/no | fixed / patch / blocked |

4. **Changes:** branch, files, commit, and test results for each prepared patch.
5. **Handoff:** exact push commands, with push and PR creation pending approval.
6. **Risks:** missing advisory data, stale artifact, registry failure, or unsupported remediation.

If no patch is needed, say why for every affected release. If the issue is unsupported, provide the extracted evidence and next owner/action rather than claiming success.

## Failure and safety rules

- Missing or malformed input: ask for a Jira `/browse/KEY-123` URL or an engineering `RHSA <number>` reference.
- Published advisory ID without an engineering errata number: ask for the engineering number or URL; do not guess the mapping.
- Errata page not pasted or truncated: stop and request the complete contents.
- Jira access failure or truncated issue/comments: stop and request complete inputs.
- Missing exact fixed NVR/module version: stop and ask for advisory Builds or equivalent authoritative evidence.
- No checkout available: ask whether the user will provide an existing checkout path or authorize a clone of their personal fork; never guess the fork URL.
- Non-RPM/non-Go vulnerability: classify and hand off; do not guess.
- UBI latest lacks an RPM fix: stop; do not bump a digest.
- Registry authentication failure: request host login and report any UBI-only evidence separately.
- Download or execution failure for either `conforma/hacks` assessor script: stop and report the exact URL and error.
- Pyxis configuration read or parse failure: stop; never use a stale release list.
- Dirty worktree or ambiguous remotes: stop before branch work.
- Already-fixed release: provide evidence and do not force a commit.
- Test or artifact verification failure: report the failure; do not call the release fixed.
- Push, PR, Jira comment, Jira transition, or other external write: show the pending operation and wait for explicit approval.
