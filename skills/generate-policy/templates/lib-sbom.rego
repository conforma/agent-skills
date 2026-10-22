#
# METADATA
# title: SBOM Access Library
# description: >-
#   Library for accessing SBOMs from attestations and OCI blobs.
#   For OPA testing, mock data.lib.sbom.spdx_sboms directly.
#
package lib.sbom

import rego.v1

# spdx_sboms returns all SPDX SBOMs.
# For testing, mock this value directly with: with data.lib.sbom.spdx_sboms as [...]
spdx_sboms := array.concat(_inline_spdx_sboms, _oci_spdx_sboms)

# cyclonedx_sboms returns all CycloneDX SBOMs.
cyclonedx_sboms := array.concat(_inline_cyclonedx_sboms, _oci_cyclonedx_sboms)

# =============================================================================
# Inline Attestations
# =============================================================================

_inline_spdx_sboms := [statement.predicate |
    some att in input.attestations
    statement := att.statement
    statement.predicateType == "https://spdx.dev/Document"
]

_inline_cyclonedx_sboms := [statement.predicate |
    some att in input.attestations
    statement := att.statement
    statement.predicateType == "https://cyclonedx.org/bom"
]

# =============================================================================
# OCI Blob Fetching (from SLSA Provenance)
# =============================================================================

_oci_spdx_sboms := [sbom |
    some sbom in _fetch_oci_sboms
    sbom.spdxVersion  # Check it's an SPDX document
]

_oci_cyclonedx_sboms := [sbom |
    some sbom in _fetch_oci_sboms
    sbom.bomFormat == "CycloneDX"
]

# Fetch SBOMs from OCI blobs referenced in SLSA provenance
_fetch_oci_sboms := [sbom |
    some att in _slsa_provenance_attestations
    some task in _get_tasks(att.statement.predicate)

    # Match image digest for multi-platform images
    _image_matches(task)

    # Get the SBOM blob URL and fetch it
    blob_url := _get_task_result(task, "SBOM_BLOB_URL")
    blob_url != ""

    blob := ec.oci.blob(blob_url)
    sbom := json.unmarshal(blob)
]

# =============================================================================
# SLSA Provenance Helpers
# =============================================================================

_slsa_provenance_attestations := [att |
    some att in input.attestations
    _is_slsa_provenance(att.statement.predicateType)
]

_is_slsa_provenance(predicate_type) if {
    startswith(predicate_type, "https://slsa.dev/provenance/")
}

# =============================================================================
# Task Extraction Helpers
# =============================================================================

# Get tasks from SLSA provenance - handles different formats
_get_tasks(predicate) := tasks if {
    # SLSA v1.0 format with buildDefinition
    tasks := predicate.buildDefinition.resolvedDependencies
} else := tasks if {
    # Tekton Chains format - tasks in runDetails.builder.builderDependencies
    tasks := predicate.runDetails.builder.builderDependencies
} else := tasks if {
    # Tekton format - buildConfig.tasks
    tasks := predicate.buildConfig.tasks
} else := []

# Get a specific result from task
_get_task_result(task, name) := value if {
    # Format: content with name field (Tekton Chains)
    some result in task.content
    result.name == name
    value := result.value
} else := value if {
    # Format: results array
    some result in task.results
    result.name == name
    value := result.value
} else := value if {
    # Format: taskResults array
    some result in task.taskResults
    result.name == name
    value := result.value
} else := ""

# =============================================================================
# Image Matching
# =============================================================================

_image_matches(task) if {
    expected := _get_image_digest(input.image.ref)
    actual := _get_task_result(task, "IMAGE_DIGEST")
    expected == actual
}

# Also match if no IMAGE_DIGEST in task (single-platform)
_image_matches(task) if {
    _get_task_result(task, "IMAGE_DIGEST") == ""
}

_get_image_digest(ref) := digest if {
    contains(ref, "@")
    parts := split(ref, "@")
    digest := parts[count(parts) - 1]
} else := ""
