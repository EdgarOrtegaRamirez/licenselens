"""Main analysis engine for LicenseLens."""

from __future__ import annotations

from pathlib import Path

from licenselens.classifier import classify_license, find_conflicts
from licenselens.models import (
    AuditReport,
    AuditSummary,
    Dependency,
    Ecosystem,
    LicenseCategory,
    LicenseIssue,
    Severity,
)
from licenselens.parser.base import BaseParser
from licenselens.parser.go import GoParser
from licenselens.parser.node import NodeParser
from licenselens.parser.python import PythonParser
from licenselens.parser.rust import RustParser
from licenselens.resolver import resolve_licenses

ALL_PARSERS: list[BaseParser] = [
    PythonParser(),
    NodeParser(),
    GoParser(),
    RustParser(),
]


def detect_ecosystem(project_dir: Path) -> list[Ecosystem]:
    """Detect which ecosystems are present in the project directory."""
    ecosystems = []
    for parser in ALL_PARSERS:
        files = parser.find_files(project_dir)
        if files:
            ecosystems.append(parser.ecosystem)
    return ecosystems


def parse_dependencies(project_dir: Path, ecosystems: list[Ecosystem] | None = None) -> list[Dependency]:
    """Parse all dependency files in the project directory."""
    deps = []
    for parser in ALL_PARSERS:
        if ecosystems and parser.ecosystem not in ecosystems:
            continue
        files = parser.find_files(project_dir)
        for f in files:
            deps.extend(parser.parse(f))

    # Deduplicate by (name, ecosystem, version)
    seen: set[tuple[str, str, str]] = set()
    unique = []
    for dep in deps:
        key = (dep.name, dep.ecosystem.value, dep.version)
        if key not in seen:
            seen.add(key)
            unique.append(dep)

    return unique


def analyze(
    project_dir: Path,
    project_name: str | None = None,
    offline: bool = False,
    ecosystems: list[Ecosystem] | None = None,
) -> AuditReport:
    """Run a full license audit on a project directory."""
    if project_name is None:
        project_name = project_dir.name

    # Parse dependencies
    deps = parse_dependencies(project_dir, ecosystems)

    # Resolve licenses
    resolve_licenses(deps, offline=offline)

    # Classify licenses
    for dep in deps:
        if dep.license_id and dep.license_id not in ("UNKNOWN", "UNLICENSED"):
            lic = classify_license(dep.license_id)
            dep.license_name = lic.name
            dep.license_category = lic.category

    # Find conflicts
    conflicts = find_conflicts(deps)

    # Generate issues
    issues = _generate_issues(deps)

    # Build summary
    summary = _build_summary(deps, issues, conflicts)

    warnings = []
    unknown_count = sum(1 for d in deps if d.license_id == "UNKNOWN")
    if unknown_count > 0:
        warnings.append(f"{unknown_count} dependencies have unknown licenses")

    return AuditReport(
        project_name=project_name,
        summary=summary,
        dependencies=deps,
        issues=issues,
        conflicts=conflicts,
        warnings=warnings,
    )


def _generate_issues(deps: list[Dependency]) -> list[LicenseIssue]:
    """Generate license issues from dependencies."""
    issues = []

    for dep in deps:
        # Unknown license
        if dep.license_id == "UNKNOWN":
            issues.append(
                LicenseIssue(
                    severity=Severity.WARNING,
                    dependency=dep,
                    message=f"License not detected for {dep.name}",
                    recommendation="Manually verify the license",
                    rule_id="UNKNOWN_LICENSE",
                )
            )
            continue

        # Unlicensed
        if dep.license_id in ("UNLICENSED", "UNLICENSE", "NOASSERTION"):
            issues.append(
                LicenseIssue(
                    severity=Severity.WARNING,
                    dependency=dep,
                    message=f"{dep.name} has no license specified",
                    recommendation="Contact the maintainer or find an alternative",
                    rule_id="NO_LICENSE",
                )
            )
            continue

        category = dep.license_category

        # Strong copyleft
        if category == LicenseCategory.STRONG_COPYLEFT:
            issues.append(
                LicenseIssue(
                    severity=Severity.ERROR,
                    dependency=dep,
                    message=f"{dep.name} uses {dep.license_id} (strong copyleft)",
                    recommendation="All derivative works must be released under the same license",
                    rule_id="STRONG_COPYLEFT",
                )
            )

        # Network copyleft
        if category == LicenseCategory.NETWORK_COPYLEFT:
            issues.append(
                LicenseIssue(
                    severity=Severity.CRITICAL,
                    dependency=dep,
                    message=f"{dep.name} uses {dep.license_id} (network copyleft)",
                    recommendation="This license may require releasing source code when providing network services",
                    rule_id="NETWORK_COPYLEFT",
                )
            )

        # OSI not approved
        lic = classify_license(dep.license_id)
        if not lic.is_osi_approved and category not in (LicenseCategory.UNKNOWN, LicenseCategory.UNLICENSED):
            issues.append(
                LicenseIssue(
                    severity=Severity.INFO,
                    dependency=dep,
                    message=f"{dep.license_id} is not OSI-approved",
                    recommendation="Verify the license terms carefully",
                    rule_id="NOT_OSI_APPROVED",
                )
            )

    return issues


def _build_summary(
    deps: list[Dependency],
    issues: list[LicenseIssue],
    conflicts: list,
) -> AuditSummary:
    """Build an audit summary from dependencies and issues."""
    summary = AuditSummary()
    summary.total_dependencies = len(deps)
    summary.direct_dependencies = sum(1 for d in deps if d.is_direct)
    summary.transitive_dependencies = sum(1 for d in deps if not d.is_direct)
    summary.issues_count = len(issues)
    summary.conflicts_count = len(conflicts)

    # Count by license
    for dep in deps:
        if dep.license_id:
            lic_key = dep.license_id
            summary.licenses_found[lic_key] = summary.licenses_found.get(lic_key, 0) + 1

        # Count by category
        cat_key = dep.license_category.value
        summary.categories[cat_key] = summary.categories.get(cat_key, 0) + 1

        # Count by ecosystem
        eco_key = dep.ecosystem.value
        summary.ecosystems[eco_key] = summary.ecosystems.get(eco_key, 0) + 1

    return summary
