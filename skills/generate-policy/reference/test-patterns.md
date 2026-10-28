# Rego Policy Test Patterns

This document describes how to write tests for EC policy rules using OPA's testing framework.

**Reference**: [OPA Policy Testing Guide](https://www.openpolicyagent.org/docs/policy-testing)

## Test File Conventions

### Naming and Location

For Rego lint compliance, test files must be in the same directory as the rule file, which matches the package name:

| Package | File Path |
|---------|-----------|
| `package_sources_test` | `<name>/policy/package_sources/package_sources_test.rego` |

- Test file: `<rule_name>_test.rego` (same directory as the rule)
- Package: `<rule_name>_test` (e.g., `package_sources_test`)

### Structure
```rego
package <rule_name>_test

import rego.v1

import data.<rule_name>

# Test rules prefixed with test_
test_<descriptive_name> if {
    # test logic
}
```

## Running Tests

```bash
# Run all tests in directory
ec opa test . -v

# Run with coverage
ec opa test . --coverage

# Run specific tests
ec opa test . -v --run "test_allowed"
```

## Mock Data Patterns

### Using `with` for Mocking

The `with` keyword replaces data during test execution:

```rego
test_example if {
    <rule>.deny == expected_result
        with input.attestations as mock_attestations
        with data.rule_data as mock_rule_data
}
```

### Chaining Multiple Mocks

```rego
test_with_multiple_mocks if {
    result := <rule>.deny
        with input.attestations as mock_attestations
        with data.rule_data.allowed_package_sources as ["^https://allowed\\.com/"]
}
```

---

## Mock Data Helpers for SBOM

### CycloneDX Mock Attestation

```rego
# Helper: Create a CycloneDX attestation
_mock_cyclonedx_attestation(components) := {
    "statement": {
        "predicateType": "https://cyclonedx.org/bom",
        "predicate": {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "components": components,
        },
    },
}

# Helper: Create a CycloneDX component
_mock_component(purl, distribution_url) := _mock_component_with_hermeto(purl, distribution_url, true)

_mock_component_with_hermeto(purl, distribution_url, has_hermeto) := component if {
    has_hermeto
    component := {
        "type": "library",
        "purl": purl,
        "externalReferences": [
            {"type": "distribution", "url": distribution_url},
        ],
        "properties": [
            {"name": "hermeto:found_by", "value": "hermeto"},
        ],
    }
} else := component if {
    component := {
        "type": "library",
        "purl": purl,
        "externalReferences": [
            {"type": "distribution", "url": distribution_url},
        ],
        "properties": [],
    }
}
```

### SPDX Mock Attestation

```rego
# Helper: Create an SPDX attestation
_mock_spdx_attestation(packages) := {
    "statement": {
        "predicateType": "https://spdx.dev/Document",
        "predicate": {
            "SPDXID": "SPDXRef-DOCUMENT",
            "spdxVersion": "SPDX-2.3",
            "packages": packages,
        },
    },
}

# Helper: Create an SPDX package
_mock_spdx_package(purl) := _mock_spdx_package_with_hermeto(purl, true)

_mock_spdx_package_with_hermeto(purl, has_hermeto) := pkg if {
    has_hermeto
    pkg := {
        "SPDXID": "SPDXRef-Package-1",
        "name": "test-package",
        "externalRefs": [
            {"referenceType": "purl", "referenceLocator": purl},
        ],
        "annotations": [
            {"comment": "{\"name\": \"hermeto:found_by\", \"value\": \"hermeto\"}"},
        ],
    }
} else := pkg if {
    pkg := {
        "SPDXID": "SPDXRef-Package-1",
        "name": "test-package",
        "externalRefs": [
            {"referenceType": "purl", "referenceLocator": purl},
        ],
        "annotations": [],
    }
}
```

---

## Required Test Cases

Every policy rule should include tests for these scenarios:

### 1. Pass Cases (No Violations)

Test that compliant data produces no denials:

```rego
test_allowed_source_passes if {
    components := [_mock_component(
        "pkg:npm/lodash@4.17.21",
        "https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz",
    )]
    attestations := [_mock_cyclonedx_attestation(components)]

    count(package_sources.deny) == 0
        with input.attestations as attestations
        with data.rule_data.allowed_package_sources as ["^https://registry\\.npmjs\\.org/"]
}
```

### 2. Fail Cases (Violations Expected)

Test that non-compliant data produces denials:

```rego
test_disallowed_source_fails if {
    components := [_mock_component(
        "pkg:npm/malicious@1.0.0",
        "https://evil.com/malicious-1.0.0.tgz",
    )]
    attestations := [_mock_cyclonedx_attestation(components)]

    count(package_sources.deny) == 1
        with input.attestations as attestations
        with data.rule_data.allowed_package_sources as ["^https://registry\\.npmjs\\.org/"]
}
```

### 3. Edge Cases

#### Empty Input
```rego
test_no_attestations if {
    count(package_sources.deny) == 0
        with input.attestations as []
}
```

#### Empty Rule Data
```rego
test_empty_allowed_sources_denies_all if {
    components := [_mock_component(
        "pkg:npm/lodash@4.17.21",
        "https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz",
    )]
    attestations := [_mock_cyclonedx_attestation(components)]

    count(package_sources.deny) == 1
        with input.attestations as attestations
        with data.rule_data.allowed_package_sources as []
}
```

#### Non-Hermeto Components (Should Skip)
```rego
test_non_hermeto_component_skipped if {
    components := [_mock_component_with_hermeto(
        "pkg:npm/lodash@4.17.21",
        "https://evil.com/lodash.tgz",
        false,  # No hermeto marker
    )]
    attestations := [_mock_cyclonedx_attestation(components)]

    count(package_sources.deny) == 0
        with input.attestations as attestations
        with data.rule_data.allowed_package_sources as ["^https://registry\\.npmjs\\.org/"]
}
```

### 4. Multiple Items

```rego
test_multiple_components_mixed if {
    components := [
        _mock_component("pkg:npm/good@1.0.0", "https://registry.npmjs.org/good.tgz"),
        _mock_component("pkg:npm/bad@1.0.0", "https://evil.com/bad.tgz"),
    ]
    attestations := [_mock_cyclonedx_attestation(components)]

    count(package_sources.deny) == 1
        with input.attestations as attestations
        with data.rule_data.allowed_package_sources as ["^https://registry\\.npmjs\\.org/"]
}
```

### 5. Violation Message Content

```rego
test_violation_message_content if {
    components := [_mock_component(
        "pkg:npm/bad@1.0.0",
        "https://evil.com/bad.tgz",
    )]
    attestations := [_mock_cyclonedx_attestation(components)]

    result := package_sources.deny
        with input.attestations as attestations
        with data.rule_data.allowed_package_sources as []

    count(result) == 1
    some violation in result
    contains(violation.msg, "pkg:npm/bad@1.0.0")
    contains(violation.msg, "https://evil.com/bad.tgz")
}
```

---

## Test Checklist

When writing tests for a policy rule, ensure you cover:

| Category | Test Case | Description |
|----------|-----------|-------------|
| Pass | Valid data | Compliant input produces no violations |
| Fail | Invalid data | Non-compliant input produces violations |
| Edge | Empty input | No attestations/components |
| Edge | Empty config | Empty or missing rule data |
| Edge | Skipped items | Items that should be ignored (e.g., no Hermeto marker) |
| Multiple | Mixed results | Some pass, some fail |
| Content | Message check | Violation message contains expected values |
| Count | Exact count | Correct number of violations |

---

## Tips

### Use Descriptive Test Names

```rego
# Good
test_npm_package_from_npmjs_allowed if { ... }
test_npm_package_from_unknown_source_denied if { ... }

# Bad
test_1 if { ... }
test_pass if { ... }
```

### Test Rule Output, Not Just Boolean

```rego
# Prefer checking the actual deny set
result := package_sources.deny with input.attestations as ...
count(result) == 1
some v in result
v.code == "package_sources.allowed_package_sources"

# Over just boolean checks
package_sources.deny with input.attestations as ...
```

### Skip Tests with `todo_` Prefix

```rego
todo_test_not_implemented_yet if {
    # This test will be skipped
    false
}
```
