"""Tests for analyzer."""

import json
import textwrap

from licenselens.analyzer import analyze, detect_ecosystem, parse_dependencies
from licenselens.models import Ecosystem, Severity


def test_analyze_python_project(tmp_path):
    """Test analyzing a Python project."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        textwrap.dedent("""\
        [project]
        name = "test-project"
        dependencies = ["requests>=2.0", "click>=8.0"]
    """)
    )

    report = analyze(tmp_path, project_name="test", offline=True)

    assert report.project_name == "test"
    assert report.summary.total_dependencies == 2
    assert Ecosystem.PYTHON.value in report.summary.ecosystems


def test_analyze_node_project(tmp_path):
    """Test analyzing a Node.js project."""
    pkg = tmp_path / "package.json"
    pkg.write_text(
        json.dumps(
            {
                "dependencies": {"express": "^4.18.0"},
                "devDependencies": {"jest": "^29.0.0"},
            }
        )
    )

    report = analyze(tmp_path, offline=True)

    assert report.summary.total_dependencies == 2
    assert Ecosystem.NODE.value in report.summary.ecosystems


def test_analyze_go_project(tmp_path):
    """Test analyzing a Go project."""
    gomod = tmp_path / "go.mod"
    gomod.write_text(
        textwrap.dedent("""\
        module example.com/app

        go 1.21

        require (
            github.com/gin-gonic/gin v1.9.1
        )
    """)
    )

    report = analyze(tmp_path, offline=True)

    assert report.summary.total_dependencies == 1
    assert Ecosystem.GO.value in report.summary.ecosystems


def test_analyze_rust_project(tmp_path):
    """Test analyzing a Rust project."""
    cargo = tmp_path / "Cargo.toml"
    cargo.write_text(
        textwrap.dedent("""\
        [package]
        name = "test"
        version = "0.1.0"

        [dependencies]
        serde = "1.0"
    """)
    )

    report = analyze(tmp_path, offline=True)

    assert report.summary.total_dependencies == 1
    assert Ecosystem.RUST.value in report.summary.ecosystems


def test_analyze_empty_project(tmp_path):
    """Test analyzing empty project."""
    report = analyze(tmp_path, offline=True)

    assert report.summary.total_dependencies == 0
    assert len(report.issues) == 0


def test_analyze_unknown_licenses(tmp_path):
    """Test that unknown licenses generate warnings."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        textwrap.dedent("""\
        [project]
        dependencies = ["some-obscure-lib>=1.0"]
    """)
    )

    report = analyze(tmp_path, offline=True)

    # Should have unknown license issues
    warning_issues = [i for i in report.issues if i.severity == Severity.WARNING]
    assert len(warning_issues) >= 1


def test_detect_ecosystem_python(tmp_path):
    """Test ecosystem detection for Python."""
    (tmp_path / "pyproject.toml").touch()
    ecosystems = detect_ecosystem(tmp_path)
    assert Ecosystem.PYTHON in ecosystems


def test_detect_ecosystem_multiple(tmp_path):
    """Test detecting multiple ecosystems."""
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "package.json").touch()
    (tmp_path / "go.mod").touch()

    ecosystems = detect_ecosystem(tmp_path)
    assert Ecosystem.PYTHON in ecosystems
    assert Ecosystem.NODE in ecosystems
    assert Ecosystem.GO in ecosystems


def test_detect_ecosystem_empty(tmp_path):
    """Test detecting no ecosystems."""
    ecosystems = detect_ecosystem(tmp_path)
    assert len(ecosystems) == 0


def test_parse_dependencies_dedup(tmp_path):
    """Test that dependencies are deduplicated."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        textwrap.dedent("""\
        [project]
        dependencies = ["requests>=2.0"]
        [project.optional-dependencies]
        dev = ["requests>=2.0"]
    """)
    )

    deps = parse_dependencies(tmp_path)
    # Should be deduplicated since same name+version
    assert len(deps) == 1


def test_analyze_summary_categories(tmp_path):
    """Test that categories are properly counted."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        textwrap.dedent("""\
        [project]
        dependencies = ["requests>=2.0", "click>=8.0"]
    """)
    )

    report = analyze(tmp_path, offline=True)
    assert "unknown" in report.summary.categories
    assert report.summary.categories["unknown"] == 2


def test_analyze_report_warnings(tmp_path):
    """Test that warnings are generated for unknown licenses."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        textwrap.dedent("""\
        [project]
        dependencies = ["some-lib>=1.0"]
    """)
    )

    report = analyze(tmp_path, offline=True)
    assert len(report.warnings) >= 1
    assert "unknown" in report.warnings[0].lower()
