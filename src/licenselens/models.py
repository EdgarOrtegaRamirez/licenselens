"""Data models for LicenseLens."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class LicenseCategory(Enum):
    """License categories for classification."""
    PERMISSIVE = "permissive"
    WEAK_COPYLEFT = "weak_copyleft"
    STRONG_COPYLEFT = "strong_copyleft"
    NETWORK_COPYLEFT = "network_copyleft"
    PROPRIETARY = "proprietary"
    UNKNOWN = "unknown"
    UNLICENSED = "unlicensed"


class Ecosystem(Enum):
    """Supported ecosystems."""
    PYTHON = "python"
    NODE = "node"
    GO = "go"
    RUST = "rust"
    UNKNOWN = "unknown"


class Severity(Enum):
    """Issue severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class License:
    """A software license."""
    spdx_id: str
    name: str
    category: LicenseCategory
    url: str = ""
    is_osi_approved: bool = False
    is_fsf_free: bool = False


@dataclass
class Dependency:
    """A project dependency with license info."""
    name: str
    version: str
    ecosystem: Ecosystem
    license_id: str = ""
    license_name: str = ""
    license_category: LicenseCategory = LicenseCategory.UNKNOWN
    is_direct: bool = True
    source_file: str = ""
    homepage: str = ""
    author: str = ""
    description: str = ""


@dataclass
class LicenseIssue:
    """A detected license issue."""
    severity: Severity
    dependency: Dependency
    message: str
    recommendation: str = ""
    rule_id: str = ""


@dataclass
class LicenseConflict:
    """A license compatibility conflict."""
    license_a: str
    license_b: str
    message: str
    severity: Severity = Severity.ERROR


@dataclass
class AuditSummary:
    """Summary of a license audit."""
    total_dependencies: int = 0
    direct_dependencies: int = 0
    transitive_dependencies: int = 0
    licenses_found: dict[str, int] = field(default_factory=dict)
    categories: dict[str, int] = field(default_factory=dict)
    issues_count: int = 0
    conflicts_count: int = 0
    ecosystems: dict[str, int] = field(default_factory=dict)


@dataclass
class AuditReport:
    """Complete audit report."""
    project_name: str
    summary: AuditSummary
    dependencies: list[Dependency] = field(default_factory=list)
    issues: list[LicenseIssue] = field(default_factory=list)
    conflicts: list[LicenseConflict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
