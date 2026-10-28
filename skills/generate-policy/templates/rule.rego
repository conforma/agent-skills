#
# METADATA
# title: Example Policy Rule
# description: >-
#   Template for standalone EC policy rules.
#   Customize the package name, metadata, and validation logic for your use case.
#
package example_rule

import rego.v1

# METADATA
# title: Example validation check
# description: >-
#   Validates attestation data against configured requirements.
#   Customize this rule for your specific validation needs.
# custom:
#   short_name: example_check
#   failure_msg: "Validation failed: %s"
#   solution: >-
#     Review the attestation data and ensure it meets the required criteria.
deny contains result if {
	# Access attestations from input
	some att in input.attestations

	# Filter by predicate type (customize for your attestation type)
	# Common types:
	#   - "https://cyclonedx.org/bom" (CycloneDX SBOM)
	#   - "https://spdx.dev/Document" (SPDX SBOM)
	#   - "https://slsa.dev/provenance/v1" (SLSA Provenance)
	att.statement.predicateType == "<predicate_type>"
	predicate := att.statement.predicate

	# Your validation logic here
	# Example: check a required field exists
	not _is_valid(predicate)

	# Construct the result
	result := {
		"code": "example_rule.example_check",
		"msg": sprintf("Validation failed: %s", ["describe the issue"]),
		"severity": "failure",
	}
}

# Helper function for validation logic
_is_valid(predicate) if {
	# Add your validation conditions here
	# This example checks for a required field
	predicate.required_field != ""
}
