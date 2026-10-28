# SBOM Attestation Structure Reference

This document describes the exact structure of SPDX and CycloneDX SBOM attestations to enable traversal and policy rule development.

## IMPORTANT: Accessing SBOMs

SBOMs are NOT always directly embedded in attestations. In Konflux/RHTAP builds, the SBOM is stored as an OCI blob and referenced from the SLSA provenance attestation.

### Use the Standalone SBOM Library

**Always include the standalone SBOM library** in your policy set. Create `policy/lib/sbom.rego` with the SBOM access functions that handle:
1. SBOMs embedded directly in attestations
2. SBOMs stored as OCI blobs (fetched via `ec.oci.blob()`)

```rego
import data.lib.sbom

# Access SPDX SBOMs
some s in sbom.spdx_sboms
some pkg in s.packages

# Access CycloneDX SBOMs
some s in sbom.cyclonedx_sboms
some component in s.components
```

### Policy Configuration

Include the lib directory in your policy.yaml:

```yaml
sources:
  - name: my-rules
    policy:
      - ./policy/lib        # Standalone SBOM library
      - ./policy/my_rule
```

### Why This Matters

If you iterate directly over `input.attestations`, you will only find SBOMs that are inline attestations. For images built with Konflux/RHTAP:
- The SLSA provenance contains a `SBOM_BLOB_URL` task result
- The actual SBOM is stored at that OCI blob URL
- The `lib.sbom` functions fetch and parse this automatically using `ec.oci.blob()`

### Directory Structure

```
<policy_set>/
├── policy.yaml
├── cosign.pub
└── policy/
    ├── lib/
    │   └── sbom.rego           # Standalone SBOM access library
    └── <rule_name>/
        ├── <rule_name>.rego
        └── <rule_name>_test.rego
```

---

## Required Inputs for SBOM Rules

When generating SBOM validation rules, prompt the user for required configuration:

### Package Source Validation

When the user requests a rule to validate package sources (e.g., "validate npm packages come from allowed sources"):

**Required**: `allowed_package_sources` - List of allowed source URLs or regex patterns

**Prompt**: "What sources should be allowed for [package type] packages? Please provide a list of allowed URLs or URL patterns."

**Example values**:
- `["https://registry.npmjs.org/"]` - npm packages
- `["https://proxy.golang.org/"]` - Go modules
- `["https://pypi.org/", "https://pypi.internal.company.com/"]` - Python packages

**Usage in policy config** (`ruleData`):
```yaml
ruleData:
  allowed_package_sources:
    - "^https://registry\\.npmjs\\.org/"
    - "^https://npm\\.internal\\.company\\.com/"
```

**Usage in Rego rule**:
```rego
allowed_patterns := object.get(data.rule_data, "allowed_package_sources", [])
not _url_matches_allowed(url, allowed_patterns)
```

### Other SBOM Rule Inputs

| Rule Type | Required Input | Description |
|-----------|---------------|-------------|
| Package source validation | `allowed_package_sources` | List of allowed URL patterns |
| License validation | `allowed_licenses` | List of allowed SPDX license IDs |
| Package blocklist | `disallowed_packages` | List of blocked package PURLs |
| Attribute validation | `disallowed_attributes` | List of forbidden package attributes |

---

## SPDX Format

### Identification
- **Predicate type**: `https://spdx.dev/Document`
- **Detection**: `att.statement.predicateType == "https://spdx.dev/Document"` or presence of `SPDXID == "SPDXRef-DOCUMENT"`

### Packages Location
```
att.statement.predicate.packages
```

### PURL Location
PURLs are found in the package's `externalRefs` array where `referenceType == "purl"`:
```
pkg.externalRefs[].referenceLocator (where referenceType == "purl")
```

### Download URL
The download URL is embedded as a qualifier within the PURL string:
```
pkg:type/namespace/name@version?download_url=https://...
```

### Hermeto Marker
Hermeto markers are stored in package annotations. The `comment` field contains JSON with the build tool information:
```
pkg.annotations[].comment (contains JSON with name: "hermeto:found_by")
```

### SPDX Example JSON

```json
{
  "_type": "https://in-toto.io/Statement/v0.1",
  "predicateType": "https://spdx.dev/Document",
  "predicate": {
    "SPDXID": "SPDXRef-DOCUMENT",
    "spdxVersion": "SPDX-2.3",
    "name": "example-sbom",
    "packages": [
      {
        "SPDXID": "SPDXRef-Package-1",
        "name": "example-package",
        "versionInfo": "1.0.0",
        "downloadLocation": "https://example.com/package.tar.gz",
        "externalRefs": [
          {
            "referenceCategory": "PACKAGE-MANAGER",
            "referenceType": "purl",
            "referenceLocator": "pkg:golang/github.com/example/package@v1.0.0?download_url=https%3A%2F%2Fproxy.golang.org%2Fgithub.com%2Fexample%2Fpackage%2F%40v%2Fv1.0.0.zip"
          },
          {
            "referenceCategory": "SECURITY",
            "referenceType": "cpe23Type",
            "referenceLocator": "cpe:2.3:a:example:package:1.0.0:*:*:*:*:*:*:*"
          }
        ],
        "annotations": [
          {
            "annotationDate": "2024-01-15T10:30:00Z",
            "annotationType": "OTHER",
            "annotator": "Tool: hermeto",
            "comment": "{\"name\": \"hermeto:found_by\", \"value\": \"go-package-analysis\"}"
          }
        ],
        "checksums": [
          {
            "algorithm": "SHA256",
            "checksumValue": "abc123def456..."
          }
        ]
      }
    ],
    "relationships": [
      {
        "spdxElementId": "SPDXRef-DOCUMENT",
        "relatedSpdxElement": "SPDXRef-Package-1",
        "relationshipType": "DESCRIBES"
      }
    ]
  }
}
```

### Key Rego Paths for SPDX

```rego
# Get all packages
packages := att.statement.predicate.packages

# Get PURL from package
purl := [ref.referenceLocator |
  some ref in pkg.externalRefs
  ref.referenceType == "purl"
][0]

# Check for Hermeto marker
has_hermeto := [ann |
  some ann in pkg.annotations
  contains(ann.comment, "hermeto:found_by")
]
```

---

## CycloneDX Format

### Identification
- **Predicate type**: `https://cyclonedx.org/bom`
- **Detection**: `att.statement.predicateType == "https://cyclonedx.org/bom"` or `bomFormat == "CycloneDX"`

### Components Location
```
att.statement.predicate.components
```

### PURL Location
PURLs are stored directly on the component:
```
component.purl
```

### Download URL
Download URLs are in the `externalReferences` array with `type == "distribution"`:
```
component.externalReferences[].url (where type == "distribution")
```

### Hermeto Marker
Hermeto markers are stored in component properties:
```
component.properties[] (where name == "hermeto:found_by")
```

### CycloneDX Example JSON

```json
{
  "_type": "https://in-toto.io/Statement/v0.1",
  "predicateType": "https://cyclonedx.org/bom",
  "predicate": {
    "bomFormat": "CycloneDX",
    "specVersion": "1.5",
    "version": 1,
    "serialNumber": "urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79",
    "metadata": {
      "timestamp": "2024-01-15T10:30:00Z",
      "tools": {
        "components": [
          {
            "type": "application",
            "name": "syft",
            "version": "0.100.0"
          }
        ]
      }
    },
    "components": [
      {
        "type": "library",
        "bom-ref": "pkg:golang/github.com/example/package@v1.0.0",
        "name": "package",
        "version": "v1.0.0",
        "purl": "pkg:golang/github.com/example/package@v1.0.0",
        "externalReferences": [
          {
            "type": "distribution",
            "url": "https://proxy.golang.org/github.com/example/package/@v/v1.0.0.zip"
          },
          {
            "type": "vcs",
            "url": "https://github.com/example/package"
          }
        ],
        "properties": [
          {
            "name": "hermeto:found_by",
            "value": "go-package-analysis"
          },
          {
            "name": "syft:package:type",
            "value": "go-module"
          }
        ],
        "hashes": [
          {
            "alg": "SHA-256",
            "content": "abc123def456..."
          }
        ]
      },
      {
        "type": "library",
        "bom-ref": "pkg:rpm/rhel/openssl@3.0.7-1.el9",
        "name": "openssl",
        "version": "3.0.7-1.el9",
        "purl": "pkg:rpm/rhel/openssl@3.0.7-1.el9?arch=x86_64",
        "externalReferences": [
          {
            "type": "distribution",
            "url": "https://cdn.redhat.com/content/dist/rhel9/..."
          }
        ],
        "properties": []
      }
    ]
  }
}
```

### Key Rego Paths for CycloneDX

```rego
# Get all components
components := att.statement.predicate.components

# Get PURL from component (direct field)
purl := component.purl

# Get download URL
download_url := [ref.url |
  some ref in component.externalReferences
  ref.type == "distribution"
][0]

# Check for Hermeto marker
has_hermeto := [prop |
  some prop in component.properties
  prop.name == "hermeto:found_by"
]
```

---

## Summary: Path Comparison

| Data Element | SPDX Path | CycloneDX Path |
|-------------|-----------|----------------|
| Items | `predicate.packages` | `predicate.components` |
| PURL | `pkg.externalRefs[].referenceLocator` (where `referenceType == "purl"`) | `component.purl` |
| Download URL | Inside PURL as `download_url` qualifier | `component.externalReferences[].url` (where `type == "distribution"`) |
| Hermeto Marker | `pkg.annotations[].comment` (JSON with `hermeto:found_by`) | `component.properties[]` (where `name == "hermeto:found_by"`) |

## Supported Schemas

Policy validation uses these JSON schema definitions (available in this directory):
- [spdx-schema.json](spdx-schema.json) - SPDX 2.3 JSON schema
- [cyclonedx-schema.json](cyclonedx-schema.json) - CycloneDX 1.5 JSON schema

## Common Rego Patterns (Pure Rego)

### Access CycloneDX SBOMs

```rego
# Filter attestations for CycloneDX SBOMs
some att in input.attestations
att.statement.predicateType == "https://cyclonedx.org/bom"
sbom := att.statement.predicate

# Iterate over components
some component in sbom.components
purl := component.purl
```

### Access SPDX SBOMs

```rego
# Filter attestations for SPDX SBOMs
some att in input.attestations
att.statement.predicateType == "https://spdx.dev/Document"
sbom := att.statement.predicate

# Iterate over packages
some pkg in sbom.packages

# Extract PURL from externalRefs
some ref in pkg.externalRefs
ref.referenceType == "purl"
purl := ref.referenceLocator
```

### Check for Hermeto Marker (CycloneDX)

```rego
# Find components fetched by Hermeto
some component in sbom.components
some prop in component.properties
prop.name == "hermeto:found_by"
```

### Check for Hermeto Marker (SPDX)

```rego
# Find packages with Hermeto annotations
some pkg in sbom.packages
some ann in pkg.annotations
contains(ann.comment, "hermeto:found_by")
```

### Get Distribution URL (CycloneDX)

```rego
# Get download URL from externalReferences
some ref in component.externalReferences
ref.type == "distribution"
url := ref.url
```

### Parse and Compare PURLs

```rego
# Parse a PURL (EC built-in)
parsed := ec.purl.parse(raw_purl)
# Returns: { type, namespace, name, version, qualifiers, subpath }

# Check if PURL is valid
is_valid := ec.purl.is_valid(raw_purl)

# Access parsed fields
purl_type := parsed.type        # e.g., "golang", "rpm", "npm"
purl_name := parsed.name        # e.g., "package-name"
purl_version := parsed.version  # e.g., "v1.0.0"
```

### Match URL Against Patterns

```rego
# Check if URL matches any allowed pattern
_url_allowed(url, patterns) if {
    some pattern in patterns
    regex.match(pattern, url)
}

# Usage
allowed_patterns := ["^https://proxy\\.golang\\.org/", "^https://registry\\.npmjs\\.org/"]
_url_allowed(distribution_url, allowed_patterns)
```
