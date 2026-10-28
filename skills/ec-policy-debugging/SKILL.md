---
name: ec-policy-debugging
description: Debug Enterprise Contract policy violations by examining rule metadata, tests, and actual data. Use when investigating EC validation failures, policy violations, or understanding why a rule triggered.
---

# EC Policy Debugging Skill

Use this skill to debug Enterprise Contract policy violations by dynamically examining policy rules, metadata, tests, and actual data.

## When to Use

- Investigating why a policy rule triggered a violation
- Understanding what a specific rule checks
- Comparing expected vs actual data in attestations/SBOMs
- Debugging `ec validate image` failures

## Understanding Violation Output

Violations are displayed in this format:

```
✕ [Violation] <package>.<short_name>
  ImageRef: <image that produced the violation>
  Reason: <brief explanation of why the violation occurred>
  Title: <human-readable rule name>
  Description: <what the rule checks and why>
  Solution: <how to resolve the issue>
```

| Field | Description |
|-------|-------------|
| `[Violation]` | Contains the rule name as `package.short_name` |
| `ImageRef` | The image whose attestation, SBOM, or manifest triggered the violation |
| `Reason` | Brief explanation of the specific issue found |
| `Title` | Human-readable name from rule metadata |
| `Description` | What the rule checks and how to exclude it |
| `Solution` | Guidance on how to fix the underlying issue |

## Quick Start

When you encounter a violation:

1. **Get the violation code** from the log (e.g., `olm.unmapped_references`)
2. **Find the rule** in the policy source
3. **Read the metadata** to understand what it checks and how to fix it
4. **Read the tests** to see expected inputs
5. **Compare actual data** against expectations

## Key Files

- [Full debugging reference](debugging.md) - Complete methodology and commands
- `summarize_violations.py` - Script to summarize violations from logs
- `summarize_violations_test.py` - Tests for the summarize script

## Summarize Violations

Resolve `summarize_violations.py` relative to this `SKILL.md` and invoke it with the log path:

```bash
python3 "<resolved path to summarize_violations.py>" "<LOG_FILE>"
```

Supports two log formats:
- **JSON format**: TaskRun/PipelineRun output with `{"success"...` structure
- **Text format**: Human-readable output with `Results:` section

Or quick count:
```bash
grep -oE '"code":\s*"[^"]+"' <LOG_FILE> | sort | uniq -c | sort -rn
```

## Testing

Run the helper tests with Python 3 and pytest. Resolve the test-file path relative to this `SKILL.md`:
```bash
python3 -m pytest -q "<resolved path to summarize_violations_test.py>"
```

Test coverage:
- JSON format parsing (9 tests)
- Text format parsing (6 tests)
- Format auto-detection (3 tests)
- Edge cases (6 tests)

## Find Rule from Violation Code

Violation codes follow the pattern `<package>.<short_name>`.

```bash
# Example: rpm_packages.unique_version
# Look in: policy/release/rpm_packages/rpm_packages.rego

grep -r "short_name: <short_name>" policy/release/
```

## Read Rule Metadata

Every rule has a METADATA block with:
- `title` - Human-readable rule name
- `description` - What the rule checks
- `custom.failure_msg` - Message template
- `custom.solution` - How to fix violations

```bash
awk '/^# METADATA/,/^deny contains|^warn contains/' policy/release/<package>/<package>.rego
```

## Access Actual Data

```bash
# Download attestation
cosign download attestation <IMAGE_REF> | jq -r .payload | base64 -d | jq

# Download SBOM
cosign download sbom <IMAGE_REF>

# Download SBOM blob
crane blob <SBOM_BLOB_URL>
```

## Pull OCI Policy Bundles

If policy sources are OCI references:
```bash
conftest pull --policy ./policies <OCI_URL>
```
