"""Node.js dependency file parser (package.json)."""

from __future__ import annotations

import json
from pathlib import Path

from licenselens.models import Dependency, Ecosystem
from licenselens.parser.base import BaseParser


class NodeParser(BaseParser):
    """Parser for Node.js dependency files."""

    @property
    def ecosystem(self) -> Ecosystem:
        return Ecosystem.NODE

    @property
    def file_patterns(self) -> list[str]:
        return ["package.json"]

    def can_parse(self, file_path: Path) -> bool:
        return file_path.name == "package.json"

    def parse(self, file_path: Path) -> list[Dependency]:
        deps = []
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return deps

        dep_sections = [
            ("dependencies", True),
            ("devDependencies", True),
            ("peerDependencies", False),
            ("optionalDependencies", False),
        ]

        for section, is_direct in dep_sections:
            dep_dict = data.get(section, {})
            if not isinstance(dep_dict, dict):
                continue
            for name, version in dep_dict.items():
                if not isinstance(version, str):
                    continue
                deps.append(
                    Dependency(
                        name=name.lower(),
                        version=version,
                        ecosystem=Ecosystem.NODE,
                        is_direct=is_direct,
                        source_file=f"package.json:{section}",
                    )
                )

        return deps
