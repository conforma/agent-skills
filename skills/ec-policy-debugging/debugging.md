# EC Policy Debugging Reference

Guide for debugging Enterprise Contract policy violations by examining policy rules, metadata, and actual data.

## Prerequisites

Before debugging, set up your environment:

1. **From a Conforma log**: Follow the [ec-setup skill](../ec-setup/SKILL.md) to extract `policy.yaml`, `key.pub`, and `run.sh`.
2. **Pull policy source code**: If policy sources are OCI references, follow the policy-pull step in the [ec-setup skill](../ec-setup/SKILL.md).

## Quick Start

When you encounter a violation, first identify the failure evidence. Resolve any bundled helper paths relative to the linked skill file, not the current working directory.

1. **Get the violation code** from the log (e.g., `olm.unmapped_references`)
2. **Find the rule** in the policy source
3. **Read the metadata** to understand what it checks and how to fix it
4. **Read the tests** to see expected inputs
5. **Compare actual data** against expectations

## Accessing Policy Source Code

Policy source locations are defined in `policy.yaml` at `sources[].policy`.

### Determine policy type
```yaml
# In policy.yaml:
sources:
  - name: Release Policies
    policy:
      - /path/to/local/policy/release              # Local path → access directly
      - oci::quay.io/example/ec-release-policy:tag # OCI reference → must pull first
```

### Local paths
Access rule files directly at the specified path.

### OCI references
OCI references (starting with `oci::`) are conftest bundles that must be downloaded first.

```bash
# Pull the policy bundle
conftest pull --policy ./policies <OCI_URL>

# Example:
conftest pull --policy ./policies oci::quay.io/enterprise-contract/ec-release-policy:konflux

# Result:
./policies/
├── release/           # Policy rules by package
│   ├── olm/
│   ├── rpm_packages/
│   └── ...
└── lib/               # Shared libraries
```

See the policy-pull step in the [ec-setup skill](../ec-setup/SKILL.md) for details.

## Finding a Rule from Violation Code

Violation codes follow the pattern `<package>.<short_name>`.

```bash
# Example: olm.unmapped_references
# Package: olm
# Short name: unmapped_references

# Find the rule file
ls policy/release/olm/

# Search for the short_name in metadata
grep -r "short_name: unmapped_references" policy/release/
```

### Policy file structure
```
policy/release/<PACKAGE>/
├── <package>.rego          # Rule definitions
└── <package>_test.rego     # Tests showing expected behavior
```

## Reading Rule Metadata

Every rule has a METADATA block that explains what it does and how to fix violations.

```bash
# Extract metadata for a specific rule
# Look for the METADATA comment block above the deny/warn rule
```

### Metadata fields

| Field | Purpose |
|-------|---------|
| `title` | Human-readable rule name |
| `description` | What the rule checks and why |
| `custom.short_name` | The violation code suffix |
| `custom.failure_msg` | Message template shown in violations |
| `custom.solution` | How to fix the violation |
| `custom.collections` | Which policy collections include this rule |

### Example: Reading rule metadata
```bash
# Find and display the metadata block for a rule
awk '/^# METADATA/,/^deny contains|^warn contains/' policy/release/olm/olm.rego
```

## Reading Rule Tests

Tests show exactly what inputs trigger violations and what inputs pass.

```bash
# Find tests for a specific rule
grep -A 20 "test.*unmapped" policy/release/olm/olm_test.rego
```

### What to look for in tests:
- **Mock data structure** - Shows expected format of attestations, SBOMs
- **Success cases** - What valid data looks like
- **Failure cases** - What triggers violations
- **Edge cases** - Special handling for specific scenarios

## Accessing Actual Data

### Download attestation
```bash
cosign download attestation <IMAGE_REF> | jq -r .payload | base64 -d | jq
```

### Download SBOM (attached to image)
```bash
cosign download sbom <IMAGE_REF>
```

### Download SBOM blob (from SBOM_BLOB_URL in attestation)
```bash
crane blob <SBOM_BLOB_URL>
```

### Inspect attestation structure
```bash
# List task names
cosign download attestation <IMAGE_REF> | head -1 | jq -r .payload | base64 -d | \
  jq '.predicate.buildConfig.tasks[].name'

# Get task results
cosign download attestation <IMAGE_REF> | head -1 | jq -r .payload | base64 -d | \
  jq '[.predicate.buildConfig.tasks[] | {name: .name, results: .results}]'
```

### Inspect operator bundle CSV
```bash
# Download and extract CSV from operator bundle
crane export <BUNDLE_IMAGE> - | tar -xOf - manifests/*.clusterserviceversion.yaml

# List related images
crane export <BUNDLE_IMAGE> - | tar -xOf - manifests/*.clusterserviceversion.yaml | \
  yq '.spec.relatedImages[]'
```

## Parsing Validation Output

### Summarize violations from log
Resolve `summarize_violations.py` relative to the parent `SKILL.md`, then run it with the log path:
```bash
python3 "<resolved path to summarize_violations.py>" "<LOG_FILE>"
```

### Quick violation count by code
```bash
grep -oE '"code":\s*"[^"]+"' <LOG_FILE> | sort | uniq -c | sort -rn
```

## Debugging Workflow

### 1. Identify the violation
Run the helper resolved relative to the parent `SKILL.md`:
```bash
python3 "<resolved path to summarize_violations.py>" "<LOG_FILE>"
# Note the violation code, e.g., "rpm_packages.unique_version"
```

### 2. Find the rule source
```bash
# Package is "rpm_packages", so look in:
ls policy/release/rpm_packages/

# Or search:
grep -r "short_name: unique_version" policy/release/
```

### 3. Read the metadata
```bash
# Open the file and find the METADATA block above the deny rule
# Look for: title, description, solution, failure_msg
```

### 4. Read the tests
```bash
# See what inputs cause failures vs success
cat policy/release/rpm_packages/rpm_packages_test.rego
```

### 5. Compare with actual data
```bash
# Get the actual attestation/SBOM data
cosign download attestation <IMAGE_REF> | jq -r .payload | base64 -d > attestation.json

# Compare structure against what tests expect
```

### 6. Identify the mismatch
- Does the actual data structure match test mocks?
- Are expected fields present?
- Do values match expected patterns?

## Reproducing Locally

Use the [ec-setup skill](../ec-setup/SKILL.md) to extract configuration from a log, then:
```bash
./run.sh
```

Or manually:
```bash
ec validate image \
  --image <IMAGE_REF> \
  --policy policy.yaml \
  -k key.pub \
  --ignore-rekor \
  --output text \
  --strict false \
  --info \
  --debug
```

## Useful Commands

### Extract RPM purls from SBOM
```bash
crane blob <SBOM_BLOB_URL> | jq -r '.packages[].externalRefs[]? |
  select(.referenceType == "purl") | .referenceLocator |
  select(startswith("pkg:rpm"))'
```

### Compare data across platforms
```bash
for sha in <SHA1> <SHA2> <SHA3> <SHA4>; do
  echo "=== $sha ==="
  crane blob <SBOM_URL>@sha256:$sha | jq '<query>'
done
```

### Check purl qualifiers
```bash
# Installed packages have distro= qualifier
crane blob <SBOM_BLOB_URL> | jq -r '.packages[].externalRefs[]? |
  select(.referenceLocator | contains("distro="))'

# Lockfile entries have repository_id= qualifier
crane blob <SBOM_BLOB_URL> | jq -r '.packages[].externalRefs[]? |
  select(.referenceLocator | contains("repository_id="))'
```
