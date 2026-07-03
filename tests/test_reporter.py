"""Tests for reporter."""

from licenselens.models import (
    AuditReport,
    AuditSummary,
    Dependency,
    Ecosystem,
    LicenseCategory,
    LicenseConflict,
    LicenseIssue,
    Severity,
)
from licenselens.reporter import (
    FORMATTERS,
    format_csv,
    format_json,
    format_markdown,
    format_text,
)


def _make_report():
    """Create a sample audit report for testing."""
    deps = [
        Dependency(
            name="requests",
            version="2.28.0",
            ecosystem=Ecosystem.PYTHON,
            license_id="Apache-2.0",
            license_name="Apache License 2.0",
            license_category=LicenseCategory.PERMISSIVE,
            is_direct=True,
        ),
        Dependency(
            name="flask",
            version="2.3.0",
            ecosystem=Ecosystem.PYTHON,
            license_id="BSD-3-Clause",
            license_name="BSD 3-Clause License",
            license_category=LicenseCategory.PERMISSIVE,
            is_direct=True,
        ),
        Dependency(
            name="sqlalchemy",
            version="2.0",
            ecosystem=Ecosystem.PYTHON,
            license_id="MIT",
            license_name="MIT License",
            license_category=LicenseCategory.PERMISSIVE,
            is_direct=True,
        ),
    ]

    issues = [
        LicenseIssue(
            severity=Severity.WARNING,
            dependency=deps[0],
            message="License not detected for some-lib",
            rule_id="UNKNOWN_LICENSE",
        ),
    ]

    conflicts = [
        LicenseConflict(
            license_a="Apache-2.0",
            license_b="GPL-2.0",
            message="Apache 2.0 patent clauses incompatible with GPL-2.0",
            severity=Severity.ERROR,
        ),
    ]

    summary = AuditSummary(
        total_dependencies=3,
        direct_dependencies=3,
        transitive_dependencies=0,
        licenses_found={"Apache-2.0": 1, "BSD-3-Clause": 1, "MIT": 1},
        categories={"permissive": 3},
        issues_count=1,
        conflicts_count=1,
        ecosystems={"python": 3},
    )

    return AuditReport(
        project_name="test-project",
        summary=summary,
        dependencies=deps,
        issues=issues,
        conflicts=conflicts,
        warnings=["1 dependencies have unknown licenses"],
    )


def test_format_text():
    """Test text formatting."""
    report = _make_report()
    text = format_text(report)

    assert "test-project" in text
    assert "Total dependencies:     3" in text
    assert "Apache-2.0" in text
    assert "Flask" not in text  # Should use license ID, not name


def test_format_markdown():
    """Test markdown formatting."""
    report = _make_report()
    md = format_markdown(report)

    assert "# License Audit: test-project" in md
    assert "| Total dependencies | 3 |" in md
    assert "Apache-2.0" in md


def test_format_json():
    """Test JSON formatting."""
    report = _make_report()
    json_str = format_json(report)

    import json

    data = json.loads(json_str)

    assert data["project_name"] == "test-project"
    assert data["summary"]["total_dependencies"] == 3
    assert len(data["dependencies"]) == 3
    assert len(data["issues"]) == 1
    assert len(data["conflicts"]) == 1


def test_format_csv():
    """Test CSV formatting."""
    report = _make_report()
    csv_str = format_csv(report)

    lines = csv_str.split("\n")
    assert lines[0] == "name,version,license_id,license_category,ecosystem,type,source_file"
    assert len(lines) == 4  # header + 3 deps


def test_format_text_empty_report():
    """Test text formatting with empty report."""
    report = AuditReport(
        project_name="empty",
        summary=AuditSummary(),
    )
    text = format_text(report)

    assert "empty" in text
    assert "Total dependencies:     0" in text


def test_formatters_registry():
    """Test that all formatters are registered."""
    assert "text" in FORMATTERS
    assert "markdown" in FORMATTERS
    assert "json" in FORMATTERS
    assert "csv" in FORMATTERS
    assert len(FORMATTERS) == 4


def test_format_markdown_conflicts():
    """Test markdown formatting includes conflicts."""
    report = _make_report()
    md = format_markdown(report)

    assert "Apache-2.0" in md
    assert "GPL-2.0" in md
    assert "incompatible" in md.lower()


def test_format_json_structure():
    """Test JSON output has correct structure."""
    report = _make_report()
    import json

    data = json.loads(format_json(report))

    assert "project_name" in data
    assert "summary" in data
    assert "dependencies" in data
    assert "issues" in data
    assert "conflicts" in data
    assert "warnings" in data

    dep = data["dependencies"][0]
    assert "name" in dep
    assert "version" in dep
    assert "license_id" in dep
    assert "ecosystem" in dep
