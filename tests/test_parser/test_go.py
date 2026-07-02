"""Tests for Go parser."""
import textwrap
from pathlib import Path

from licenselens.models import Ecosystem
from licenselens.parser.go import GoParser


def test_go_mod_basic(tmp_path):
    """Test parsing basic go.mod."""
    gomod = tmp_path / "go.mod"
    gomod.write_text(textwrap.dedent("""\
        module github.com/example/project

        go 1.21

        require (
            github.com/gin-gonic/gin v1.9.1
            github.com/go-sql-driver/mysql v1.7.1
        )
    """))

    parser = GoParser()
    deps = parser.parse(gomod)

    assert len(deps) == 2
    gin = next(d for d in deps if d.name == "gin")
    assert gin.version == "v1.9.1"
    assert gin.ecosystem == Ecosystem.GO
    assert gin.is_direct is True
    assert "gin-gonic/gin" in gin.homepage


def test_go_mod_with_indirect(tmp_path):
    """Test parsing go.mod with indirect dependencies."""
    gomod = tmp_path / "go.mod"
    gomod.write_text(textwrap.dedent("""\
        module example.com/app

        go 1.21

        require (
            github.com/foo/bar v1.0.0
            github.com/baz/qux v2.0.0 // indirect
        )
    """))

    parser = GoParser()
    deps = parser.parse(gomod)

    assert len(deps) == 2
    bar = next(d for d in deps if d.name == "bar")
    assert bar.is_direct is True
    qux = next(d for d in deps if d.name == "qux")
    assert qux.is_direct is False


def test_go_mod_single_require(tmp_path):
    """Test parsing go.mod with single-line require."""
    gomod = tmp_path / "go.mod"
    gomod.write_text(textwrap.dedent("""\
        module example.com/app

        go 1.21

        require github.com/foo/bar v1.0.0
    """))

    parser = GoParser()
    deps = parser.parse(gomod)

    assert len(deps) == 1
    assert deps[0].name == "bar"
    assert deps[0].version == "v1.0.0"


def test_go_mod_with_comments(tmp_path):
    """Test parsing go.mod with comments."""
    gomod = tmp_path / "go.mod"
    gomod.write_text(textwrap.dedent("""\
        module example.com/app

        go 1.21

        require (
            // This is a comment
            github.com/foo/bar v1.0.0
        )
    """))

    parser = GoParser()
    deps = parser.parse(gomod)

    assert len(deps) == 1
    assert deps[0].name == "bar"


def test_can_parse():
    """Test can_parse method."""
    parser = GoParser()
    assert parser.can_parse(Path("go.mod"))
    assert not parser.can_parse(Path("package.json"))


def test_find_files(tmp_path):
    """Test finding dependency files."""
    (tmp_path / "go.mod").touch()

    parser = GoParser()
    files = parser.find_files(tmp_path)

    assert len(files) == 1
    assert files[0].name == "go.mod"


def test_empty_go_mod(tmp_path):
    """Test parsing empty go.mod."""
    gomod = tmp_path / "go.mod"
    gomod.write_text("module example.com/app\n\n")

    parser = GoParser()
    deps = parser.parse(gomod)

    assert len(deps) == 0
