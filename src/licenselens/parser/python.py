"""Python dependency file parser (pyproject.toml, setup.cfg, requirements.txt)."""

from __future__ import annotations

import re
from pathlib import Path

from licenselens.models import Dependency, Ecosystem
from licenselens.parser.base import BaseParser


class PythonParser(BaseParser):
    """Parser for Python dependency files."""

    @property
    def ecosystem(self) -> Ecosystem:
        return Ecosystem.PYTHON

    @property
    def file_patterns(self) -> list[str]:
        return ["pyproject.toml", "setup.cfg", "setup.py", "requirements.txt", "requirements-dev.txt"]

    def can_parse(self, file_path: Path) -> bool:
        return file_path.name in self.file_patterns

    def parse(self, file_path: Path) -> list[Dependency]:
        if file_path.name == "pyproject.toml":
            return self._parse_pyproject(file_path)
        elif file_path.name == "setup.cfg":
            return self._parse_setup_cfg(file_path)
        elif file_path.name == "requirements.txt" or file_path.name == "requirements-dev.txt":
            return self._parse_requirements(file_path)
        return []

    def _parse_pyproject(self, file_path: Path) -> list[Dependency]:
        """Parse pyproject.toml for dependencies."""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore
            except ImportError:
                return self._parse_pyproject_simple(file_path)

        deps = []
        try:
            data = tomllib.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return deps

        project = data.get("project", {})
        for dep_str in project.get("dependencies", []):
            dep = self._parse_dep_string(dep_str)
            if dep:
                dep.is_direct = True
                dep.source_file = file_path.name
                deps.append(dep)

        optional = project.get("optional-dependencies", {})
        for group_name, dep_list in optional.items():
            for dep_str in dep_list:
                dep = self._parse_dep_string(dep_str)
                if dep:
                    dep.is_direct = True
                    dep.source_file = f"{file_path.name}[{group_name}]"
                    deps.append(dep)

        return deps

    def _parse_pyproject_simple(self, file_path: Path) -> list[Dependency]:
        """Fallback: parse pyproject.toml with regex for dependency extraction."""
        deps = []
        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception:
            return deps

        in_deps = False
        in_optional = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("dependencies"):
                in_deps = True
                in_optional = False
                continue
            if stripped.startswith("[project.optional-dependencies"):
                in_optional = True
                in_deps = False
                continue
            if stripped.startswith("[") and not stripped.startswith("[project.optional"):
                in_deps = False
                in_optional = False
                continue

            if in_deps or in_optional:
                dep_str = stripped.strip('",').strip("'").strip()
                if dep_str and not dep_str.startswith("#"):
                    dep = self._parse_dep_string(dep_str)
                    if dep:
                        dep.is_direct = True
                        dep.source_file = file_path.name
                        deps.append(dep)

        return deps

    def _parse_setup_cfg(self, file_path: Path) -> list[Dependency]:
        """Parse setup.cfg for install_requires."""
        deps = []
        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception:
            return deps

        in_install = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("install_requires"):
                in_install = True
                continue
            if in_install and stripped and not stripped.startswith("["):
                dep = self._parse_dep_string(stripped.strip("=").strip())
                if dep:
                    dep.is_direct = True
                    dep.source_file = "setup.cfg"
                    deps.append(dep)
            elif stripped.startswith("[") and in_install:
                break

        return deps

    def _parse_requirements(self, file_path: Path) -> list[Dependency]:
        """Parse requirements.txt."""
        deps = []
        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception:
            return deps

        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            dep = self._parse_dep_string(line)
            if dep:
                dep.is_direct = True
                dep.source_file = file_path.name
                deps.append(dep)

        return deps

    def _parse_dep_string(self, dep_str: str) -> Dependency | None:
        """Parse a PEP 508 dependency string like 'requests>=2.0' or 'numpy; python_version>="3.8"'."""
        if not dep_str:
            return None

        # Remove environment markers
        dep_str = dep_str.split(";")[0].strip()
        # Remove extras
        dep_str = re.sub(r"\[.*?\]", "", dep_str)
        # Remove version specifiers
        match = re.match(r"([a-zA-Z0-9_.-]+)\s*(.*)", dep_str)
        if not match:
            return None

        name = match.group(1).strip()
        version = match.group(2).strip() if match.group(2) else ""

        # Normalize name
        name = re.sub(r"[-_.]+", "-", name).lower()

        return Dependency(
            name=name,
            version=version or "*",
            ecosystem=Ecosystem.PYTHON,
        )
