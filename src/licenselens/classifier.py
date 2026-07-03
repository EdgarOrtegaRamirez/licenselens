"""License classifier and compatibility engine."""

from __future__ import annotations

from licenselens.models import (
    Dependency,
    License,
    LicenseCategory,
    LicenseConflict,
    Severity,
)

# SPDX license ID to License mapping
KNOWN_LICENSES: dict[str, License] = {
    # Permissive
    "MIT": License("MIT", "MIT License", LicenseCategory.PERMISSIVE, is_osi_approved=True, is_fsf_free=True),
    "Apache-2.0": License("Apache-2.0", "Apache License 2.0", LicenseCategory.PERMISSIVE, is_osi_approved=True, is_fsf_free=True),
    "BSD-2-Clause": License("BSD-2-Clause", "BSD 2-Clause License", LicenseCategory.PERMISSIVE, is_osi_approved=True, is_fsf_free=True),
    "BSD-3-Clause": License("BSD-3-Clause", "BSD 3-Clause License", LicenseCategory.PERMISSIVE, is_osi_approved=True, is_fsf_free=True),
    "ISC": License("ISC", "ISC License", LicenseCategory.PERMISSIVE, is_osi_approved=True, is_fsf_free=True),
    "0BSD": License("0BSD", "Zero-Clause BSD", LicenseCategory.PERMISSIVE, is_osi_approved=True, is_fsf_free=True),
    "Unlicense": License("Unlicense", "The Unlicense", LicenseCategory.PERMISSIVE, is_osi_approved=True, is_fsf_free=True),
    "CC0-1.0": License("CC0-1.0", "Creative Commons Zero 1.0", LicenseCategory.PERMISSIVE),
    "Zlib": License("Zlib", "zlib License", LicenseCategory.PERMISSIVE, is_osi_approved=True, is_fsf_free=True),
    "BlueOak-1.0.0": License("BlueOak-1.0.0", "Blue Oak Model License 1.0.0", LicenseCategory.PERMISSIVE, is_osi_approved=True),
    "Python-2.0": License("Python-2.0", "Python License 2.0", LicenseCategory.PERMISSIVE, is_osi_approved=True, is_fsf_free=True),
    # Weak copyleft
    "LGPL-2.1": License("LGPL-2.1", "GNU Lesser General Public License v2.1", LicenseCategory.WEAK_COPYLEFT, is_osi_approved=True, is_fsf_free=True),
    "LGPL-3.0": License("LGPL-3.0", "GNU Lesser General Public License v3.0", LicenseCategory.WEAK_COPYLEFT, is_osi_approved=True, is_fsf_free=True),
    "MPL-2.0": License("MPL-2.0", "Mozilla Public License 2.0", LicenseCategory.WEAK_COPYLEFT, is_osi_approved=True, is_fsf_free=True),
    "EPL-1.0": License("EPL-1.0", "Eclipse Public License 1.0", LicenseCategory.WEAK_COPYLEFT, is_osi_approved=True, is_fsf_free=True),
    "EPL-2.0": License("EPL-2.0", "Eclipse Public License 2.0", LicenseCategory.WEAK_COPYLEFT, is_osi_approved=True, is_fsf_free=True),
    "CDDL-1.0": License("CDDL-1.0", "Common Development and Distribution License 1.0", LicenseCategory.WEAK_COPYLEFT, is_osi_approved=True),
    "CECILL-2.0": License("CECILL-2.0", "CeCILL License 2.0", LicenseCategory.WEAK_COPYLEFT, is_osi_approved=True),
    "EUPL-1.1": License("EUPL-1.1", "European Union Public License 1.1", LicenseCategory.WEAK_COPYLEFT, is_osi_approved=True),
    "Artistic-2.0": License("Artistic-2.0", "Artistic License 2.0", LicenseCategory.WEAK_COPYLEFT, is_osi_approved=True, is_fsf_free=True),
    "BSL-1.0": License("BSL-1.0", "Boost Software License 1.0", LicenseCategory.PERMISSIVE, is_osi_approved=True),
    # Strong copyleft
    "GPL-2.0": License("GPL-2.0", "GNU General Public License v2.0", LicenseCategory.STRONG_COPYLEFT, is_osi_approved=True, is_fsf_free=True),
    "GPL-3.0": License("GPL-3.0", "GNU General Public License v3.0", LicenseCategory.STRONG_COPYLEFT, is_osi_approved=True, is_fsf_free=True),
    "AGPL-3.0": License(
        "AGPL-3.0", "GNU Affero General Public License v3.0", LicenseCategory.NETWORK_COPYLEFT, is_osi_approved=True, is_fsf_free=True
    ),
    # Network copyleft
    "SSPL-1.0": License("SSPL-1.0", "Server Side Public License 1.0", LicenseCategory.NETWORK_COPYLEFT),
    "BSL-1.1": License("BSL-1.1", "Business Source License 1.1", LicenseCategory.NETWORK_COPYLEFT),
    # Proprietary
    "LicenseRef-Proprietary": License("LicenseRef-Proprietary", "Proprietary", LicenseCategory.PROPRIETARY),
}

# License compatibility matrix
# (license_a, license_b) -> (compatible, notes)
# True = compatible, False = conflict, None = needs investigation
LICENSE_COMPATIBILITY: dict[tuple[str, str], tuple[bool, str]] = {
    # Permissive licenses are compatible with everything
    ("MIT", "MIT"): (True, "Same license"),
    ("MIT", "Apache-2.0"): (True, "MIT and Apache 2.0 are compatible"),
    ("MIT", "BSD-2-Clause"): (True, "Both permissive licenses"),
    ("MIT", "BSD-3-Clause"): (True, "Both permissive licenses"),
    ("MIT", "ISC"): (True, "Both permissive licenses, functionally equivalent"),
    ("Apache-2.0", "Apache-2.0"): (True, "Same license"),
    ("Apache-2.0", "MIT"): (True, "Apache 2.0 and MIT are compatible"),
    # Permissive + Weak copyleft
    ("MIT", "LGPL-2.1"): (True, "MIT code can be used with LGPL libraries"),
    ("MIT", "LGPL-3.0"): (True, "MIT code can be used with LGPL libraries"),
    ("MIT", "MPL-2.0"): (True, "MIT is compatible with MPL-2.0"),
    ("Apache-2.0", "LGPL-2.1"): (True, "Apache 2.0 compatible with LGPL"),
    ("Apache-2.0", "LGPL-3.0"): (True, "Apache 2.0 compatible with LGPL 3.0"),
    # Permissive + Strong copyleft
    ("MIT", "GPL-2.0"): (True, "MIT code can be relicensed under GPL-2.0"),
    ("MIT", "GPL-3.0"): (True, "MIT code can be relicensed under GPL-3.0"),
    ("Apache-2.0", "GPL-2.0"): (False, "Apache 2.0 patent clauses incompatible with GPL-2.0"),
    ("Apache-2.0", "GPL-3.0"): (True, "Apache 2.0 compatible with GPL-3.0"),
    ("MIT", "AGPL-3.0"): (True, "MIT code can be relicensed under AGPL-3.0"),
    ("Apache-2.0", "AGPL-3.0"): (True, "Apache 2.0 compatible with AGPL-3.0"),
    # Weak copyleft interactions
    ("LGPL-2.1", "LGPL-2.1"): (True, "Same license family"),
    ("LGPL-3.0", "LGPL-3.0"): (True, "Same license family"),
    ("MPL-2.0", "MPL-2.0"): (True, "Same license"),
    ("MPL-2.0", "MIT"): (True, "MPL-2.0 compatible with MIT"),
    ("LGPL-2.1", "GPL-2.0"): (True, "LGPL-2.1 is a subset of GPL-2.0"),
    ("LGPL-3.0", "GPL-3.0"): (True, "LGPL-3.0 is a subset of GPL-3.0"),
    # Strong copyleft conflicts
    ("GPL-2.0", "GPL-3.0"): (False, "GPL-2.0 and GPL-3.0 are incompatible"),
    ("GPL-2.0", "AGPL-3.0"): (False, "GPL-2.0 and AGPL-3.0 are incompatible"),
    ("GPL-2.0", "MPL-2.0"): (True, "MPL-2.0 has GPL-2.0 compatibility clause"),
    ("GPL-3.0", "AGPL-3.0"): (True, "AGPL-3.0 is GPL-3.0 with network clause"),
    # Network copyleft
    ("SSPL-1.0", "SSPL-1.0"): (True, "Same license"),
    ("SSPL-1.0", "AGPL-3.0"): (False, "SSPL and AGPL are incompatible"),
    ("SSPL-1.0", "MIT"): (False, "SSPL is incompatible with permissive licenses"),
    ("AGPL-3.0", "AGPL-3.0"): (True, "Same license"),
}


def classify_license(license_id: str) -> License:
    """Classify a license by its SPDX ID."""
    normalized = license_id.strip()
    if normalized in KNOWN_LICENSES:
        return KNOWN_LICENSES[normalized]

    # Try fuzzy matching
    upper = normalized.upper()
    for known_id, license_obj in KNOWN_LICENSES.items():
        if known_id.upper() == upper:
            return license_obj

    # Unknown license
    return License(
        spdx_id=normalized,
        name=normalized,
        category=LicenseCategory.UNKNOWN,
    )


def check_compatibility(license_a: str, license_b: str) -> tuple[bool, str]:
    """Check if two licenses are compatible. Returns (compatible, notes)."""
    # Normalize
    la, lb = license_a.strip(), license_b.strip()

    # Check direct lookup (both orderings)
    key = (la, lb)
    if key in LICENSE_COMPATIBILITY:
        return LICENSE_COMPATIBILITY[key]

    key_rev = (lb, la)
    if key_rev in LICENSE_COMPATIBILITY:
        compat, notes = LICENSE_COMPATIBILITY[key_rev]
        return compat, notes

    # Default: unknown compatibility
    return None, f"Unknown compatibility between {la} and {lb}"  # type: ignore


def find_conflicts(dependencies: list[Dependency]) -> list[LicenseConflict]:
    """Find license conflicts among dependencies."""
    conflicts = []
    seen_pairs: set[tuple[str, str]] = set()

    # Get unique licenses
    licenses = set()
    for dep in dependencies:
        if dep.license_id and dep.license_id not in ("UNKNOWN", "UNLICENSED"):
            licenses.add(dep.license_id)

    # Check all pairs
    license_list = sorted(licenses)
    for i, la in enumerate(license_list):
        for lb in license_list[i + 1 :]:
            pair = (la, lb)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            compatible, notes = check_compatibility(la, lb)
            if compatible is False:
                conflicts.append(
                    LicenseConflict(
                        license_a=la,
                        license_b=lb,
                        message=notes,
                        severity=Severity.ERROR,
                    )
                )
            elif compatible is None:
                conflicts.append(
                    LicenseConflict(
                        license_a=la,
                        license_b=lb,
                        message=notes,
                        severity=Severity.WARNING,
                    )
                )

    return conflicts
