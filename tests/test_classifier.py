"""Tests for license classifier."""
from licenselens.classifier import (
    KNOWN_LICENSES,
    check_compatibility,
    classify_license,
    find_conflicts,
)
from licenselens.models import Dependency, Ecosystem, LicenseCategory, Severity


def test_classify_known_licenses():
    """Test classifying known licenses."""
    lic = classify_license("MIT")
    assert lic.spdx_id == "MIT"
    assert lic.category == LicenseCategory.PERMISSIVE
    assert lic.is_osi_approved is True

    lic = classify_license("GPL-3.0")
    assert lic.category == LicenseCategory.STRONG_COPYLEFT

    lic = classify_license("AGPL-3.0")
    assert lic.category == LicenseCategory.NETWORK_COPYLEFT

    lic = classify_license("LGPL-2.1")
    assert lic.category == LicenseCategory.WEAK_COPYLEFT


def test_classify_unknown_license():
    """Test classifying unknown license."""
    lic = classify_license("SomeWeirdLicense-1.0")
    assert lic.category == LicenseCategory.UNKNOWN
    assert lic.spdx_id == "SomeWeirdLicense-1.0"


def test_classify_case_insensitive():
    """Test case-insensitive classification."""
    lic = classify_license("mit")
    assert lic.spdx_id == "MIT"

    lic = classify_license("MIT")
    assert lic.spdx_id == "MIT"


def test_known_licenses_count():
    """Test that we have a reasonable number of known licenses."""
    assert len(KNOWN_LICENSES) >= 20


def test_compatibility_permissive():
    """Test compatibility between permissive licenses."""
    compatible, notes = check_compatibility("MIT", "MIT")
    assert compatible is True

    compatible, notes = check_compatibility("MIT", "Apache-2.0")
    assert compatible is True

    compatible, notes = check_compatibility("MIT", "BSD-3-Clause")
    assert compatible is True


def test_compatibility_copyleft():
    """Test compatibility with copyleft licenses."""
    compatible, notes = check_compatibility("MIT", "GPL-2.0")
    assert compatible is True

    compatible, notes = check_compatibility("Apache-2.0", "GPL-2.0")
    assert compatible is False

    compatible, notes = check_compatibility("Apache-2.0", "GPL-3.0")
    assert compatible is True


def test_compatibility_gpl_versions():
    """Test GPL version incompatibility."""
    compatible, notes = check_compatibility("GPL-2.0", "GPL-3.0")
    assert compatible is False


def test_compatibility_unknown():
    """Test unknown license compatibility."""
    compatible, notes = check_compatibility("MIT", "SomeWeirdLicense")
    assert compatible is None


def test_compatibility_reverse_order():
    """Test that compatibility works in both orderings."""
    compatible, _ = check_compatibility("MIT", "Apache-2.0")
    compatible_rev, _ = check_compatibility("Apache-2.0", "MIT")
    assert compatible == compatible_rev


def test_find_conflicts_no_conflicts():
    """Test conflict detection with compatible licenses."""
    deps = [
        Dependency(name="a", version="1.0", ecosystem=Ecosystem.PYTHON, license_id="MIT"),
        Dependency(name="b", version="2.0", ecosystem=Ecosystem.PYTHON, license_id="Apache-2.0"),
        Dependency(name="c", version="3.0", ecosystem=Ecosystem.PYTHON, license_id="BSD-3-Clause"),
    ]
    conflicts = find_conflicts(deps)
    # No conflicts between permissive licenses
    error_conflicts = [c for c in conflicts if c.severity == Severity.ERROR]
    assert len(error_conflicts) == 0


def test_find_conflicts_with_conflicts():
    """Test conflict detection with incompatible licenses."""
    deps = [
        Dependency(name="a", version="1.0", ecosystem=Ecosystem.PYTHON, license_id="Apache-2.0"),
        Dependency(name="b", version="2.0", ecosystem=Ecosystem.PYTHON, license_id="GPL-2.0"),
    ]
    conflicts = find_conflicts(deps)
    assert len(conflicts) >= 1
    error_conflicts = [c for c in conflicts if c.severity == Severity.ERROR]
    assert len(error_conflicts) == 1
    assert error_conflicts[0].license_a == "Apache-2.0"
    assert error_conflicts[0].license_b == "GPL-2.0"


def test_find_conflicts_empty():
    """Test conflict detection with no licenses."""
    deps = [
        Dependency(name="a", version="1.0", ecosystem=Ecosystem.PYTHON, license_id="UNKNOWN"),
    ]
    conflicts = find_conflicts(deps)
    assert len(conflicts) == 0


def test_find_conflicts_single_license():
    """Test conflict detection with single license."""
    deps = [
        Dependency(name="a", version="1.0", ecosystem=Ecosystem.PYTHON, license_id="MIT"),
    ]
    conflicts = find_conflicts(deps)
    assert len(conflicts) == 0
