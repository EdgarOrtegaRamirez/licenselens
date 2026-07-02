"""Tests for Python parser."""
import textwrap
from pathlib import Path

from licenselens.models import Ecosystem
from licenselens.parser.python import PythonParser


def test_pyproject_with_tomllib(tmp_path):
    """Test parsing pyproject.toml with tomllib."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(textwrap.dedent("""\
        [project]
        name = "test-project"
        version = "0.1.0"
        dependencies = [
            "requests>=2.0",
            "click>=8.0",
            "rich>=13.0",
        ]

        [project.optional-dependencies]
        dev = [
            "pytest>=7.0",
            "ruff>=0.15.0",
        ]
    """))

    parser = PythonParser()
    deps = parser.parse(pyproject)

    assert len(deps) == 5
    assert deps[0].name == "requests"
    assert deps[0].version == ">=2.0"
    assert deps[0].ecosystem == Ecosystem.PYTHON
    assert deps[0].is_direct is True
    assert deps[0].source_file == "pyproject.toml"

    # Check optional deps
    dev_deps = [d for d in deps if "dev" in d.source_file]
    assert len(dev_deps) == 2
    assert dev_deps[0].name == "pytest"


def test_pyproject_complex_versions(tmp_path):
    """Test parsing complex version specifiers."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(textwrap.dedent("""\
        [project]
        dependencies = [
            "numpy>=1.20; python_version>='3.8'",
            "pandas[all]>=1.0",
            "scikit-learn~=1.0",
        ]
    """))

    parser = PythonParser()
    deps = parser.parse(pyproject)

    assert len(deps) == 3
    assert deps[0].name == "numpy"
    assert deps[1].name == "pandas"
    assert deps[2].name == "scikit-learn"


def test_requirements_txt(tmp_path):
    """Test parsing requirements.txt."""
    req = tmp_path / "requirements.txt"
    req.write_text(textwrap.dedent("""\
        # This is a comment
        requests>=2.0
        click>=8.0

        # Blank line above
        rich>=13.0
    """))

    parser = PythonParser()
    deps = parser.parse(req)

    assert len(deps) == 3
    assert deps[0].name == "requests"
    assert deps[1].name == "click"
    assert deps[2].name == "rich"


def test_requirements_txt_with_extras(tmp_path):
    """Test parsing requirements.txt with extras."""
    req = tmp_path / "requirements.txt"
    req.write_text("requests[security]>=2.0\n")

    parser = PythonParser()
    deps = parser.parse(req)

    assert len(deps) == 1
    assert deps[0].name == "requests"


def test_setup_cfg(tmp_path):
    """Test parsing setup.cfg."""
    cfg = tmp_path / "setup.cfg"
    cfg.write_text(textwrap.dedent("""\
        [metadata]
        name = test-project

        [options]
        install_requires =
            requests>=2.0
            click>=8.0
    """))

    parser = PythonParser()
    deps = parser.parse(cfg)

    assert len(deps) == 2
    assert deps[0].name == "requests"
    assert deps[1].name == "click"


def test_can_parse(tmp_path):
    """Test can_parse method."""
    parser = PythonParser()
    assert parser.can_parse(Path("pyproject.toml"))
    assert parser.can_parse(Path("requirements.txt"))
    assert parser.can_parse(Path("setup.cfg"))
    assert not parser.can_parse(Path("package.json"))
    assert not parser.can_parse(Path("go.mod"))


def test_find_files(tmp_path):
    """Test finding dependency files."""
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "requirements.txt").touch()
    (tmp_path / "package.json").touch()

    parser = PythonParser()
    files = parser.find_files(tmp_path)

    assert len(files) == 2
    names = {f.name for f in files}
    assert "pyproject.toml" in names
    assert "requirements.txt" in names


def test_empty_pyproject(tmp_path):
    """Test parsing empty pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'test'\n")

    parser = PythonParser()
    deps = parser.parse(pyproject)

    assert len(deps) == 0


def test_requirements_comments_and_options(tmp_path):
    """Test that comments and options are skipped."""
    req = tmp_path / "requirements.txt"
    req.write_text(textwrap.dedent("""\
        -r base.txt
        --index-url https://pypi.org/simple
        # Comment
        requests>=2.0
    """))

    parser = PythonParser()
    deps = parser.parse(req)

    assert len(deps) == 1
    assert deps[0].name == "requests"


def test_dep_string_parsing():
    """Test individual dependency string parsing."""
    parser = PythonParser()

    dep = parser._parse_dep_string("requests>=2.0")
    assert dep is not None
    assert dep.name == "requests"
    assert dep.version == ">=2.0"

    dep = parser._parse_dep_string("numpy")
    assert dep is not None
    assert dep.name == "numpy"
    assert dep.version == "*"

    dep = parser._parse_dep_string("")
    assert dep is None
