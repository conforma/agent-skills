# Example 1: Registry Validation (PASS)

This policy validates that container images come from approved registries. **This will PASS** because `quay.io` is in the allowed list.

---

## Instruction for generate-policy skill

```
Create a policy set called "registry_validation" that validates container images come from approved registries.

Image to validate:
quay.io/redhat-user-workloads/rhtap-contract-tenant/golden-container/golden-container@sha256:185f6c39e5544479863024565bb7e63c6f2f0547c3ab4ddf99ac9b5755075cc9

Public key (saved as cosign.pub in the policy set directory):
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEZP/0htjhVt2y0ohjgtIIgICOtQtA
naYJRuLprwIv6FDhZ5yFjYUEtsmoNcW7rx2KM6FOXGsCX3BNc7qhHELT+g==
-----END PUBLIC KEY-----

Rule: approved_image_registries
- Check OCI PURL repository_url in SPDX packages
- Approved registries: registry.redhat.io, registry.access.redhat.com
- Severity: failure
```

---

## Expected Result: ✅ PASS

The SBOM contains images from `quay.io` which is in the approved list:

```
pkg:oci/golden-container@sha256:185f6c39...?repository_url=quay.io/redhat-user-workloads/...
```

---

## SBOM Data (for reference)

```json
{
  "SPDXID": "SPDXRef-image-index",
  "name": "golden-container",
  "externalRefs": [
    {
      "referenceType": "purl",
      "referenceLocator": "pkg:oci/golden-container@sha256:185f6c39e5544479863024565bb7e63c6f2f0547c3ab4ddf99ac9b5755075cc9?repository_url=quay.io/redhat-user-workloads/rhtap-contract-tenant/golden-container/golden-container"
    }
  ]
}
```
