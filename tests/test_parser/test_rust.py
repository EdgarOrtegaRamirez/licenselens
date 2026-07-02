"""Tests for Rust parser."""
import textwrap
from pathlib import Path

from licenselens.models import Ecosystem
from licenselens.parser.rust import RustParser


def test_cargo_toml_basic(tmp_path):
    """Test parsing basic Cargo.toml."""
    cargo = tmp_path / "Cargo.toml"
    cargo.write_text(textwrap.dedent("""\
        [package]
        name = "test-project"
        version = "0.1.0"
        edition = "2021"

        [dependencies]
        serde = "1.0"
        tokio = { version = "1.0", features = ["full"] }
        clap = "4.0"

        [dev-dependencies]
        assert_cmd = "2.0"
    """))

    parser = RustParser()
    deps = parser.parse(cargo)

    assert len(deps) == 4

    serde = next(d for d in deps if d.name == "serde")
    assert serde.version == "1.0"
    assert serde.ecosystem == Ecosystem.RUST
    assert serde.is_direct is True

    tokio = next(d for d in deps if d.name == "tokio")
    assert isinstance(tokio.version, str)

    assert_cmd = next(d for d in deps if d.name == "assert_cmd")
    assert assert_cmd.is_direct is True
    assert assert_cmd.source_file == "Cargo.toml"


def test_cargo_toml_inline_table(tmp_path):
    """Test parsing Cargo.toml with inline tables."""
    cargo = tmp_path / "Cargo.toml"
    cargo.write_text(textwrap.dedent("""\
        [dependencies]
        serde = { version = "1.0", features = ["derive"] }
    """))

    parser = RustParser()
    deps = parser.parse(cargo)

    assert len(deps) == 1
    assert deps[0].name == "serde"
    assert deps[0].version == "1.0"


def test_cargo_toml_empty(tmp_path):
    """Test parsing empty Cargo.toml."""
    cargo = tmp_path / "Cargo.toml"
    cargo.write_text("[package]\nname = 'test'\n")

    parser = RustParser()
    deps = parser.parse(cargo)

    assert len(deps) == 0


def test_cargo_toml_string_values(tmp_path):
    """Test parsing Cargo.toml with string version values."""
    cargo = tmp_path / "Cargo.toml"
    cargo.write_text(textwrap.dedent("""\
        [dependencies]
        serde = "1.0"
    """))

    parser = RustParser()
    deps = parser.parse(cargo)

    assert len(deps) == 1
    assert deps[0].version == "1.0"


def test_can_parse():
    """Test can_parse method."""
    parser = RustParser()
    assert parser.can_parse(Path("Cargo.toml"))
    assert not parser.can_parse(Path("package.json"))


def test_find_files(tmp_path):
    """Test finding dependency files."""
    (tmp_path / "Cargo.toml").touch()

    parser = RustParser()
    files = parser.find_files(tmp_path)

    assert len(files) == 1
    assert files[0].name == "Cargo.toml"
