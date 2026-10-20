# Example 2: License Compliance (FAIL)

This policy validates that all packages have declared licenses. **This will FAIL** because all licenses in the SBOM are `NOASSERTION`.

---

## Instruction for generate-policy skill

```
Create a policy set called "license_compliance" that validates packages have proper license declarations.

Image to validate:
quay.io/redhat-user-workloads/rhtap-contract-tenant/golden-container/golden-container@sha256:185f6c39e5544479863024565bb7e63c6f2f0547c3ab4ddf99ac9b5755075cc9

Public key (saved as cosign.pub in the policy set directory):
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEZP/0htjhVt2y0ohjgtIIgICOtQtA
naYJRuLprwIv6FDhZ5yFjYUEtsmoNcW7rx2KM6FOXGsCX3BNc7qhHELT+g==
-----END PUBLIC KEY-----

Rule 1: license_declared
- Check licenseDeclared field in SPDX packages
- Reject packages with NOASSERTION or NONE as license
- Severity: failure

Rule 2: allowed_licenses
- Check licenseDeclared against an allowlist
- Allowed licenses: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, CC0-1.0, GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, LGPL-2.1-only, LGPL-3.0-only, MPL-2.0
- Severity: failure
```

---

## Expected Result: ❌ FAIL

The SBOM contains packages with `NOASSERTION` licenses:

**Expected Violation Messages:**
```
Package golden-container has license "NOASSERTION" which is not an acceptable license declaration
Package golden-container_amd64 has license "NOASSERTION" which is not an acceptable license declaration
Package golden-container_arm64 has license "NOASSERTION" which is not an acceptable license declaration
```

---

## SBOM Data (for reference)

```json
{
  "SPDXID": "SPDXRef-image-index",
  "name": "golden-container",
  "licenseDeclared": "NOASSERTION",
  "externalRefs": [
    {
      "referenceType": "purl",
      "referenceLocator": "pkg:oci/golden-container@sha256:185f6c39...?repository_url=quay.io/..."
    }
  ]
}
```

All three packages in the SBOM have `"licenseDeclared": "NOASSERTION"`:
- `golden-container`
- `golden-container_amd64`
- `golden-container_arm64`
