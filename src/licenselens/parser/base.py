"""Base parser interface for dependency files."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from licenselens.models import Dependency, Ecosystem


class BaseParser(ABC):
    """Abstract base class for dependency file parsers."""

    @property
    @abstractmethod
    def ecosystem(self) -> Ecosystem:
        """Return the ecosystem this parser handles."""

    @property
    @abstractmethod
    def file_patterns(self) -> list[str]:
        """Return file patterns this parser can handle (e.g., ['pyproject.toml'])."""

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""

    @abstractmethod
    def parse(self, file_path: Path) -> list[Dependency]:
        """Parse the dependency file and return a list of dependencies."""

    def find_files(self, project_dir: Path) -> list[Path]:
        """Find all dependency files in the project directory."""
        found = []
        for pattern in self.file_patterns:
            candidate = project_dir / pattern
            if candidate.exists():
                found.append(candidate)
        return found
