"""Tests for data models."""

from licenselens.models import (
    AuditReport,
    AuditSummary,
    Dependency,
    Ecosystem,
    License,
    LicenseCategory,
    Severity,
)


def test_dependency_creation():
    dep = Dependency(
        name="requests",
        version="2.28.0",
        ecosystem=Ecosystem.PYTHON,
        license_id="Apache-2.0",
    )
    assert dep.name == "requests"
    assert dep.ecosystem == Ecosystem.PYTHON
    assert dep.is_direct is True


def test_dependency_defaults():
    dep = Dependency(name="foo", version="1.0", ecosystem=Ecosystem.NODE)
    assert dep.license_id == ""
    assert dep.license_category == LicenseCategory.UNKNOWN
    assert dep.is_direct is True


def test_license_creation():
    lic = License(
        spdx_id="MIT",
        name="MIT License",
        category=LicenseCategory.PERMISSIVE,
        is_osi_approved=True,
    )
    assert lic.spdx_id == "MIT"
    assert lic.category == LicenseCategory.PERMISSIVE


def test_severity_levels():
    assert Severity.INFO.value == "info"
    assert Severity.WARNING.value == "warning"
    assert Severity.ERROR.value == "error"
    assert Severity.CRITICAL.value == "critical"


def test_ecosystem_values():
    assert Ecosystem.PYTHON.value == "python"
    assert Ecosystem.NODE.value == "node"
    assert Ecosystem.GO.value == "go"
    assert Ecosystem.RUST.value == "rust"


def test_audit_summary_defaults():
    s = AuditSummary()
    assert s.total_dependencies == 0
    assert s.licenses_found == {}
    assert s.categories == {}


def test_audit_report_defaults():
    r = AuditReport(project_name="test", summary=AuditSummary())
    assert r.project_name == "test"
    assert r.dependencies == []
    assert r.issues == []
    assert r.conflicts == []
