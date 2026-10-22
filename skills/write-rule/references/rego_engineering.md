# Conforma Policy Development Skill

Use this skill when writing, reviewing, or debugging Conforma/EC policy rules in Rego.

---

## Before Writing Rules

Always retrieve and reference the actual policy bundle - do not rely on hardcoded examples.

### Pull the bundle

```bash
conftest pull --policy ./policies quay.io/conforma/release-policy:konflux
```

### Understand the structure

After pulling, examine:
- `./policies/` - Top-level directory structure
- `./policies/lib/` - General helper libraries
- `./policies/release/lib/` - Release-specific helpers
- `./policies/release/*.rego` - Example release rules

### What to look for in the bundle

1. **Library functions** - Read the lib files to find available helpers for:
   - Building results
   - Accessing rule_data configuration
   - Extracting data from attestations
   - Tekton/pipeline helpers

2. **METADATA structure** - Look at existing rules to see the required annotations (title, description, custom fields, etc.)

3. **Input structure** - Examine how existing rules access input data

4. **Patterns** - Match the style and patterns used in existing rules

---

## Writing Rules

### Process

1. **Examine the bundle** - Read relevant lib files and similar existing rules
2. **Match patterns** - Use the same imports, helpers, and result-building approach
3. **Follow METADATA format** - Copy the annotation structure from existing rules
4. **Format** - Always run `opa fmt -w <file>` before finishing

### Rule types

- `deny` - Blocking violations (pipeline fails)
- `warn` - Advisory warnings (pipeline continues)

---

## Data Overlays

Configuration can be passed via `--data` files. Look at the bundle's lib files to understand how rule_data is accessed and structured.

```bash
conftest test --policy ./policies --data ./data/config.json input.json
```

---

## Debugging Policies

### Print statements

Add `print()` calls to trace evaluation (visible with `-v` flag):

```rego
print("Debug:", some_variable)
```

### Interactive evaluation

```bash
# Evaluate a specific rule
opa eval --data ./policies --input input.json "data.release.rule_name.deny"

# With formatted output
opa eval --data ./policies --input input.json --format pretty "data.release.rule_name.deny"

# Full trace
opa eval --data ./policies --input input.json --explain full "data.release.rule_name.deny"
```

---

## Testing Policies

```bash
# Run unit tests
opa test ./policies -v

# Test against sample data
conftest test --policy ./policies --data ./data input.json

# Format before committing
opa fmt -w <path-to-rule.rego>
```

---

## Style Guide

Always follow the Rego style guide: https://docs.styra.com/opa/rego-style-guide

Key conventions:
- Use `some` for iteration variables
- Prefer `contains` over set builder notation
- Use descriptive rule names
- Add METADATA annotations for all deny/warn rules
