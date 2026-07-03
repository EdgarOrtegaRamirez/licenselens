"""Tests for Node.js parser."""

import json
from pathlib import Path

from licenselens.models import Ecosystem
from licenselens.parser.node import NodeParser


def test_package_json_basic(tmp_path):
    """Test parsing basic package.json."""
    pkg = tmp_path / "package.json"
    pkg.write_text(
        json.dumps(
            {
                "name": "test-pkg",
                "version": "1.0.0",
                "dependencies": {
                    "express": "^4.18.0",
                    "lodash": "^4.17.21",
                },
                "devDependencies": {
                    "jest": "^29.0.0",
                    "eslint": "^8.0.0",
                },
            }
        )
    )

    parser = NodeParser()
    deps = parser.parse(pkg)

    assert len(deps) == 4
    express = next(d for d in deps if d.name == "express")
    assert express.version == "^4.18.0"
    assert express.ecosystem == Ecosystem.NODE
    assert express.is_direct is True
    assert "dependencies" in express.source_file

    jest = next(d for d in deps if d.name == "jest")
    assert jest.is_direct is True
    assert "devDependencies" in jest.source_file


def test_package_json_all_sections(tmp_path):
    """Test parsing all dependency sections."""
    pkg = tmp_path / "package.json"
    pkg.write_text(
        json.dumps(
            {
                "dependencies": {"a": "1.0"},
                "devDependencies": {"b": "2.0"},
                "peerDependencies": {"c": "3.0"},
                "optionalDependencies": {"d": "4.0"},
            }
        )
    )

    parser = NodeParser()
    deps = parser.parse(pkg)

    assert len(deps) == 4
    # peerDependencies and optionalDependencies are not direct
    peer = next(d for d in deps if d.name == "c")
    assert peer.is_direct is False
    optional = next(d for d in deps if d.name == "d")
    assert optional.is_direct is False


def test_package_json_empty(tmp_path):
    """Test parsing empty package.json."""
    pkg = tmp_path / "package.json"
    pkg.write_text(json.dumps({"name": "test"}))

    parser = NodeParser()
    deps = parser.parse(pkg)

    assert len(deps) == 0


def test_package_json_invalid(tmp_path):
    """Test parsing invalid package.json."""
    pkg = tmp_path / "package.json"
    pkg.write_text("not json {{{")

    parser = NodeParser()
    deps = parser.parse(pkg)

    assert len(deps) == 0


def test_can_parse():
    """Test can_parse method."""
    parser = NodeParser()
    assert parser.can_parse(Path("package.json"))
    assert not parser.can_parse(Path("pyproject.toml"))


def test_find_files(tmp_path):
    """Test finding dependency files."""
    (tmp_path / "package.json").touch()
    (tmp_path / "pyproject.toml").touch()

    parser = NodeParser()
    files = parser.find_files(tmp_path)

    assert len(files) == 1
    assert files[0].name == "package.json"
