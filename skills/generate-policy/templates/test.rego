#
# METADATA
# title: Package Source Validation Tests
# description: >-
#   Tests for the package_sources policy rule.
#
package package_sources_test

import rego.v1

import data.package_sources

# =============================================================================
# Mock Data Helpers
# =============================================================================

# Helper: Create a CycloneDX attestation with components
_mock_attestation(components) := {
	"statement": {
		"predicateType": "https://cyclonedx.org/bom",
		"predicate": {
			"bomFormat": "CycloneDX",
			"specVersion": "1.5",
			"components": components,
		},
	},
}

# Helper: Create a component with Hermeto marker
_mock_component(purl, distribution_url) := {
	"type": "library",
	"purl": purl,
	"externalReferences": [{"type": "distribution", "url": distribution_url}],
	"properties": [{"name": "hermeto:found_by", "value": "hermeto"}],
}

# Helper: Create a component without Hermeto marker
_mock_component_no_hermeto(purl, distribution_url) := {
	"type": "library",
	"purl": purl,
	"externalReferences": [{"type": "distribution", "url": distribution_url}],
	"properties": [],
}

# =============================================================================
# Pass Cases - No Violations Expected
# =============================================================================

test_allowed_source_passes if {
	components := [_mock_component(
		"pkg:npm/lodash@4.17.21",
		"https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz",
	)]
	attestations := [_mock_attestation(components)]

	count(package_sources.deny) == 0
		with input.attestations as attestations
		with data.rule_data.allowed_package_sources as ["^https://registry\\.npmjs\\.org/"]
}

test_multiple_allowed_patterns if {
	components := [
		_mock_component("pkg:npm/pkg1@1.0.0", "https://registry.npmjs.org/pkg1.tgz"),
		_mock_component("pkg:golang/pkg2@1.0.0", "https://proxy.golang.org/pkg2.zip"),
	]
	attestations := [_mock_attestation(components)]

	count(package_sources.deny) == 0
		with input.attestations as attestations
		with data.rule_data.allowed_package_sources as [
			"^https://registry\\.npmjs\\.org/",
			"^https://proxy\\.golang\\.org/",
		]
}

# =============================================================================
# Fail Cases - Violations Expected
# =============================================================================

test_disallowed_source_fails if {
	components := [_mock_component(
		"pkg:npm/malicious@1.0.0",
		"https://evil.com/malicious-1.0.0.tgz",
	)]
	attestations := [_mock_attestation(components)]

	count(package_sources.deny) == 1
		with input.attestations as attestations
		with data.rule_data.allowed_package_sources as ["^https://registry\\.npmjs\\.org/"]
}

test_empty_allowed_sources_denies_all if {
	components := [_mock_component(
		"pkg:npm/lodash@4.17.21",
		"https://registry.npmjs.org/lodash.tgz",
	)]
	attestations := [_mock_attestation(components)]

	count(package_sources.deny) == 1
		with input.attestations as attestations
		with data.rule_data.allowed_package_sources as []
}

# =============================================================================
# Edge Cases
# =============================================================================

test_no_attestations if {
	count(package_sources.deny) == 0
		with input.attestations as []
		with data.rule_data.allowed_package_sources as []
}

test_non_hermeto_component_skipped if {
	components := [_mock_component_no_hermeto(
		"pkg:npm/lodash@4.17.21",
		"https://evil.com/lodash.tgz",
	)]
	attestations := [_mock_attestation(components)]

	# Should pass because non-Hermeto components are not checked
	count(package_sources.deny) == 0
		with input.attestations as attestations
		with data.rule_data.allowed_package_sources as ["^https://registry\\.npmjs\\.org/"]
}

test_component_without_distribution_ref_skipped if {
	components := [{
		"type": "library",
		"purl": "pkg:npm/lodash@4.17.21",
		"externalReferences": [{"type": "vcs", "url": "https://github.com/lodash/lodash"}],
		"properties": [{"name": "hermeto:found_by", "value": "hermeto"}],
	}]
	attestations := [_mock_attestation(components)]

	count(package_sources.deny) == 0
		with input.attestations as attestations
		with data.rule_data.allowed_package_sources as ["^https://registry\\.npmjs\\.org/"]
}

# =============================================================================
# Multiple Items
# =============================================================================

test_multiple_components_mixed_results if {
	components := [
		_mock_component("pkg:npm/good@1.0.0", "https://registry.npmjs.org/good.tgz"),
		_mock_component("pkg:npm/bad@1.0.0", "https://evil.com/bad.tgz"),
	]
	attestations := [_mock_attestation(components)]

	count(package_sources.deny) == 1
		with input.attestations as attestations
		with data.rule_data.allowed_package_sources as ["^https://registry\\.npmjs\\.org/"]
}

# =============================================================================
# Violation Content
# =============================================================================

test_violation_contains_purl_and_url if {
	components := [_mock_component(
		"pkg:npm/bad@1.0.0",
		"https://evil.com/bad.tgz",
	)]
	attestations := [_mock_attestation(components)]

	result := package_sources.deny
		with input.attestations as attestations
		with data.rule_data.allowed_package_sources as []

	count(result) == 1
	some violation in result
	contains(violation.msg, "pkg:npm/bad@1.0.0")
	contains(violation.msg, "https://evil.com/bad.tgz")
	violation.code == "package_sources.allowed_package_sources"
}
