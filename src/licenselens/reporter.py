"""Report generation for LicenseLens audit results."""

from __future__ import annotations

import json

from licenselens.models import (
    AuditReport,
    Severity,
)

# Category emoji mapping
CATEGORY_ICONS = {
    "permissive": "✅",
    "weak_copyleft": "⚠️",
    "strong_copyleft": "🔴",
    "network_copyleft": "🚨",
    "proprietary": "🔒",
    "unknown": "❓",
    "unlicensed": "❌",
}

SEVERITY_ICONS = {
    Severity.INFO: "ℹ️",
    Severity.WARNING: "⚠️",
    Severity.ERROR: "❌",
    Severity.CRITICAL: "🚨",
}


def format_text(report: AuditReport) -> str:
    """Format audit report as plain text."""
    lines = []
    s = report.summary

    lines.append(f"License Audit Report: {report.project_name}")
    lines.append("=" * (len(report.project_name) + 20))
    lines.append("")

    # Summary
    lines.append(f"Total dependencies:     {s.total_dependencies}")
    lines.append(f"  Direct:               {s.direct_dependencies}")
    lines.append(f"  Transitive:           {s.transitive_dependencies}")
    lines.append("")

    # Ecosystems
    if s.ecosystems:
        lines.append("Ecosystems:")
        for eco, count in sorted(s.ecosystems.items()):
            lines.append(f"  {eco:<10} {count}")
        lines.append("")

    # License breakdown
    if s.licenses_found:
        lines.append("Licenses found:")
        for lic, count in sorted(s.licenses_found.items(), key=lambda x: -x[1]):
            lines.append(f"  {lic:<30} {count}")
        lines.append("")

    # Category breakdown
    if s.categories:
        lines.append("License categories:")
        for cat, count in sorted(s.categories.items()):
            icon = CATEGORY_ICONS.get(cat, "  ")
            lines.append(f"  {icon} {cat:<25} {count}")
        lines.append("")

    # Issues
    if report.issues:
        lines.append(f"Issues ({len(report.issues)}):")
        for issue in report.issues:
            icon = SEVERITY_ICONS.get(issue.severity, "  ")
            lines.append(f"  {icon} [{issue.severity.value.upper()}] {issue.message}")
            if issue.recommendation:
                lines.append(f"     → {issue.recommendation}")
        lines.append("")

    # Conflicts
    if report.conflicts:
        lines.append(f"Conflicts ({len(report.conflicts)}):")
        for conflict in report.conflicts:
            icon = SEVERITY_ICONS.get(conflict.severity, "  ")
            lines.append(f"  {icon} {conflict.license_a} ↔ {conflict.license_b}")
            lines.append(f"     {conflict.message}")
        lines.append("")

    # Warnings
    if report.warnings:
        lines.append("Warnings:")
        for w in report.warnings:
            lines.append(f"  ⚠️  {w}")
        lines.append("")

    # Dependency list
    if report.dependencies:
        lines.append("Dependencies:")
        for dep in sorted(report.dependencies, key=lambda d: d.name):
            icon = CATEGORY_ICONS.get(dep.license_category.value, "  ")
            direct = "direct" if dep.is_direct else "transitive"
            lines.append(f"  {icon} {dep.name:<30} {dep.version:<15} {dep.license_id:<15} {dep.ecosystem.value:<8} {direct}")

    return "\n".join(lines)


def format_markdown(report: AuditReport) -> str:
    """Format audit report as Markdown."""
    lines = []
    s = report.summary

    lines.append(f"# License Audit: {report.project_name}")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total dependencies | {s.total_dependencies} |")
    lines.append(f"| Direct | {s.direct_dependencies} |")
    lines.append(f"| Transitive | {s.transitive_dependencies} |")
    lines.append(f"| Issues | {s.issues_count} |")
    lines.append(f"| Conflicts | {s.conflicts_count} |")
    lines.append("")

    # License breakdown
    if s.licenses_found:
        lines.append("## Licenses")
        lines.append("")
        lines.append("| License | Count |")
        lines.append("|---------|-------|")
        for lic, count in sorted(s.licenses_found.items(), key=lambda x: -x[1]):
            lines.append(f"| {lic} | {count} |")
        lines.append("")

    # Categories
    if s.categories:
        lines.append("## Categories")
        lines.append("")
        lines.append("| Category | Count |")
        lines.append("|----------|-------|")
        for cat, count in sorted(s.categories.items()):
            icon = CATEGORY_ICONS.get(cat, "")
            lines.append(f"| {icon} {cat} | {count} |")
        lines.append("")

    # Issues
    if report.issues:
        lines.append(f"## Issues ({len(report.issues)})")
        lines.append("")
        for issue in report.issues:
            icon = SEVERITY_ICONS.get(issue.severity, "")
            lines.append(f"- {icon} **{issue.severity.value.upper()}**: {issue.message}")
            if issue.recommendation:
                lines.append(f"  - Recommendation: {issue.recommendation}")
        lines.append("")

    # Conflicts
    if report.conflicts:
        lines.append(f"## Conflicts ({len(report.conflicts)})")
        lines.append("")
        for conflict in report.conflicts:
            icon = SEVERITY_ICONS.get(conflict.severity, "")
            lines.append(f"- {icon} **{conflict.license_a}** ↔ **{conflict.license_b}**: {conflict.message}")
        lines.append("")

    # Dependency list
    if report.dependencies:
        lines.append("## Dependencies")
        lines.append("")
        lines.append("| Name | Version | License | Ecosystem | Type |")
        lines.append("|------|---------|---------|-----------|------|")
        for dep in sorted(report.dependencies, key=lambda d: d.name):
            icon = CATEGORY_ICONS.get(dep.license_category.value, "")
            direct = "direct" if dep.is_direct else "transitive"
            lines.append(f"| {dep.name} | {dep.version} | {icon} {dep.license_id} | {dep.ecosystem.value} | {direct} |")

    return "\n".join(lines)


def format_json(report: AuditReport) -> str:
    """Format audit report as JSON."""
    data = {
        "project_name": report.project_name,
        "summary": {
            "total_dependencies": report.summary.total_dependencies,
            "direct_dependencies": report.summary.direct_dependencies,
            "transitive_dependencies": report.summary.transitive_dependencies,
            "licenses_found": report.summary.licenses_found,
            "categories": report.summary.categories,
            "ecosystems": report.summary.ecosystems,
            "issues_count": report.summary.issues_count,
            "conflicts_count": report.summary.conflicts_count,
        },
        "dependencies": [
            {
                "name": d.name,
                "version": d.version,
                "license_id": d.license_id,
                "license_name": d.license_name,
                "license_category": d.license_category.value,
                "ecosystem": d.ecosystem.value,
                "is_direct": d.is_direct,
                "source_file": d.source_file,
            }
            for d in report.dependencies
        ],
        "issues": [
            {
                "severity": i.severity.value,
                "dependency": i.dependency.name,
                "message": i.message,
                "recommendation": i.recommendation,
                "rule_id": i.rule_id,
            }
            for i in report.issues
        ],
        "conflicts": [
            {
                "license_a": c.license_a,
                "license_b": c.license_b,
                "message": c.message,
                "severity": c.severity.value,
            }
            for c in report.conflicts
        ],
        "warnings": report.warnings,
    }
    return json.dumps(data, indent=2)


def format_csv(report: AuditReport) -> str:
    """Format dependency list as CSV."""
    lines = ["name,version,license_id,license_category,ecosystem,type,source_file"]
    for dep in sorted(report.dependencies, key=lambda d: d.name):
        direct = "direct" if dep.is_direct else "transitive"
        lines.append(
            f'"{dep.name}","{dep.version}","{dep.license_id}","{dep.license_category.value}","{dep.ecosystem.value}","{direct}","{dep.source_file}"'
        )
    return "\n".join(lines)


FORMATTERS = {
    "text": format_text,
    "markdown": format_markdown,
    "json": format_json,
    "csv": format_csv,
}
