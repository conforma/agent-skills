# Example 7: SLSA v0.2 Builder ID Validation (PASS)

This policy validates the builder recorded in an SLSA v0.2 provenance
attestation. **This will PASS** because the attestation builder ID is in the
approved list.

---

## Instruction for generate-policy skill

```
Create a policy set called "slsa_v02_builder_id_validation" that validates the
builder ID in an image's SLSA Provenance v0.2 attestation.

Image to validate:
quay.io/redhat-user-workloads/rhtap-contract-tenant/golden-container/golden-container@sha256:185f6c39e5544479863024565bb7e63c6f2f0547c3ab4ddf99ac9b5755075cc9

Public key (save as cosign.pub in the policy set directory):
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEZP/0htjhVt2y0ohjgtIIgICOtQtA
naYJRuLprwIv6FDhZ5yFjYUEtsmoNcW7rx2KM6FOXGsCX3BNc7qhHELT+g==
-----END PUBLIC KEY-----

Rule: approved_slsa_v02_builder
- Validate SLSA Provenance v0.2 attestations only.
- Read the builder ID from predicate.builder.id.
- Approved builder IDs: https://tekton.dev/chains/v2
- Store the approved IDs as a non-empty, unique list of strings in rule data
  under allowed_builder_ids.
- Deny when the builder ID is missing or is not in allowed_builder_ids.
- Severity: failure.

Generate the rule, its Rego tests, policy.yaml, and rule-data file. Run the OPA
tests and then validate the image with ec validate image.
```

---

## Expected Result: PASS

The SLSA v0.2 attestation has builder ID
`https://tekton.dev/chains/v2`, which is in `allowed_builder_ids`; no builder
ID violation is reported.

---

## SLSA Provenance v0.2 Data (for reference)

This decoded in-toto statement follows the v0.2 shape used by the
`slsa_build_build_service` policy tests in `ec-policies`. At evaluation time,
Conforma exposes this statement beneath an attestation's `statement` field.

```json
{
  "_type": "https://in-toto.io/Statement/v0.1",
  "subject": [
    {
      "name": "quay.io/redhat-user-workloads/rhtap-contract-tenant/golden-container/golden-container",
      "digest": {
        "sha256": "185f6c39e5544479863024565bb7e63c6f2f0547c3ab4ddf99ac9b5755075cc9"
      }
    }
  ],
  "predicateType": "https://slsa.dev/provenance/v0.2",
  "predicate": {
    "builder": {
      "id": "https://tekton.dev/chains/v2"
    },
    "buildType": "tekton.dev/v1beta1/PipelineRun",
    "invocation": {
      "configSource": {},
      "parameters": {
        "git-url": "https://github.com/conforma/golden-container",
        "image-url": "quay.io/redhat-user-workloads/rhtap-contract-tenant/golden-container/golden-container"
      }
    }
  }
}
```

For SLSA v0.2, the builder ID is at `predicate.builder.id`. This differs from
SLSA v1.0, where it is at `predicate.runDetails.builder.id`.
