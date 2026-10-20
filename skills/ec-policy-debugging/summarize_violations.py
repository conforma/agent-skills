#!/usr/bin/env python3
"""
Summarize EC validation violations from a Conforma log file.

Supports two log formats:
1. TaskRun/PipelineRun format: JSON output with {"success"... structure
2. Text output format: Human-readable output with "Results:" section

Usage: python3 summarize_violations.py <LOG_FILE>
"""

import json
import re
import sys


def parse_json_format(content):
    """Parse JSON format from TaskRun/PipelineRun logs."""
    # Match JSON starting with {"success" until end of line with closing brace
    # The JSON is typically on a single line, or ends before STEP- markers
    match = re.search(r'(\{"success".*?)(?=\n\n|\nSTEP-|\nstep-|$)', content, re.DOTALL | re.IGNORECASE)
    if not match:
        return None

    json_str = match.group(1).strip()

    # Handle case where JSON might be multiline - find the balanced closing brace
    # For simple cases, the JSON ends at a single closing brace
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        # Try to find proper JSON boundary by counting braces
        brace_count = 0
        end_pos = 0
        for i, char in enumerate(json_str):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i + 1
                    break
        if end_pos > 0:
            try:
                data = json.loads(json_str[:end_pos])
            except json.JSONDecodeError:
                return None
        else:
            return None

    result = {
        'format': 'json',
        'success': data.get('success'),
        'components': [],
        'failures': {},
        'warnings': {}
    }

    for comp in data.get('components', []):
        comp_info = {
            'name': comp.get('name', 'unknown'),
            'image_ref': comp.get('containerImage', ''),
            'violations': len(comp.get('violations', [])),
            'warnings': len(comp.get('warnings', []))
        }
        result['components'].append(comp_info)

        for v in comp.get('violations', []):
            code = v.get('metadata', {}).get('code', 'unknown')
            msg = v.get('msg', '')[:100]
            image_ref = comp.get('containerImage', '')
            if code not in result['failures']:
                result['failures'][code] = {'count': 0, 'sample': msg, 'image_refs': []}
            result['failures'][code]['count'] += 1
            if image_ref and image_ref not in result['failures'][code]['image_refs']:
                result['failures'][code]['image_refs'].append(image_ref)

        for w in comp.get('warnings', []):
            code = w.get('metadata', {}).get('code', 'unknown')
            msg = w.get('msg', '')[:100]
            image_ref = comp.get('containerImage', '')
            if code not in result['warnings']:
                result['warnings'][code] = {'count': 0, 'sample': msg, 'image_refs': []}
            result['warnings'][code]['count'] += 1
            if image_ref and image_ref not in result['warnings'][code]['image_refs']:
                result['warnings'][code]['image_refs'].append(image_ref)

    return result


def parse_text_format(content):
    """Parse text output format from Conforma validation."""
    # Check for text format markers
    if not re.search(r'^Results:', content, re.MULTILINE):
        return None

    result = {
        'format': 'text',
        'success': None,
        'components': [],
        'failures': {},
        'warnings': {}
    }

    # Parse header
    success_match = re.search(r'^Success:\s*(true|false)', content, re.MULTILINE | re.IGNORECASE)
    if success_match:
        result['success'] = success_match.group(1).lower() == 'true'

    # Parse components section
    components_match = re.search(r'Components:\n(.*?)\nResults:', content, re.DOTALL)
    if components_match:
        comp_section = components_match.group(1)
        # Match component entries - format: "- Name: ...\n  ImageRef: ...\n  Violations: X, Warnings: Y, Successes: Z"
        comp_pattern = re.compile(
            r'-\s*Name:\s*(.+?)\n\s+ImageRef:\s*(.+?)\n\s+Violations:\s*(\d+),\s*Warnings:\s*(\d+)',
            re.MULTILINE
        )
        for match in comp_pattern.finditer(comp_section):
            result['components'].append({
                'name': match.group(1).strip(),
                'image_ref': match.group(2).strip(),
                'violations': int(match.group(3)),
                'warnings': int(match.group(4))
            })

    # Parse results section - find all violations and warnings
    # Use line-by-line parsing for more reliable extraction
    lines = content.split('\n')
    in_results = False
    current_block = None

    for line in lines:
        if line.startswith('Results:'):
            in_results = True
            continue

        if not in_results:
            continue

        if line.startswith('For more information') or line.startswith('Error:'):
            break

        # Check for violation/warning/success markers (Unicode or ASCII)
        violation_match = re.match(r'^[✕xX]\s*\[Violation\]\s*(\S+)', line)
        warning_match = re.match(r'^[!]\s*\[Warning\]\s*(\S+)', line)

        if violation_match:
            code = violation_match.group(1)
            if code not in result['failures']:
                result['failures'][code] = {'count': 0, 'sample': '', 'image_refs': []}
            result['failures'][code]['count'] += 1
            current_block = ('failure', code)
        elif warning_match:
            code = warning_match.group(1)
            if code not in result['warnings']:
                result['warnings'][code] = {'count': 0, 'sample': '', 'image_refs': []}
            result['warnings'][code]['count'] += 1
            current_block = ('warning', code)
        elif current_block:
            block_type, code = current_block
            storage = result['failures'] if block_type == 'failure' else result['warnings']

            # Extract ImageRef
            image_match = re.match(r'\s+ImageRef:\s*(.+)', line)
            if image_match:
                image_ref = image_match.group(1).strip()
                if image_ref not in storage[code]['image_refs']:
                    storage[code]['image_refs'].append(image_ref)

            # Extract Reason (first line of reason as sample)
            reason_match = re.match(r'\s+Reason:\s*(.+)', line)
            if reason_match and not storage[code]['sample']:
                storage[code]['sample'] = reason_match.group(1).strip()[:100]

    return result


def parse_log_file(content):
    """Parse log file, auto-detecting format."""
    # Try JSON format first
    result = parse_json_format(content)
    if result:
        return result

    # Try text format
    result = parse_text_format(content)
    if result:
        return result

    return None


def print_summary(result):
    """Print a summary of the parsed results."""
    print(f"Format: {result['format']}")
    print(f"Success: {result['success']}")
    print(f"Components: {len(result['components'])}")
    print()

    # Print failures
    print("=== FAILURES ===")
    if not result['failures']:
        print("None")
    else:
        for code, info in sorted(result['failures'].items(), key=lambda x: -x[1]['count']):
            print(f"{info['count']:3d}x {code}")
            print(f"     {info['sample']}...")
            print()

    # Print warnings
    print("=== WARNINGS ===")
    if not result['warnings']:
        print("None")
    else:
        for code, info in sorted(result['warnings'].items(), key=lambda x: -x[1]['count']):
            print(f"{info['count']:3d}x {code}")
            print(f"     {info['sample']}...")
            print()

    # Print affected components
    print("=== AFFECTED COMPONENTS ===")
    for comp in result['components']:
        if comp['violations'] > 0 or comp['warnings'] > 0:
            print(f"{comp['name']}: {comp['violations']} failures, {comp['warnings']} warnings")
            if comp.get('image_ref'):
                print(f"  {comp['image_ref']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 summarize_violations.py <LOG_FILE>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        content = f.read()

    result = parse_log_file(content)
    if not result:
        print("Could not parse log file. Supported formats:")
        print("  - TaskRun/PipelineRun JSON format (contains {\"success\"...)")
        print("  - Text output format (contains 'Results:' section)")
        sys.exit(1)

    print_summary(result)


if __name__ == '__main__':
    main()
