"""Offline checks for the portable skill catalog and its bundled helper."""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
EXPECTED_SKILLS = {
    "capture-context",
    "ec-debug-violations",
    "ec-policy-debugging",
    "ec-setup",
    "generate-policy",
    "groom",
    "mid-sprint-add",
    "renovate-act",
    "renovate-triage",
    "scaffold-repo",
    "sprint-report",
    "sprint-triage",
    "write-rule",
}


def markdown_links_exist(markdown_root):
    link_pattern = re.compile(r"\[[^\]\n]*\]\(([^\s)]+)\)")
    missing = []
    for document in markdown_root.rglob("*.md"):
        text = document.read_text(encoding="utf-8")
        for match in link_pattern.finditer(text):
            target = match.group(1).split("#", 1)[0]
            if (
                not target
                or target.startswith(("http:", "https:", "mailto:", "#", "~/"))
                or "{" in target
                or "<" in target
            ):
                continue
            if not (document.parent / target).exists():
                line = text.count("\n", 0, match.start()) + 1
                missing.append(f"{document.relative_to(markdown_root)}:{line}: {target}")
    return missing


def assert_skill_catalog(skills_root):
    skill_dirs = {
        path.parent.name for path in skills_root.rglob("SKILL.md")
    }
    assert skill_dirs == EXPECTED_SKILLS

    for skill_dir in skills_root.iterdir():
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").is_file():
            continue
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", content, re.DOTALL)
        assert match, f"{skill_dir.name}: missing frontmatter"
        fields = {}
        for line in match.group(1).splitlines():
            key, separator, value = line.partition(":")
            assert separator and value.strip(), f"{skill_dir.name}: invalid metadata: {line}"
            assert key not in fields, f"{skill_dir.name}: duplicate metadata field {key}"
            fields[key] = value.strip()
        assert set(fields) == {"name", "description"}, (skill_dir.name, fields)
        assert fields["name"] == skill_dir.name
        assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fields["name"])
        assert len(fields["name"]) <= 64
        assert len(fields["description"]) <= 1024

    missing_links = markdown_links_exist(skills_root)
    assert not missing_links, missing_links


def test_skill_catalog_and_local_links():
    assert_skill_catalog(SKILLS)
    missing_links = markdown_links_exist(ROOT)
    assert not missing_links, missing_links
    instructions = "\n".join(
        path.read_text(encoding="utf-8") for path in SKILLS.rglob("*.md")
    )
    for harness_only in (
        "$ARGUMENTS",
        "allowed-tools:",
        "argument-hint:",
        "WebFetch",
        "/install-plugin",
        "~/.claude/",
        ".claude/settings.json",
        "CLAUDE.md",
    ):
        assert harness_only not in instructions, harness_only
    slash_command = re.compile(
        r"(?<![A-Za-z0-9_./-])/(?:ec-[a-z-]+|groom|mid-sprint-add|"
        r"renovate-(?:act|triage)|scaffold-repo|sprint-(?:report|triage)|"
        r"write-rule|generate-policy)(?=\b|\s)"
    )
    assert not slash_command.search(instructions)
    assert "mcp__work-assistant__jira_sprint_issues" in instructions
    assert "mcp__work-assistant__jira_get_issue" in instructions

    renovate_triage = (SKILLS / "renovate-triage" / "SKILL.md").read_text(encoding="utf-8")
    renovate_act = (SKILLS / "renovate-act" / "SKILL.md").read_text(encoding="utf-8")
    sprint_report = (SKILLS / "sprint-report" / "SKILL.md").read_text(encoding="utf-8")
    assert ".conforma/reports/" in renovate_triage
    assert ".conforma/reports/" in renovate_act
    assert ".claude/reports/" in renovate_act
    assert "same basename" in renovate_act
    assert ".conforma/reports/" in sprint_report
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "skills/ec-policy-debugging /path/to/agent-skills/skills/ec-setup" in readme
    assert "If `--report <path>` was provided" in renovate_act
    assert "Find the generated table row matching both the repository and PR number" in renovate_act
    triage_rules = (SKILLS / "renovate-triage" / "references" / "triage-rules.md").read_text(encoding="utf-8")
    assert 'Compare each PR\'s extracted `base_branch`' in triage_rules
    assert "skip comparing it with `baseBranchPatterns`" in renovate_triage
    assert 'The independent title suffix signal still applies' in triage_rules


def test_helper_runs_from_a_relocated_collection_and_other_working_directory():
    json_log = (
        '{"success":false,"components":[{"name":"app",'
        '"containerImage":"image-ref","violations":[{"msg":"blocked",'
        '"metadata":{"code":"test.rule"}}],"warnings":[]}]}'
    )
    text_log = """Success: false

Components:
- Name: app
  ImageRef: image-ref
  Violations: 1, Warnings: 0, Successes: 0

Results:
✕ [Violation] text.rule
  ImageRef: image-ref
  Reason: blocked

For more information see docs
"""

    with tempfile.TemporaryDirectory(prefix="skill portability ") as temporary:
        temporary_path = Path(temporary)
        copied_skills = temporary_path / "collection with spaces" / "skills"
        shutil.copytree(
            SKILLS,
            copied_skills,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        working_directory = temporary_path / "unrelated working directory"
        working_directory.mkdir()
        helper = copied_skills / "ec-policy-debugging" / "summarize_violations.py"

        cases = (
            (json_log, "input.json", ("Format: json", "test.rule")),
            (text_log, "input.log", ("Format: text", "text.rule")),
        )
        for log, filename, expected in cases:
            log_path = temporary_path / filename
            log_path.write_text(log, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(helper), str(log_path)],
                cwd=working_directory,
                check=True,
                capture_output=True,
                text=True,
            )
            for value in expected:
                assert value in result.stdout

        assert_skill_catalog(copied_skills)
