"""Rust dependency file parser (Cargo.toml)."""

from __future__ import annotations

from pathlib import Path

from licenselens.models import Dependency, Ecosystem
from licenselens.parser.base import BaseParser


class RustParser(BaseParser):
    """Parser for Rust dependency files (Cargo.toml)."""

    @property
    def ecosystem(self) -> Ecosystem:
        return Ecosystem.RUST

    @property
    def file_patterns(self) -> list[str]:
        return ["Cargo.toml"]

    def can_parse(self, file_path: Path) -> bool:
        return file_path.name == "Cargo.toml"

    def parse(self, file_path: Path) -> list[Dependency]:
        deps = []
        try:
            data = self._parse_toml_simple(file_path.read_text(encoding="utf-8"))
        except OSError:
            return deps

        sections = [
            ("dependencies", True),
            ("dev-dependencies", True),
            ("build-dependencies", True),
        ]

        for section, is_direct in sections:
            section_data = data.get(section, {})
            for name, value in section_data.items():
                if isinstance(value, str):
                    version = value
                elif isinstance(value, dict):
                    version = value.get("version", "*")
                else:
                    continue

                deps.append(
                    Dependency(
                        name=name,
                        version=version,
                        ecosystem=Ecosystem.RUST,
                        is_direct=is_direct,
                        source_file="Cargo.toml",
                    )
                )

        return deps

    def _parse_toml_simple(self, text: str) -> dict:
        """Simple TOML parser for Cargo.toml - handles the common patterns."""
        result: dict = {}
        current_section: dict = result

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Section header like [dependencies]
            if stripped.startswith("[") and stripped.endswith("]"):
                section_name = stripped[1:-1].strip()
                if section_name not in result:
                    result[section_name] = {}
                current_section = result[section_name]
                continue

            # Key = value
            if "=" in stripped:
                key, _, val = stripped.partition("=")
                key = key.strip().strip('"')
                val = val.strip().strip('"').strip(",")

                if val.startswith("{") and val.endswith("}"):
                    # Inline table - parse simple key = "value" pairs
                    inner = {}
                    for pair in val[1:-1].split(","):
                        if "=" in pair:
                            k, _, v = pair.partition("=")
                            inner[k.strip()] = v.strip().strip('"')
                    current_section[key] = inner
                elif val.startswith('"') and val.endswith('"'):
                    current_section[key] = val.strip('"')
                else:
                    current_section[key] = val

        return result
