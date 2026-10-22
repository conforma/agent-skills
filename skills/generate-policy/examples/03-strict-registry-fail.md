# Example 3: Strict Registry Policy (FAIL)

This policy requires images from `registry.redhat.io` only and blocks user workload namespaces. **This will FAIL** because the image is from `quay.io/redhat-user-workloads`.

---

## Instruction for generate-policy skill

```
Create a policy set called "strict_registry_policy" that enforces strict registry requirements for production releases.

Image to validate:
quay.io/redhat-user-workloads/rhtap-contract-tenant/golden-container/golden-container@sha256:185f6c39e5544479863024565bb7e63c6f2f0547c3ab4ddf99ac9b5755075cc9

Public key (saved as cosign.pub in the policy set directory):
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEZP/0htjhVt2y0ohjgtIIgICOtQtA
naYJRuLprwIv6FDhZ5yFjYUEtsmoNcW7rx2KM6FOXGsCX3BNc7qhHELT+g==
-----END PUBLIC KEY-----

Rule 1: redhat_registry_only
- Check OCI PURL repository_url in SPDX packages
- Only allow images from registry.redhat.io
- Severity: failure

Rule 2: no_user_workloads
- Check repository URL does not contain blocked patterns
- Block patterns: "redhat-user-workloads", "user-workloads", "-tenant/"
- Severity: failure

Rule 3: require_supplier_info
- Check supplier field in SPDX packages
- Warn if supplier is NOASSERTION
- Severity: warning
```

---

## Expected Result: ❌ FAIL

### Rule 1 Failure: redhat_registry_only

The SBOM contains images from `quay.io`, not `registry.redhat.io`:

```
pkg:oci/golden-container@sha256:...?repository_url=quay.io/redhat-user-workloads/...
```

**Expected Violation Message:**
```
Image pkg:oci/golden-container@sha256:185f6c39... is from registry "quay.io" which is not approved. Only registry.redhat.io is allowed.
```

### Rule 2 Failure: no_user_workloads

The repository URL contains `redhat-user-workloads`:

```
repository_url=quay.io/redhat-user-workloads/rhtap-contract-tenant/...
```

**Expected Violation Message:**
```
Image golden-container is from repository "quay.io/redhat-user-workloads/rhtap-contract-tenant/golden-container/golden-container" which matches blocked pattern "redhat-user-workloads"
```

### Rule 3 Warning: require_supplier_info

The SBOM contains packages with no supplier information:

```json
{
  "name": "golden-container",
  "supplier": "NOASSERTION"
}
```

**Expected Warning Message:**
```
Package golden-container has no supplier information (NOASSERTION)
```

---

## SBOM Data (for reference)

```json
{
  "SPDXID": "SPDXRef-image-index",
  "name": "golden-container",
  "supplier": "NOASSERTION",
  "licenseDeclared": "NOASSERTION",
  "externalRefs": [
    {
      "referenceType": "purl",
      "referenceLocator": "pkg:oci/golden-container@sha256:185f6c39e5544479863024565bb7e63c6f2f0547c3ab4ddf99ac9b5755075cc9?repository_url=quay.io/redhat-user-workloads/rhtap-contract-tenant/golden-container/golden-container"
    }
  ]
}
```
