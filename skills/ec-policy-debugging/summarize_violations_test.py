#!/usr/bin/env python3
"""
Tests for summarize_violations.py

Run with: pytest summarize_violations_test.py -v

Test categories:
- TestParseJsonFormat: JSON format parsing (TaskRun/PipelineRun logs)
- TestParseTextFormat: Text format parsing (ec validate output)
- TestParseLogFile: Format auto-detection
- TestEdgeCases: Empty input, malformed data, edge conditions
"""

import pytest
from summarize_violations import parse_json_format, parse_text_format, parse_log_file


# =============================================================================
# JSON Format Tests
# =============================================================================

class TestParseJsonFormat:
    def test_basic_json_with_violations(self):
        content = '{"success":false,"components":[{"name":"my-app","containerImage":"quay.io/org/app@sha256:abc123","violations":[{"msg":"Image not signed","metadata":{"code":"signature.valid"}}],"warnings":[]}]}'

        result = parse_json_format(content)

        assert result is not None
        assert result['format'] == 'json'
        assert result['success'] is False
        assert len(result['components']) == 1
        assert result['components'][0]['name'] == 'my-app'
        assert result['components'][0]['violations'] == 1
        assert result['components'][0]['warnings'] == 0
        assert 'signature.valid' in result['failures']
        assert result['failures']['signature.valid']['count'] == 1

    def test_json_with_warnings(self):
        content = '{"success":true,"components":[{"name":"my-app","containerImage":"quay.io/org/app@sha256:abc","violations":[],"warnings":[{"msg":"Task outdated","metadata":{"code":"trusted_task.current"}}]}]}'

        result = parse_json_format(content)

        assert result is not None
        assert result['success'] is True
        assert len(result['warnings']) == 1
        assert 'trusted_task.current' in result['warnings']

    def test_json_multiple_components(self):
        content = '{"success":false,"components":[{"name":"app1","containerImage":"img1","violations":[{"msg":"err1","metadata":{"code":"rule.one"}}],"warnings":[]},{"name":"app2","containerImage":"img2","violations":[{"msg":"err2","metadata":{"code":"rule.two"}}],"warnings":[]}]}'

        result = parse_json_format(content)

        assert result is not None
        assert len(result['components']) == 2
        assert len(result['failures']) == 2
        assert result['failures']['rule.one']['count'] == 1
        assert result['failures']['rule.two']['count'] == 1

    def test_json_same_violation_multiple_components(self):
        content = '{"success":false,"components":[{"name":"app1","containerImage":"img1","violations":[{"msg":"err","metadata":{"code":"same.rule"}}],"warnings":[]},{"name":"app2","containerImage":"img2","violations":[{"msg":"err","metadata":{"code":"same.rule"}}],"warnings":[]}]}'

        result = parse_json_format(content)

        assert result is not None
        assert result['failures']['same.rule']['count'] == 2
        assert len(result['failures']['same.rule']['image_refs']) == 2

    def test_json_embedded_in_log(self):
        content = '''STEP-INITIALIZE
Some output here

STEP-VALIDATE
{"success":false,"components":[{"name":"test","containerImage":"img","violations":[{"msg":"fail","metadata":{"code":"test.rule"}}],"warnings":[]}]}

STEP-SUMMARY
More output
'''
        result = parse_json_format(content)

        assert result is not None
        assert result['success'] is False
        assert 'test.rule' in result['failures']

    def test_json_with_extra_data_after(self):
        content = '{"success":true,"components":[]}\n\n{"other":"json"}'

        result = parse_json_format(content)

        assert result is not None
        assert result['success'] is True

    def test_no_json_returns_none(self):
        content = 'This is just plain text with no JSON'

        result = parse_json_format(content)

        assert result is None

    def test_malformed_json_returns_none(self):
        content = '{"success":false,"components":[{broken'

        result = parse_json_format(content)

        assert result is None

    def test_json_empty_components(self):
        content = '{"success":true,"components":[]}'

        result = parse_json_format(content)

        assert result is not None
        assert result['success'] is True
        assert len(result['components']) == 0
        assert len(result['failures']) == 0


# =============================================================================
# Text Format Tests
# =============================================================================

class TestParseTextFormat:
    def test_basic_text_with_violations(self):
        content = '''Success: false
Result: FAILURE
Violations: 2, Warnings: 0, Successes: 5

Components:
- Name: my-app
  ImageRef: quay.io/org/app@sha256:abc123
  Violations: 2, Warnings: 0, Successes: 5

Results:
✕ [Violation] registry.approved
  ImageRef: quay.io/org/app@sha256:abc123
  Reason: Image from unapproved registry
  Title: Approved registries

✕ [Violation] signature.valid
  ImageRef: quay.io/org/app@sha256:abc123
  Reason: Image not signed
  Title: Valid signature

For more information see docs
'''
        result = parse_text_format(content)

        assert result is not None
        assert result['format'] == 'text'
        assert result['success'] is False
        assert len(result['components']) == 1
        assert result['components'][0]['name'] == 'my-app'
        assert len(result['failures']) == 2
        assert 'registry.approved' in result['failures']
        assert 'signature.valid' in result['failures']

    def test_text_with_warnings(self):
        content = '''Success: true
Result: WARNING
Violations: 0, Warnings: 1, Successes: 10

Components:
- Name: my-app
  ImageRef: quay.io/org/app@sha256:abc
  Violations: 0, Warnings: 1, Successes: 10

Results:
! [Warning] trusted_task.current
  ImageRef: quay.io/org/app@sha256:abc
  Reason: Task version outdated
  Title: Current task versions

For more information see docs
'''
        result = parse_text_format(content)

        assert result is not None
        assert result['success'] is True
        assert len(result['warnings']) == 1
        assert 'trusted_task.current' in result['warnings']

    def test_text_multiple_components(self):
        content = '''Success: false
Violations: 2, Warnings: 0

Components:
- Name: app1
  ImageRef: img1
  Violations: 1, Warnings: 0, Successes: 5

- Name: app2
  ImageRef: img2
  Violations: 1, Warnings: 0, Successes: 5

Results:
✕ [Violation] test.rule
  ImageRef: img1
  Reason: Failed

✕ [Violation] test.rule
  ImageRef: img2
  Reason: Failed

For more information see docs
'''
        result = parse_text_format(content)

        assert result is not None
        assert len(result['components']) == 2
        assert result['failures']['test.rule']['count'] == 2
        assert len(result['failures']['test.rule']['image_refs']) == 2

    def test_text_extracts_reason_as_sample(self):
        content = '''Success: false

Components:
- Name: app
  ImageRef: img
  Violations: 1, Warnings: 0

Results:
✕ [Violation] my.rule
  ImageRef: img
  Reason: This is the error message
  Title: My Rule

For more information see docs
'''
        result = parse_text_format(content)

        assert result is not None
        assert result['failures']['my.rule']['sample'] == 'This is the error message'

    def test_text_no_results_section_returns_none(self):
        content = '''Success: true
Components:
- Name: app
  ImageRef: img
  Violations: 0, Warnings: 0
'''
        result = parse_text_format(content)

        assert result is None

    def test_text_with_x_marker(self):
        """Test that X and x work as violation markers (ASCII fallback)"""
        content = '''Success: false

Components:
- Name: app
  ImageRef: img
  Violations: 1, Warnings: 0

Results:
X [Violation] ascii.marker
  ImageRef: img
  Reason: Using ASCII X

For more information see docs
'''
        result = parse_text_format(content)

        assert result is not None
        assert 'ascii.marker' in result['failures']


# =============================================================================
# Auto-detection Tests
# =============================================================================

class TestParseLogFile:
    def test_prefers_json_over_text(self):
        content = '''{"success":false,"components":[{"name":"json-app","containerImage":"img","violations":[{"msg":"err","metadata":{"code":"json.rule"}}],"warnings":[]}]}

Results:
✕ [Violation] text.rule
  ImageRef: img
  Reason: Text violation
'''
        result = parse_log_file(content)

        assert result is not None
        assert result['format'] == 'json'
        assert 'json.rule' in result['failures']

    def test_falls_back_to_text(self):
        content = '''Success: false

Components:
- Name: app
  ImageRef: img
  Violations: 1, Warnings: 0

Results:
✕ [Violation] text.rule
  ImageRef: img
  Reason: Text only

For more information see docs
'''
        result = parse_log_file(content)

        assert result is not None
        assert result['format'] == 'text'

    def test_returns_none_for_unparseable(self):
        content = 'Random content with no recognizable format'

        result = parse_log_file(content)

        assert result is None


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    def test_empty_content(self):
        result = parse_log_file('')
        assert result is None

    def test_json_no_violations_or_warnings(self):
        content = '{"success":true,"components":[{"name":"clean-app","containerImage":"img","violations":[],"warnings":[]}]}'

        result = parse_json_format(content)

        assert result is not None
        assert result['success'] is True
        assert len(result['failures']) == 0
        assert len(result['warnings']) == 0
        assert result['components'][0]['violations'] == 0

    def test_text_success_true(self):
        content = '''Success: true
Result: SUCCESS
Violations: 0, Warnings: 0, Successes: 10

Components:
- Name: app
  ImageRef: img
  Violations: 0, Warnings: 0, Successes: 10

Results:

For more information see docs
'''
        result = parse_text_format(content)

        assert result is not None
        assert result['success'] is True
        assert len(result['failures']) == 0

    def test_long_message_truncated(self):
        long_msg = 'x' * 200
        content = f'{{"success":false,"components":[{{"name":"app","containerImage":"img","violations":[{{"msg":"{long_msg}","metadata":{{"code":"test.rule"}}}}],"warnings":[]}}]}}'

        result = parse_json_format(content)

        assert result is not None
        assert len(result['failures']['test.rule']['sample']) == 100

    def test_missing_metadata_code(self):
        content = '{"success":false,"components":[{"name":"app","containerImage":"img","violations":[{"msg":"error","metadata":{}}],"warnings":[]}]}'

        result = parse_json_format(content)

        assert result is not None
        assert 'unknown' in result['failures']

    def test_unicode_markers_in_text(self):
        """Test various Unicode markers that might appear in output"""
        content = '''Success: false

Components:
- Name: app
  ImageRef: img
  Violations: 1, Warnings: 0

Results:
✕ [Violation] unicode.test
  ImageRef: img
  Reason: Unicode marker test

For more information see docs
'''
        result = parse_text_format(content)

        assert result is not None
        assert 'unicode.test' in result['failures']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
