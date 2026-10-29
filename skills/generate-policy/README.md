# Generate Policy Skill

Describe what a container image policy should check, and this skill generates a Conforma policy set with rules, tests, configuration, and a validation command. You do not need to know Rego or the attestation formats.

## Quick start

Ask your agent to use the `generate-policy` skill with one of the prompts below, or ask it to read [SKILL.md](SKILL.md) and follow its workflow.

## Inputs

| Input | When needed | Example |
|-------|-------------|---------|
| Policy set name and validation requirement | Always | `package_sources`; “Allow npm packages only from registry.npmjs.org” |
| Rule-specific values | When the rule needs them | Approved registries, allowed builder IDs, or expected source repository |
| Image reference | To validate the generated policy against an image | `quay.io/org/app@sha256:...` |
| Public key | When validating an image signed with that key | `cosign.pub` or the key contents |

An image is optional. Without one, the agent can generate the policy and run its Rego tests; image validation requires an image reference.

## Example prompts

### Package sources in an SBOM

```text
Use the generate-policy skill to create a policy set named package_sources.
Check distribution URLs for npm components in CycloneDX SBOMs. Allow only
URLs under https://registry.npmjs.org/. Store the allowed URL pattern in
rule data, and deny components fetched from any other source.

Generate the Rego rule, tests, policy.yaml, and rule-data file. Cover
allowed and disallowed URLs, missing distribution URLs, and an empty
allowlist in the tests. Run the Rego tests and report the results.
I do not have an image to validate yet.
```

### Builder identity in SLSA provenance

```text
Use the generate-policy skill to create a policy set named approved_builders.
Check SLSA provenance v0.2 and v1.0 attestations. Allow only builder ID
https://tekton.dev/chains/v2. Store the allowed builder IDs in rule data.
Deny attestations with a missing or unapproved builder ID.

Generate the Rego rule, tests, policy.yaml, and rule-data file. Include
every Rego dependency in the policy configuration. Test both provenance
versions, missing builder IDs, unapproved IDs, and an empty allowlist.
Run the Rego tests and report the results. I do not have an image to
validate yet.
```

## What the skill creates

```text
<policy_set>/
├── policy.yaml
├── data/
│   └── <rule_data>.yaml
└── policy/
    └── <rule_name>/
        ├── <rule_name>.rego
        └── <rule_name>_test.rego
```

The skill can generate rules for:

- **SBOM contents:** Check packages, package sources, licenses, and OCI package registry URLs recorded in an image's SBOM.
- **SLSA build provenance:** Check attestation fields such as builder identity, source repository, and build type.

## Verify the result

From the generated policy set directory, run the Rego tests:

```bash
ec opa test ./policy -v --fail-on-empty
```

The skill outputs an `ec validate image` command for the generated policy. If you provide an image reference, the agent also runs the command and checks that the result matches your requirements. Run the command from the policy set directory so the relative paths in `policy.yaml` resolve. If you provided a public key file, the command includes `--public-key cosign.pub`; other verification options depend on your signing setup.

## Examples and references

- [Package source rules and SBOM structure](reference/sbom-structure.md)
- [OCI package registry validation from an SPDX SBOM](examples/01-registry-validation-pass.md)
- [License compliance](examples/02-license-compliance-fail.md)
- [SLSA v0.2 builder ID validation](examples/07-slsa-v02-builder-id-validation-pass.md) and [SLSA v1.0 builder ID validation](examples/08-slsa-v1-builder-id-validation-fail.md)
- [Policy configuration reference](reference/policy-config.md) and [test patterns](reference/test-patterns.md)
