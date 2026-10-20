# Capture Context Reference — Quality Bar and Filter Criteria

This document is a reference for the capture-context skill. It contains examples of good and bad design doc entries, the full filter criteria, and common subsystem categories for the Conforma ecosystem.

## Good vs Bad Design Doc Entries

### Good: Explains WHY with the constraint that drives the design

From ec-cli's `internal/evaluator/DESIGN.md`:

> ## Filtering Happens Twice
>
> Pre-evaluation filtering selects which *packages* to load into OPA. Post-evaluation
> filtering decides which *results* to keep. Both use the same `PolicyResolver` instance
> so decisions are consistent. This two-pass design exists because OPA evaluates all
> rules in a loaded package — you can't selectively run individual rules within a
> package, only control which packages load.

**Why this is good:** States the design choice (two-pass filtering), then explains the constraint that makes it necessary (OPA evaluates all rules in a loaded package). An implementer reading this understands why they can't just filter at one level. The constraint isn't obvious from reading the code — you'd need to understand OPA's evaluation model.

### Good: Captures a non-obvious integration point

> ## Why VSAs Use DSSE Signing
>
> VSAs are wrapped in DSSE (Dead Simple Signing Envelope) with signature verification
> enabled by default. This was a deliberate security decision — unsigned VSAs would
> allow an attacker to forge validation results and skip policy enforcement. The signing
> key is the same key used for the original image validation.

**Why this is good:** The security rationale isn't visible in the code. Someone might reasonably think signing is optional or configurable. This doc prevents a future implementer from making signing optional "for convenience."

### Good: Documents a cross-repo connection

> ## How Task Bundles Reach Clusters
>
> Task definitions in conforma-tekton-catalog are pushed as OCI bundles to
> quay.io/konflux-ci/ on each merge to main. The ec-defaults ConfigMap in
> infra-deployments references these bundles by SHA. Updating a task requires:
> (1) merge to tekton-catalog, (2) get the new SHA from the bundle push CI step,
> (3) update the ConfigMap in infra-deployments. There's no automated promotion —
> the SHA update is a manual PR.

**Why this is good:** This operational knowledge spans three repos and involves a manual step. No single repo's code reveals the full pipeline. An LLM implementing a task update story would need all of this.

### Bad: Describes WHAT the code does

> ## Rule Filtering
>
> The system uses two policy resolvers: ECPolicyResolver and
> IncludeExcludePolicyResolver. ECPolicyResolver handles pipeline intention
> filtering. IncludeExcludePolicyResolver skips it. Filtering uses a scoring
> system defined in filters.go.

**Why this is bad:** You can learn all of this by reading `filters.go`. It describes structure without explaining why it exists. Removing this doc wouldn't leave anyone confused.

### Bad: Story-specific details

> ## EC-1806 Performance Fix
>
> We reduced memory usage by switching from conftest to direct OPA evaluation.
> The PR was reviewed by Simon. The benchmark showed a 40% improvement.

**Why this is bad:** References a specific story and PR. The useful knowledge ("why direct OPA instead of conftest") is buried under story metadata. The performance numbers will become stale. State the design rationale, not the project history.

### Bad: Already in AGENTS.md

> ## Building ec-cli
>
> Build with CGO_ENABLED=0 because the binary needs to run in scratch
> containers. Run `make build` to build, `make test` to test.

**Why this is bad:** Build commands belong in AGENTS.md. The CGO rationale could be a design doc entry if AGENTS.md only says "CGO_ENABLED=0 required" without explaining why — but in practice, AGENTS.md already covers this.

### Bad: Temporary state

> ## Current Migration Status
>
> As of Sprint 47, we're halfway through migrating from conftest to OPA.
> The old evaluator still exists but is deprecated. 3 of 5 callers have
> been migrated.

**Why this is bad:** This is a snapshot that rots immediately. The migration status changes every week. Put this in the Jira epic, not a design doc.

## Filter Criteria — Detailed

### Filter 1: Reusable

**Question:** Would another story touching this subsystem need this knowledge?

Pass examples:
- "The publishing pipeline involves three repos and a manual SHA update" — any story touching task publishing needs this
- "VSA signing is mandatory for security reasons" — anyone modifying VSA code should know this
- "OPA evaluates all rules in a loaded package" — fundamental constraint affecting all filtering work

Fail examples:
- "The story asked us to add a --verbose flag" — specific to one story
- "We chose to put the new test in evaluator_test.go" — obvious file placement
- "The PR had 3 review rounds" — project management, not design knowledge

### Filter 2: Non-obvious

**Question:** Can you derive this by reading the code?

Pass examples:
- Cross-repo workflows (no single repo reveals the full picture)
- Security rationale (the code shows WHAT is enforced, not WHY)
- Historical constraints ("we use two modules because the acceptance tests need different deps" — the go.mod doesn't explain WHY)

Fail examples:
- Function signatures and call chains (read the code)
- Directory structure (run `ls` or `tree`)
- Config file formats (the files are self-documenting or have schemas)
- Test patterns (follow existing tests)

### Filter 3: Stable

**Question:** Will this remain true for more than one sprint?

Pass examples:
- Architectural constraints ("OPA can't filter individual rules within a package")
- Security decisions ("VSAs must be signed")
- Integration protocols ("task bundles are published as OCI artifacts to quay.io")

Fail examples:
- Migration progress ("3 of 5 callers migrated")
- Sprint-specific workarounds ("temporarily pinned to v0.2 until upstream fixes the bug")
- Feature flags ("EC_USE_OPA=1 gates the new evaluator" — the flag will be removed)

## Boundary: Design Documents vs Repository Instructions

| Knowledge type | Where it goes |
|---------------|---------------|
| Build commands, test commands, lint rules | Repository agent instructions (for example, AGENTS.md) |
| Code conventions (naming, formatting, patterns) | Repository agent instructions (for example, AGENTS.md) |
| Review checklist items (effective_on dates, collection membership) | Repository agent instructions (for example, AGENTS.md) |
| Repo structure and file layout | Repository agent instructions (for example, AGENTS.md) |
| Why a subsystem is designed the way it is | design doc |
| Cross-repo operational knowledge | design doc |
| Security and architectural constraints | design doc |
| Integration points with external systems | design doc |
| Workspace-wide repo map and architecture | Repository instructions loaded by the current harness |
| Tool usage and workflow instructions | Harness-specific instructions or configuration |

When in doubt: if it tells you HOW to work in the repo, it's repository instructions. If it tells you WHY the code is the way it is, it's a design doc.

## Common Subsystem Categories for Conforma

These are areas where design docs are most likely to be valuable, based on the sprint triage patterns:

| Subsystem | Repos involved | Why docs would help |
|-----------|---------------|-------------------|
| Publishing pipeline | conforma-tekton-catalog, ec-cli, build-definitions | Multi-repo workflow with manual steps |
| Policy evaluation | ec-cli, ec-policies | OPA constraints, two-pass filtering, scoring |
| VSA (Verification Summary Attestation) | ec-cli | Security decisions, signing requirements, storage backends |
| CRD lifecycle | conforma-crds, ec-cli, infra-deployments | Generate/export/deploy chain across repos |
| Deployment & promotion | infra-deployments | ArgoCD sync model, overlay patterns, cluster topology |
| Task bundle management | conforma-tekton-catalog, build-definitions | OCI bundle format, versioning, SHA pinning |
| Release workflow | release-service-catalog | Tekton pipeline patterns, vault encryption, release gates |
| effective_on dates | ec-policies | Time-gating convention, rule data structure, migration windows |
| Exception mechanism | ec-policies, ec-cli | Config vs VolatileConfig exclusions, CRD fields, metadata flow |

This is not exhaustive. New subsystems will emerge as stories are implemented. Name design docs after whatever subsystem the knowledge belongs to.
