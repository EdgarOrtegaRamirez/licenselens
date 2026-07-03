"""CLI interface for LicenseLens."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from licenselens.analyzer import analyze, detect_ecosystem
from licenselens.models import AuditReport, Ecosystem, Severity
from licenselens.reporter import FORMATTERS

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="licenselens")
def main() -> None:
    """LicenseLens: Multi-ecosystem dependency license auditor."""
    pass


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--format", "-f", "fmt", type=click.Choice(["text", "markdown", "json", "csv"]), default="text", help="Output format")
@click.option("--output", "-o", type=click.Path(), help="Write output to file")
@click.option("--offline", is_flag=True, help="Skip API calls for license resolution")
@click.option(
    "--ecosystem", "-e", multiple=True, type=click.Choice(["python", "node", "go", "rust"]), help="Limit to specific ecosystems (can be repeated)"
)
def audit(path: str, fmt: str, output: str | None, offline: bool, ecosystem: tuple[str, ...]) -> None:
    """Audit dependencies in a project directory."""
    project_dir = Path(path).resolve()

    # Detect ecosystems
    ecosystems = [Ecosystem(e) for e in ecosystem] if ecosystem else None
    if ecosystems is None:
        detected = detect_ecosystem(project_dir)
        if not detected:
            if fmt == "text":
                console.print("[yellow]No dependency files found in the project directory.[/yellow]")
            sys.exit(1)
        ecosystems = detected
        if fmt == "text":
            console.print(f"[dim]Detected ecosystems: {', '.join(e.value for e in ecosystems)}[/dim]")

    # Run analysis
    if fmt == "text":
        console.print(f"[bold]Analyzing {project_dir}...[/bold]")
    report = analyze(project_dir, offline=offline, ecosystems=ecosystems)

    # Format output
    formatter = FORMATTERS[fmt]
    result = formatter(report)

    if output:
        Path(output).write_text(result, encoding="utf-8")
        console.print(f"[green]Report written to {output}[/green]")
    else:
        if fmt == "text":
            # Use rich for terminal output
            _print_rich_report(report)
        else:
            console.print(result)

    # Exit code based on issues
    if report.summary.issues_count > 0:
        sys.exit(1)


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def detect(path: str) -> None:
    """Detect ecosystems in a project directory."""
    project_dir = Path(path).resolve()
    ecosystems = detect_ecosystem(project_dir)

    if ecosystems:
        console.print(f"[bold]Detected ecosystems in {project_dir}:[/bold]")
        for eco in ecosystems:
            console.print(f"  • {eco.value}")
    else:
        console.print("[yellow]No dependency files found.[/yellow]")


@main.command()
@click.argument("license_id")
def info(license_id: str) -> None:
    """Show information about a license."""
    from licenselens.classifier import classify_license

    lic = classify_license(license_id)

    table = Table(title=f"License: {lic.spdx_id}")
    table.add_column("Property", style="bold")
    table.add_column("Value")

    table.add_row("SPDX ID", lic.spdx_id)
    table.add_row("Name", lic.name)
    table.add_row("Category", lic.category.value)
    table.add_row("OSI Approved", "Yes" if lic.is_osi_approved else "No")
    table.add_row("FSF Free", "Yes" if lic.is_fsf_free else "No")

    console.print(table)


@main.command()
def licenses() -> None:
    """List all known licenses."""
    from licenselens.classifier import KNOWN_LICENSES

    table = Table(title="Known Licenses")
    table.add_column("SPDX ID", style="bold")
    table.add_column("Name")
    table.add_column("Category")
    table.add_column("OSI")

    for lic in sorted(KNOWN_LICENSES.values(), key=lambda x: x.category.value):
        osi = "✓" if lic.is_osi_approved else ""
        cat_icon = {
            "permissive": "✅",
            "weak_copyleft": "⚠️",
            "strong_copyleft": "🔴",
            "network_copyleft": "🚨",
            "proprietary": "🔒",
        }.get(lic.category.value, "❓")
        table.add_row(lic.spdx_id, lic.name, f"{cat_icon} {lic.category.value}", osi)

    console.print(table)


def _print_rich_report(report: AuditReport) -> None:
    """Print a rich-formatted report."""

    s = report.summary

    # Summary panel
    summary_text = Text()
    summary_text.append(f"Total: {s.total_dependencies} ", style="bold")
    summary_text.append(f"(direct: {s.direct_dependencies}, transitive: {s.transitive_dependencies})\n")
    if s.issues_count > 0:
        summary_text.append(f"Issues: {s.issues_count}\n", style="red")
    if s.conflicts_count > 0:
        summary_text.append(f"Conflicts: {s.conflicts_count}\n", style="red bold")
    if not s.issues_count and not s.conflicts_count:
        summary_text.append("✅ No issues found\n", style="green")

    console.print(Panel(summary_text, title=f"License Audit: {report.project_name}"))

    # License breakdown
    if s.licenses_found:
        table = Table(title="Licenses")
        table.add_column("License", style="bold")
        table.add_column("Count", justify="right")
        table.add_column("Category")

        category_icons = {
            "permissive": "✅",
            "weak_copyleft": "⚠️",
            "strong_copyleft": "🔴",
            "network_copyleft": "🚨",
            "proprietary": "🔒",
            "unknown": "❓",
        }

        # Group by category
        from licenselens.classifier import classify_license

        for lic_id, count in sorted(s.licenses_found.items(), key=lambda x: -x[1]):
            lic = classify_license(lic_id)
            icon = category_icons.get(lic.category.value, "❓")
            table.add_row(lic_id, str(count), f"{icon} {lic.category.value}")

        console.print(table)

    # Issues
    if report.issues:
        table = Table(title=f"Issues ({len(report.issues)})")
        table.add_column("Severity")
        table.add_column("Dependency")
        table.add_column("Message")

        severity_styles = {
            Severity.INFO: "blue",
            Severity.WARNING: "yellow",
            Severity.ERROR: "red",
            Severity.CRITICAL: "red bold",
        }

        for issue in report.issues:
            style = severity_styles.get(issue.severity, "")
            table.add_row(
                Text(issue.severity.value.upper(), style=style),
                issue.dependency.name,
                issue.message,
            )

        console.print(table)

    # Conflicts
    if report.conflicts:
        table = Table(title=f"Conflicts ({len(report.conflicts)})")
        table.add_column("License A")
        table.add_column("License B")
        table.add_column("Message")

        for conflict in report.conflicts:
            table.add_row(conflict.license_a, conflict.license_b, conflict.message)

        console.print(table)


if __name__ == "__main__":
    main()
