"""Go dependency file parser (go.mod)."""

from __future__ import annotations

import re
from pathlib import Path

from licenselens.models import Dependency, Ecosystem
from licenselens.parser.base import BaseParser


class GoParser(BaseParser):
    """Parser for Go dependency files (go.mod)."""

    @property
    def ecosystem(self) -> Ecosystem:
        return Ecosystem.GO

    @property
    def file_patterns(self) -> list[str]:
        return ["go.mod"]

    def can_parse(self, file_path: Path) -> bool:
        return file_path.name == "go.mod"

    def parse(self, file_path: Path) -> list[Dependency]:
        deps = []
        try:
            text = file_path.read_text(encoding="utf-8")
        except OSError:
            return deps

        in_require = False
        for line in text.splitlines():
            stripped = line.strip()

            if stripped.startswith("require ("):
                in_require = True
                continue
            if in_require and stripped == ")":
                in_require = False
                continue

            if in_require:
                dep = self._parse_require_line(stripped)
                if dep:
                    deps.append(dep)
            elif stripped.startswith("require "):
                dep = self._parse_require_line(stripped[len("require ") :])
                if dep:
                    deps.append(dep)

        return deps

    def _parse_require_line(self, line: str) -> Dependency | None:
        """Parse a require line like 'github.com/foo/bar v1.2.3'."""
        line = line.strip()
        if not line or line.startswith("//"):
            return None

        match = re.match(r"(\S+)\s+(v[\d.]+[^\s]*)(.*)", line)
        if not match:
            return None

        module_path = match.group(1)
        version = match.group(2)

        # Extract short name from module path
        parts = module_path.split("/")
        name = parts[-1] if parts else module_path

        # Check for indirect
        remaining = match.group(3).strip()
        is_direct = "indirect" not in remaining

        return Dependency(
            name=name,
            version=version,
            ecosystem=Ecosystem.GO,
            is_direct=is_direct,
            source_file="go.mod",
            homepage=f"https://{module_path}",
        )
