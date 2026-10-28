---
name: generate-policy
description: Generate complete Conforma validation setup for container images. Creates policy rules, tests, configuration, and ready-to-run commands. Users don't need to know Rego, Conforma, or SBOM formats.
---

# Generate Policy Skill

Help users validate container images with Conforma policies. The user doesn't need to know anything about Rego, Conforma, SBOMs, or policy configuration - this skill handles everything.

## What the User Provides

| Input | Description | Example |
|-------|-------------|---------|
| Policy set name | Descriptive name for the policy set | `release_policies` |
| Image reference | Container image to validate (optional) | `quay.io/org/app@sha256:abc123...` |
| Public key | Cosign public key file (optional) | `cosign.pub` |
| Validation requirements | What they want to check | "Ensure npm packages come from registry.npmjs.org" |
| Builder IDs | Allowed build service identifiers (SLSA provenance) | `["https://tekton.dev/chains/v2"]` |
| Source repository | Expected source repo for provenance correlation (SLSA provenance) | `https://github.com/org/repo` |
| Build type | Expected build system type (SLSA provenance) | `"tekton.dev/v1/PipelineRun"` |

Collect the inputs in this section, especially the validation requirements and any required SLSA fields. Ask the user about missing information before generating files.

## What to Generate

When a user requests policy validation, generate these artifacts:

| Artifact | Description |
|----------|-------------|
| Policy rule (`.rego`) | Standalone Rego v1 rule |
| Test file (`_test.rego`) | Comprehensive tests for the rule |
| Policy config (`policy.yaml`) | Conforma configuration referencing data files |
| Data file (`data/*.yaml`) | Rule data configuration (e.g., allowed registries) |
| Conforma command | Ready-to-run `ec validate image` command |
| Instructions | Clear next steps for the user |

## Workflow

1. **Gather requirements** - Ask what the user wants to validate
2. **Prompt for required inputs** - See domain references for what to ask (e.g., `allowed_package_sources` for SBOM rules)
3. **Generate artifacts** - Create files with directory matching package name (for Rego lint compliance)
4. **VERIFY: Run OPA tests** - Run `ec opa test ./policy -v --fail-on-empty` and ensure ALL tests pass
5. **VERIFY: Run EC validation** - If image provided, run `ec validate image` and verify expected results
6. **Report results** - Only after verification passes, provide the Conforma command and next steps

---

## ⚠️ MANDATORY VERIFICATION STEPS ⚠️

**YOU ARE NOT DONE UNTIL THESE STEPS PASS. DO NOT REPORT SUCCESS TO THE USER UNTIL VERIFICATION IS COMPLETE.**

### Step 1: Run OPA Tests (REQUIRED)

After creating all Rego files, you MUST run the tests:

```bash
cd <policy_set_directory>
ec opa test ./policy -v --fail-on-empty
```

For SBOM rules, tests must mock `data.lib.sbom.spdx_sboms` or
`data.lib.sbom.cyclonedx_sboms` directly so they do not fetch OCI blobs.
`--fail-on-empty` prevents a missing or ignored test file from appearing successful.

**Requirements:**
- ALL tests must pass (exit code 0)
- If tests fail, FIX the code and re-run until they pass
- DO NOT skip this step or report success if tests fail

### Step 2: Run EC Validation (REQUIRED if image provided)

If the user provided an image reference, you MUST validate the policy against it:

```bash
cd <policy_set_directory>
ec validate image \
  --image <IMAGE_REFERENCE> \
  --policy policy.yaml \
  --output text \
  --info
```

Add `--public-key cosign.pub` when the user supplied a public key. Choose
signature and Rekor options to match the user's verification setup; use
`--ignore-rekor` only when intentionally skipping transparency log checks.

**Requirements:**
- Verify the output matches expectations:
  - If the policy should FAIL (e.g., image from wrong registry), confirm violations appear
  - If the policy should PASS, confirm no violations
- If results don't match expectations, FIX the policy and re-run
- DO NOT skip this step or report success if results are unexpected

### Step 3: Debug Unexpected Results

If validation doesn't produce expected results:
1. Extract and examine the actual SBOM data from the image
2. Compare SBOM structure to what the policy expects
3. Adjust the policy to match the actual data structure
4. Re-run validation to confirm
5. Repeat until expected results are achieved

---

## Directory Structure

For Rego lint compliance, directory path must match package name. Use a descriptive top-level directory name, with rules organized under a `policy/` subdirectory:

```
<descriptive_name>/                # e.g., release_policies, sbom_validation
├── policy.yaml                    # Conforma configuration
├── cosign.pub                     # Public key (if provided)
├── data/                          # Rule data files (referenced from policy.yaml)
│   └── <rule_data>.yaml           # YAML file with rule_data configuration
└── policy/                        # Contains all rule directories
    ├── lib/                       # Shared library (required for SBOM rules)
    │   └── sbom.rego              # SBOM access library
    └── <rule_name>/               # Directory matches package name
        ├── <rule_name>.rego       # package <rule_name>
        └── <rule_name>_test.rego  # package <rule_name>_test
```

**Example** - For release policies with a `package_sources` rule:
```
release_policies/
├── policy.yaml
├── cosign.pub
├── data/
│   └── allowed_sources.yaml           # rule_data for allowed package sources
└── policy/
    ├── lib/
    │   └── sbom.rego                  # package lib.sbom
    └── package_sources/
        ├── package_sources.rego       # package package_sources
        └── package_sources_test.rego  # package package_sources_test
```

## SBOM Access Library (Required for SBOM Rules)

**IMPORTANT**: SBOMs are NOT directly embedded in attestations. In Konflux/RHTAP builds, the SBOM is stored as an OCI blob and referenced from the SLSA provenance attestation. The library fetches these using `ec.oci.blob()`.

For any rule that validates SBOM data, you MUST:

1. **Create the SBOM library** at `policy/lib/sbom.rego` using the [SBOM Library Template](templates/lib-sbom.rego)

2. **Include the lib and data in policy.yaml**:
   ```yaml
   sources:
     - name: my-rules
       data:
         - ./data                # Rule data files
       policy:
         - ./policy/lib          # SBOM access library
         - ./policy/my_rule
   ```

3. **Import and use in your rules**:
   ```rego
   import data.lib.sbom

   deny contains result if {
       some s in sbom.spdx_sboms      # Fetches from OCI blobs via ec.oci.blob()
       some pkg in s.packages
       # validation logic
   }
   ```

4. **Mock the SBOM data in tests** (CRITICAL):
   ```rego
   test_my_rule if {
       sboms := [_mock_spdx_sbom(packages)]

       count(my_rule.deny) == 1
           with data.lib.sbom.spdx_sboms as sboms   # MUST mock - bypasses ec.oci.blob()
   }
   ```

**How it works:**
- The library uses `ec.oci.blob()` to fetch SBOMs from OCI blobs referenced in SLSA provenance
- Tests MUST mock `data.lib.sbom.spdx_sboms` or `data.lib.sbom.cyclonedx_sboms` directly to avoid fetching blobs
- At EC runtime, the library fetches real SBOMs from OCI registries

**Testing Note**: Keep SBOM tests deterministic by mocking the relevant SBOM value in `data.lib.sbom`. The OPA test command loads the library along with the rules and tests.

**DO NOT** iterate directly over `input.attestations` for SBOM data - always use the library.

## SLSA Provenance Access (For Provenance Rules)

**IMPORTANT**: SLSA provenance rules do NOT use the SBOM library (`policy/lib/sbom.rego`) and do not require a local `policy/lib/` directory. Instead, they use runtime-provided helpers from `data.lib` to access provenance attestations.

For any rule that validates SLSA provenance data:

1. **Use `data.lib` helpers to access attestations** — `import data.lib` and use `lib.slsa_provenance_attestations`, `lib.pipelinerun_attestations`, and `lib.attestation_materials(att)` for version-agnostic access. See [SLSA Quick Reference](#slsa-quick-reference) for patterns.

2. **Define a local `_builder_id` helper** — `data.lib` does not provide a cross-version builder ID helper. See [SLSA Quick Reference](#slsa-quick-reference) for the dual-version pattern.

3. **No local library directory needed** — directory structure is simpler than SBOM rules:
   ```text
   build_policies/
   ├── policy.yaml
   ├── data/
   │   └── allowed_builders.yaml
   └── policy/
       └── builder_verification/
           ├── builder_verification.rego
           └── builder_verification_test.rego
   ```

4. **Policy config** — no library path entry needed:
   ```yaml
   sources:
     - name: my-rules
       data:
         - ./data
       policy:
         - ./policy/builder_verification    # No ./policy/lib needed
   ```

### Required Inputs for SLSA Provenance Rules

When generating SLSA provenance rules, prompt the user for these inputs. See [SLSA Provenance Structure Reference](reference/slsa-provenance-structure.md) for full details.

| Rule Type | Required Input | Description | Example |
|-----------|---------------|-------------|---------|
| Builder ID validation | `allowed_builder_ids` | Accepted builder identifiers | `["https://tekton.dev/chains/v2"]` |
| Attestation type validation | `allowed_predicate_types` | Accepted in-toto predicate types | `["https://slsa.dev/provenance/v1"]` |
| Build type validation | `allowed_provenance_build_types` | Accepted build type strings | `["tekton.dev/v1/PipelineRun"]` |
| Source correlation | `supported_vcs` | Supported VCS types | `["git"]` |
| Source correlation | `supported_digests` | Supported digest algorithms | `["sha1", "gitCommit", "sha256"]` |
| Pipeline run params | `pipeline_run_params` | Expected PipelineRun parameter names | `["git-repo", "git-revision", "output-image"]` |

## Conforma Command Template

Run from within the policy set directory (e.g., `cd release_policies`):

```bash
ec validate image \
  --image <IMAGE_REFERENCE> \
  --policy policy.yaml \
  --output text \
  --info
```

Add `--public-key cosign.pub` when the user supplied a public key. Adjust
the signature and Rekor options to match the user's verification setup.

**Important**: The `policy.yaml` references rules with relative paths (`./policy/<rule_name>`), so the command must be run from the policy set directory where `policy.yaml` is located.

---

## Reference Documents

### Core References

- [Rego Patterns Reference](reference/rego-patterns.md) - Rego v1 syntax, metadata format, result construction
- [Test Patterns Reference](reference/test-patterns.md) - OPA testing, mock helpers, required test cases
- [Policy Configuration Reference](reference/policy-config.md) - Policy config structure, ruleData, collections

### Domain-Specific References

#### SBOM Validation
- [SBOM Structure Reference](reference/sbom-structure.md) - SPDX/CycloneDX paths, required inputs
- [SPDX 2.3 Schema](reference/spdx-schema.json), [CycloneDX 1.5 Schema](reference/cyclonedx-schema.json)

#### SLSA Provenance
- [SLSA Provenance Structure Reference](reference/slsa-provenance-structure.md) - v1.0/v0.2 field paths, required inputs, dual-version patterns

### Templates

- [Rule Template](templates/rule.rego) - Generic Rego v1 rule
- [Test Template](templates/test.rego) - Test file with mock helpers
- [SBOM Rule Template](templates/sbom-rule.rego) - Package source validation example
- [SBOM Library Template](templates/lib-sbom.rego) - Standalone SBOM access library (REQUIRED for SBOM rules)
- [Policy Config Template](templates/policy.yaml) - Conforma policy configuration
- [Rule Data Template](templates/rule-data.yaml) - Data file for rule configuration

---

## Quick References

### Rego v1 Essentials (SBOM Rule)

```rego
package <rule_name>

import rego.v1

import data.lib.sbom  # Use the SBOM library

# METADATA
# title: Rule Title
# description: >-
#   What the rule checks.
# custom:
#   short_name: rule_name
#   failure_msg: "Error: %s"
#   solution: How to fix.
deny contains result if {
    # Use sbom.spdx_sboms or sbom.cyclonedx_sboms (NOT input.attestations)
    some s in sbom.spdx_sboms
    some pkg in s.packages

    # validation logic

    result := {
        "code": "<rule_name>.rule_name",
        "msg": sprintf("Error: %s", [value]),
        "severity": "failure",
    }
}
```

### Policy Config Essentials

```yaml
name: <policy_name>
description: <description>
sources:
  - name: <source_name>
    data:
      - ./data                  # Directory containing rule_data YAML files
    policy:
      - ./policy/lib            # SBOM library (required for SBOM rules)
      - ./policy/<rule_name>    # Reference each rule directory under policy/
    config:
      include:
        - "<rule_name>.short_name"
```

### Data File Format

Rule data is stored in separate YAML files under the `data/` directory:

```yaml
# data/allowed_sources.yaml
rule_data:
  allowed_package_sources:
    - "^https://registry\\.npmjs\\.org/"
    - "^https://proxy\\.golang\\.org/"
```

The data is accessed in Rego rules via `data.rule_data`:

```rego
allowed := object.get(data.rule_data, "allowed_package_sources", [])
```

### SBOM Quick Reference

**Access SBOMs** (use `lib.sbom` - handles OCI blob fetching):
```rego
import data.lib.sbom

# SPDX SBOMs
some s in sbom.spdx_sboms
some pkg in s.packages

# CycloneDX SBOMs
some s in sbom.cyclonedx_sboms
some component in s.components
```

**SPDX Structure**:
- Packages: `s.packages`
- PURL: `pkg.externalRefs[].referenceLocator` where `referenceType == "purl"`
- License: `pkg.licenseDeclared`

**CycloneDX Structure**:
- Components: `s.components`
- PURL: `component.purl`
- Distribution URL: `component.externalReferences[].url` where `type == "distribution"`

### Rego v1 Essentials (SLSA Provenance Rule)

```rego
package <rule_name>

import rego.v1

import data.lib

# METADATA
# title: Rule Title
# description: >-
#   What the rule checks.
# custom:
#   short_name: rule_name
#   failure_msg: "Error: %s"
#   solution: How to fix.
deny contains result if {
    # Use runtime-provided helpers (NOT direct input.attestations)
    some att in lib.pipelinerun_attestations

    # Get builder ID (dual-version support)
    builder_id := _builder_id(att)

    # Validate against allowed list
    allowed_ids := object.get(data.rule_data, "allowed_builder_ids", [])
    not builder_id in allowed_ids

    result := {
        "code": "<rule_name>.rule_name",
        "msg": sprintf("Error: builder %s is not allowed", [builder_id]),
        "severity": "failure",
    }
}

# Helper: extract builder ID (v0.2 first, then v1.0)
_builder_id(att) := builder_id if {
    builder_id := att.statement.predicate.builder.id
} else := builder_id if {
    builder_id := att.statement.predicate.runDetails.builder.id
}
```

### SLSA Dual-Version Support

SLSA v1.0 and v0.2 use different field paths. Use helper functions for version-agnostic access:

| Data Element | v1.0 Path | v0.2 Path |
|-------------|-----------|-----------|
| Builder ID | `predicate.runDetails.builder.id` | `predicate.builder.id` |
| Build type | `predicate.buildDefinition.buildType` | `predicate.buildType` |
| Materials | `predicate.buildDefinition.resolvedDependencies` | `predicate.materials` |
| Build finished | `predicate.runDetails.metadata.finishedOn` | `predicate.metadata.buildFinishedOn` |

### SLSA Data File Format

```yaml
# data/allowed_builders.yaml
rule_data:
  allowed_builder_ids:
    - "https://tekton.dev/chains/v2"
  allowed_predicate_types:
    - "https://slsa.dev/provenance/v1"
    - "https://slsa.dev/provenance/v0.2"
```

The data is accessed in Rego rules via `data.rule_data`:

```rego
allowed_ids := object.get(data.rule_data, "allowed_builder_ids", [])
allowed_types := object.get(data.rule_data, "allowed_predicate_types", [])
```

### SLSA Quick Reference

**Access provenance attestations** (use `data.lib` helpers):
```rego
import data.lib

# All SLSA provenance (both v1.0 and v0.2)
some att in lib.slsa_provenance_attestations

# PipelineRun attestations only (latest per version)
some att in lib.pipelinerun_attestations
```

**Predicate type validation** (against configured allowlist):
```rego
allowed_types := object.get(data.rule_data, "allowed_predicate_types", [])
not att.statement.predicateType in allowed_types
```

**Builder ID** (local helper, dual-version):
```rego
_builder_id(att) := builder_id if {
    builder_id := att.statement.predicate.builder.id
} else := builder_id if {
    builder_id := att.statement.predicate.runDetails.builder.id
}
```

**Source materials** (use `lib.attestation_materials`):
```rego
materials := lib.attestation_materials(att)
some material in materials
startswith(material.uri, "git+")
```

**Build type** (dual-version):
```rego
_build_type(att) := att.statement.predicate.buildType if {
    att.statement.predicateType == "https://slsa.dev/provenance/v0.2"
} else := att.statement.predicate.buildDefinition.buildType
```

---

## Iterative Refinement

Users can refine generated policies through follow-up conversational requests. This workflow supports incremental changes without regenerating all artifacts from scratch.

### How It Works

1. **Initial generation** — Follow the standard workflow to generate all artifacts
2. **User requests a change** — e.g., "pin the builder to our Tekton instance", "add an exception for test builds", "tighten the allowed registries"
3. **Modify existing files** — Edit the generated `.rego`, `_test.rego`, and data files in place rather than regenerating from scratch
4. **Re-run verification** — After every refinement, re-run both verification steps:
   - `ec opa test ./policy -v --fail-on-empty` (OPA tests)
   - `ec validate image ...` (EC validation, if image provided)
5. **Report updated results** — Only report success after verification passes

### Guidelines

- **Preserve existing work** — Modify the specific rule, test, or data file affected by the request. Do not regenerate unrelated files.
- **Maintain test coverage** — When modifying a rule, update the corresponding tests to cover the new behavior. Add new test cases for exceptions or additional conditions.
- **Update data files** — If the refinement changes configuration values (e.g., adding a builder ID), update the data YAML file rather than hardcoding values in Rego.
- **Cumulative changes** — Each refinement builds on the previous state. Track all changes so verification reflects the full policy, not just the latest change.
