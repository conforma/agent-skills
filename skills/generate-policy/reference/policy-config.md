# EC Policy Configuration Reference

This document describes the structure of Conforma policy configuration files.

**Schema source**: [conforma/crds](https://github.com/conforma/crds) repository

**JSON Schema**: [policy-spec-schema.json](policy-spec-schema.json)

## Overview

An EC policy configuration defines:
- Which policy rules to evaluate
- Where to find those rules (sources)
- Rule-specific data (ruleData)
- Which rules to include or exclude
- Signature verification settings

## Top-Level Structure

```yaml
name: <string>           # Optional policy name
description: <string>    # Optional description
sources: []              # Required: list of policy sources
configuration: {}        # Optional: global include/exclude
publicKey: <string>      # Optional: public key for verification
rekorUrl: <string>       # Optional: Rekor transparency log URL
identity: {}             # Optional: keyless verification identity
```

## Sources

Each source defines a group of policy rules evaluated together.

```yaml
sources:
  - name: <string>       # Optional source name
    data: []             # Required for rules using rule_data: list of data URLs
    policy: []           # Required: list of policy URLs
    config: {}           # Optional: source-level include/exclude
    volatileConfig: {}   # Optional: time-based include/exclude
```

### Policy URLs

Policy URLs use go-getter style syntax:

| Type | Format | Example |
|------|--------|---------|
| Local path | `./path` | `./policy/package_sources` (relative to policy.yaml) |
| Git | `git::URL//path?ref=REF` | `git::https://github.com/org/repo.git//release_policies/policy/package_sources?ref=main` |
| OCI | `oci::REGISTRY/IMAGE:TAG` | `oci::quay.io/org/policy:latest` |

### Data Files

Rule data is stored in separate YAML files and referenced via the `data:` field. These files contain configuration passed to policy rules via `data.rule_data`.

**Directory structure:**
```
<policy_set>/
├── policy.yaml
├── data/
│   └── config.yaml    # Contains rule_data
└── policy/
    └── ...
```

**policy.yaml:**
```yaml
sources:
  - name: my-rules
    data:
      - ./data    # Directory containing YAML files with rule_data
    policy:
      - ./policy/my_rule
```

**data/config.yaml:**
```yaml
rule_data:
  approved_registries:
    - "quay.io"
    - "registry.redhat.io"
  allowed_package_sources:
    - "^https://registry\\.npmjs\\.org/"
    - "^https://proxy\\.golang\\.org/"
  disallowed_packages:
    - "pkg:npm/malicious-package"
```

Accessed in Rego as:
```rego
approved := object.get(data.rule_data, "approved_registries", [])
allowed := object.get(data.rule_data, "allowed_package_sources", [])
```

**Benefits of external data files:**
- Separates configuration from policy logic
- Easier to update without modifying policy.yaml
- Can have multiple data files for different configuration aspects
- Supports version control and review of configuration changes

### config (Source-Level)

Include or exclude specific rules for this source:

```yaml
config:
  include:
    - "@redhat"                    # Include collection
    - "sbom.allowed_sources"       # Include specific rule
  exclude:
    - "test.experimental_rule"     # Exclude specific rule
```

## Configuration (Global)

Global include/exclude that applies to all sources:

```yaml
configuration:
  include:
    - "@minimal"
  exclude:
    - "deprecated.old_rule"
```

## Collections

Collections are predefined groups of rules. Reference them with `@` prefix:

| Collection | Description |
|------------|-------------|
| `@minimal` | Minimal set of essential rules |
| `@redhat` | Red Hat specific policy rules |
| `@slsa3` | SLSA Level 3 compliance rules |
| `@redhat_rpms` | RPM package validation rules |

```yaml
config:
  include:
    - "@redhat"
    - "@slsa3"
```

## Rule References

Rules are referenced as `<package>.<short_name>`:

```yaml
config:
  include:
    - "sbom.found"                    # From package 'sbom', rule 'found'
    - "sbom_cyclonedx.allowed"        # From package 'sbom_cyclonedx'
  exclude:
    - "test.experimental"
```

## Signature Verification

### Public Key

Inline public key for signature verification:

```yaml
publicKey: |
  -----BEGIN PUBLIC KEY-----
  MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
  -----END PUBLIC KEY-----
```

### Rekor Integration

URL for Rekor transparency log (empty string disables):

```yaml
rekorUrl: https://rekor.sigstore.dev
```

### Keyless Verification

For keyless signing with OIDC identity:

```yaml
identity:
  issuer: https://accounts.google.com
  subject: user@example.com
  # Or use regex patterns:
  # issuerRegExp: "^https://accounts\\.google\\.com$"
  # subjectRegExp: ".*@example\\.com$"
```

## Complete Example

**policy.yaml:**
```yaml
name: production-policy
description: Policy for production releases

sources:
  - name: release-rules
    data:
      - ./data    # Contains rule_data YAML files
    policy:
      - ./policy/lib
      - ./policy/package_sources
    config:
      include:
        - "@redhat"
        - "@slsa3"
      exclude:
        - "test.skip_in_prod"

publicKey: |
  -----BEGIN PUBLIC KEY-----
  MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
  -----END PUBLIC KEY-----

rekorUrl: https://rekor.sigstore.dev
```

**data/allowed_sources.yaml:**
```yaml
rule_data:
  allowed_package_sources:
    - "^https://registry\\.npmjs\\.org/"
    - "^https://proxy\\.golang\\.org/"
```

## Volatile Configuration

Time-based or image-specific exclusions:

```yaml
volatileConfig:
  exclude:
    - value: "package.rule_name"
      effectiveOn: "2024-01-01T00:00:00Z"
      effectiveUntil: "2024-06-01T00:00:00Z"
      reference: "https://issues.example.com/ISSUE-123"
    - value: "package.rule_name"
      imageDigest: "sha256:abc123..."
```

## Schema Reference

For the complete JSON schema, see:
- [policy-spec-schema.json](policy-spec-schema.json) (local copy)
- [conforma/crds repository](https://github.com/conforma/crds/blob/main/api/v1alpha1/policy_spec.json) (upstream)
