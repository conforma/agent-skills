## Example 5:  Purl check

### Requirements
Check the Cyclonedx formatted SBOM for a purl

### Public key
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEvNwsVZ3wDJ4VexmmrYvxxNDOuuNs
HgJrCj+favVDoHXuxelanurZGOor1nCoTytfwEFZc5HgcLr+C4lgksRBAA==
-----END PUBLIC KEY-----

### SBOM
{
  "$schema": "http://cyclonedx.org/schema/bom-1.4.schema.json",
  "bomFormat": "CycloneDX",
  "specVersion": "1.4",
  "serialNumber": "urn:uuid:1aa66ef7-08c5-4d39-87c7-ee03f5d00289",
  "version": 1,
  "metadata": {
    "timestamp": "2026-08-01T22:28:43-07:00",
    "tools": [
      {
        "vendor": "anchore",
        "name": "syft",
        "version": "1.42.3"
      }
    ],
    "component": {
      "bom-ref": "4de37fc013392439",
      "type": "container",
      "name": "quay.io/vedadashan2/busybox",
      "version": "sha256:d80aa3d7f5f5388cfae543b990d3cd3d47ff51c48ef29ff66102427bf7bc0a88"
    }
  },
  "components": [
    {
      "bom-ref": "pkg:generic/busybox@1.37.0?package-id=78312d8707bde775",
      "type": "application",
      "name": "busybox",
      "version": "1.37.0",
      "cpe": "cpe:2.3:a:busybox:busybox:1.37.0:*:*:*:*:*:*:*",
      "purl": "pkg:generic/busybox@1.37.0",
      "properties": [
        {
          "name": "syft:package:foundBy",
          "value": "binary-classifier-cataloger"
        },
        {
          "name": "syft:package:type",
          "value": "binary"
        },
        {
          "name": "syft:package:metadataType",
          "value": "binary-signature"
        },
        {
          "name": "syft:location:0:layerID",
          "value": "sha256:068f50152bbc6e10c9d223150c9fbd30d11bcfd7789c432152aa0a99703bd03a"
        },
        {
          "name": "syft:location:0:path",
          "value": "/bin/["
        }
      ]
    },
    {
      "bom-ref": "os:busybox@1.37.0",
      "type": "operating-system",
      "name": "busybox",
      "version": "1.37.0",
      "description": "BusyBox v1.37.0",
      "swid": {
        "tagId": "busybox",
        "name": "busybox",
        "version": "1.37.0"
      },
      "properties": [
        {
          "name": "syft:distro:extendedSupport",
          "value": "false"
        },
        {
          "name": "syft:distro:id",
          "value": "busybox"
        },
        {
          "name": "syft:distro:idLike:0",
          "value": "busybox"
        },
        {
          "name": "syft:distro:prettyName",
          "value": "BusyBox v1.37.0"
        },
        {
          "name": "syft:distro:versionID",
          "value": "1.37.0"
        }
      ]
    },
    {
      "bom-ref": "432e74abcb260bfb",
      "type": "file",
      "name": "/bin/[",
      "hashes": [
        {
          "alg": "SHA-1",
          "content": "912faeca732392cd21175ae53ae49624da034f1c"
        },
        {
          "alg": "SHA-256",
          "content": "25015cc97808781979490c4843c4a483019ec5efc0ecfae648c7fd4f36d18096"
        }
      ]
    }
  ]
}