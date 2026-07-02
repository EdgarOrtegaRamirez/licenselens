"""License resolution engine."""
from __future__ import annotations

import json
import urllib.request

from licenselens.classifier import classify_license
from licenselens.models import Dependency, Ecosystem


def resolve_license(dep: Dependency, offline: bool = False) -> Dependency:
    """Resolve the license for a dependency. Mutates and returns the dependency."""
    if dep.license_id:
        return dep

    if offline:
        dep.license_id = "UNKNOWN"
        dep.license_name = "Unknown"
        return dep

    license_id = None

    if dep.ecosystem == Ecosystem.PYTHON:
        license_id = _resolve_pypi(dep.name)
    elif dep.ecosystem == Ecosystem.NODE:
        license_id = _resolve_npm(dep.name)
    elif dep.ecosystem == Ecosystem.GO:
        license_id = _resolve_goproxy(dep.name)
    elif dep.ecosystem == Ecosystem.RUST:
        license_id = _resolve_crates(dep.name)

    if license_id:
        dep.license_id = license_id
        lic = classify_license(license_id)
        dep.license_name = lic.name
        dep.license_category = lic.category
    else:
        dep.license_id = "UNKNOWN"
        dep.license_name = "Unknown"

    return dep


def resolve_licenses(deps: list[Dependency], offline: bool = False) -> list[Dependency]:
    """Resolve licenses for a list of dependencies."""
    for dep in deps:
        resolve_license(dep, offline=offline)
    return deps


def _resolve_pypi(package_name: str) -> str | None:
    """Resolve license from PyPI API."""
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            info = data.get("info", {})
            return info.get("license") or info.get("license_expression")
    except Exception:
        return None


def _resolve_npm(package_name: str) -> str | None:
    """Resolve license from npm registry API."""
    try:
        url = f"https://registry.npmjs.org/{package_name}/latest"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            lic = data.get("license")
            if isinstance(lic, dict):
                return lic.get("type")
            return lic
    except Exception:
        return None


def _resolve_goproxy(module_path: str) -> str | None:
    """Resolve license from Go module (best effort via pkg.go.dev)."""
    # Go modules don't have a standard license API
    # Return None to indicate unknown
    return None


def _resolve_crates(crate_name: str) -> str | None:
    """Resolve license from crates.io API."""
    try:
        url = f"https://crates.io/api/v1/crates/{crate_name}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            crate = data.get("crate", {})
            return crate.get("license")
    except Exception:
        return None
