#
# METADATA
# title: SBOM Package Source Validation
# description: >-
#   Validates that packages in a CycloneDX SBOM come from allowed sources.
#   Example template for SBOM validation rules.
#
package package_sources

import rego.v1

# METADATA
# title: Allowed package sources
# description: >-
#   Verify that packages fetched by Hermeto come from allowed distribution URLs.
#   By default, no sources are allowed unless explicitly configured.
# custom:
#   short_name: allowed_package_sources
#   failure_msg: "Package %s was sourced from %s which is not allowed"
#   solution: >-
#     Update the build to fetch packages only from allowed sources.
#     Configure the allowed_package_sources rule data with permitted URL patterns.
deny contains result if {
	# Get CycloneDX SBOMs from attestations
	some att in input.attestations
	att.statement.predicateType == "https://cyclonedx.org/bom"
	sbom := att.statement.predicate

	# Find components with distribution references
	some component in sbom.components
	some ref in component.externalReferences
	ref.type == "distribution"

	# Only check components fetched by Hermeto
	some prop in component.properties
	prop.name == "hermeto:found_by"

	# Get the distribution URL and package identifier
	url := ref.url
	purl := component.purl

	# Check against allowed patterns from rule data
	allowed_patterns := object.get(data.rule_data, "allowed_package_sources", [])
	not _url_matches_allowed(url, allowed_patterns)

	# Construct the result
	result := {
		"code": "package_sources.allowed_package_sources",
		"msg": sprintf("Package %s was sourced from %s which is not allowed", [purl, url]),
		"severity": "failure",
		"term": purl,
	}
}

# Helper: check if URL matches any allowed pattern
_url_matches_allowed(url, patterns) if {
	some pattern in patterns
	regex.match(pattern, url)
}
