# Example 8: SLSA v1.0 Builder ID Validation (FAIL)

This policy validates the builder recorded in an SLSA v1.0 provenance
attestation. **This will FAIL** because the attestation builder ID is not in
the approved list.

---

## Instruction for generate-policy skill

```
Create a policy set called "slsa_v1_builder_id_validation" that validates the
builder ID in an image's SLSA Provenance v1.0 attestation.

Image to validate:
quay.io/redhat-user-workloads/rhtap-contract-tenant/golden-container/golden-container@sha256:185f6c39e5544479863024565bb7e63c6f2f0547c3ab4ddf99ac9b5755075cc9

Public key (save as cosign.pub in the policy set directory):
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEZP/0htjhVt2y0ohjgtIIgICOtQtA
naYJRuLprwIv6FDhZ5yFjYUEtsmoNcW7rx2KM6FOXGsCX3BNc7qhHELT+g==
-----END PUBLIC KEY-----

Rule: approved_slsa_v1_builder
- Validate SLSA Provenance v1.0 attestations only.
- Read the builder ID from predicate.runDetails.builder.id.
- Approved builder IDs: https://tekton.dev/chains/v3
- Store the approved IDs as a non-empty, unique list of strings in rule data
  under allowed_builder_ids.
- Deny when the builder ID is missing or is not in allowed_builder_ids.
- Severity: failure.

Generate the rule, its Rego tests, policy.yaml, and rule-data file. Run the OPA
tests and then validate the image with ec validate image. Demonstrate the
expected builder-ID violation.
```

---

## Expected Result: FAIL

The SLSA v1.0 attestation records builder ID
`https://tekton.dev/chains/v2`, but `allowed_builder_ids` allows only
`https://tekton.dev/chains/v3`.

**Expected violation message:**

```
Builder ID "https://tekton.dev/chains/v2" is unexpected
```

---

## SLSA Provenance v1.0 Data (for reference)

This decoded in-toto statement follows the v1.0 fixture used by the
`slsa_build_build_service` and Tekton library tests in `ec-policies`. At
evaluation time, Conforma exposes this statement beneath an attestation's
`statement` field.

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    {
      "name": "quay.io/redhat-user-workloads/rhtap-contract-tenant/golden-container/golden-container",
      "digest": {
        "sha256": "185f6c39e5544479863024565bb7e63c6f2f0547c3ab4ddf99ac9b5755075cc9"
      }
    }
  ],
  "predicateType": "https://slsa.dev/provenance/v1",
  "predicate": {
    "buildDefinition": {
      "buildType": "https://tekton.dev/chains/v2/slsa-tekton",
      "externalParameters": {
        "runSpec": {
          "params": [
            {
              "name": "git-url",
              "value": "https://github.com/conforma/golden-container"
            },
            {
              "name": "output-image",
              "value": "quay.io/redhat-user-workloads/rhtap-contract-tenant/golden-container/golden-container"
            }
          ],
          "pipelineSpec": {}
        }
      },
      "resolvedDependencies": []
    },
    "runDetails": {
      "builder": {
        "id": "https://tekton.dev/chains/v2"
      },
      "metadata": {
        "invocationID": "golden-container-example",
        "buildStartedOn": "2025-02-10T01:12:23Z",
        "buildFinishedOn": "2025-02-10T01:20:00Z"
      }
    }
  }
}
```

For SLSA v1.0, the builder ID is at `predicate.runDetails.builder.id`. This is
different from the v0.2 path, `predicate.builder.id`.
