"""Tests for CLI."""
import textwrap

from click.testing import CliRunner

from licenselens.cli import main


def test_main_help():
    """Test main help output."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "LicenseLens" in result.output


def test_audit_python_project(tmp_path):
    """Test auditing a Python project."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(textwrap.dedent("""\
        [project]
        name = "test"
        dependencies = ["click>=8.0"]
    """))

    runner = CliRunner()
    result = runner.invoke(main, ["audit", str(tmp_path), "--offline"])

    assert result.exit_code == 1  # Exit 1 due to unknown license issues


def test_audit_json_format(tmp_path):
    """Test auditing with JSON output."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(textwrap.dedent("""\
        [project]
        name = "test"
        dependencies = ["click>=8.0"]
    """))

    runner = CliRunner()
    result = runner.invoke(main, ["audit", str(tmp_path), "--offline", "--format", "json"])

    assert result.exit_code == 1
    import json
    data = json.loads(result.output)
    assert data["summary"]["total_dependencies"] == 1


def test_audit_markdown_format(tmp_path):
    """Test auditing with Markdown output."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(textwrap.dedent("""\
        [project]
        name = "test"
        dependencies = []
    """))

    runner = CliRunner()
    result = runner.invoke(main, ["audit", str(tmp_path), "--offline", "--format", "markdown"])

    assert result.exit_code == 0
    assert "# License Audit:" in result.output


def test_audit_csv_format(tmp_path):
    """Test auditing with CSV output."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(textwrap.dedent("""\
        [project]
        name = "test"
        dependencies = []
    """))

    runner = CliRunner()
    result = runner.invoke(main, ["audit", str(tmp_path), "--offline", "--format", "csv"])

    assert result.exit_code == 0
    assert "name,version,license_id" in result.output


def test_audit_output_file(tmp_path):
    """Test writing audit output to file."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(textwrap.dedent("""\
        [project]
        name = "test"
        dependencies = []
    """))

    output_file = tmp_path / "report.txt"
    runner = CliRunner()
    result = runner.invoke(main, [
        "audit", str(tmp_path), "--offline",
        "--output", str(output_file),
    ])

    assert result.exit_code == 0
    assert output_file.exists()


def test_detect_command(tmp_path):
    """Test detect command."""
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "package.json").touch()

    runner = CliRunner()
    result = runner.invoke(main, ["detect", str(tmp_path)])

    assert result.exit_code == 0
    assert "python" in result.output
    assert "node" in result.output


def test_detect_empty(tmp_path):
    """Test detect command on empty directory."""
    runner = CliRunner()
    result = runner.invoke(main, ["detect", str(tmp_path)])

    assert result.exit_code == 0
    assert "No dependency files found" in result.output


def test_info_command():
    """Test info command."""
    runner = CliRunner()
    result = runner.invoke(main, ["info", "MIT"])

    assert result.exit_code == 0
    assert "MIT" in result.output


def test_info_unknown_license():
    """Test info command for unknown license."""
    runner = CliRunner()
    result = runner.invoke(main, ["info", "SomeWeirdLicense"])

    assert result.exit_code == 0
    assert "SomeWeirdLicense" in result.output


def test_licenses_command():
    """Test licenses command."""
    runner = CliRunner()
    result = runner.invoke(main, ["licenses"])

    assert result.exit_code == 0
    assert "MIT" in result.output
    assert "GPL" in result.output


def test_audit_empty_project(tmp_path):
    """Test auditing an empty project."""
    runner = CliRunner()
    result = runner.invoke(main, ["audit", str(tmp_path), "--offline"])

    # Empty project = no deps found = exit 1 (no dependency files)
    assert result.exit_code == 1
    assert "No dependency files found" in result.output
