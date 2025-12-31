"""
Version Parsing and Comparison
==============================

Provides utilities for parsing and comparing Python package versions
following PEP 440 version specifiers.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


class VersionOperator(str, Enum):
    """Version comparison operators."""

    EQ = "=="  # Exact match
    NE = "!="  # Not equal
    GE = ">="  # Greater or equal
    GT = ">"  # Greater than
    LE = "<="  # Less or equal
    LT = "<"  # Less than
    COMPAT = "~="  # Compatible release


@dataclass
class Version:
    """
    Represents a parsed version number.

    Supports standard version formats like:
    - 1.0.0
    - 2.5.3
    - 0.0.1
    - 1.0.0a1 (alpha)
    - 1.0.0b2 (beta)
    - 1.0.0rc1 (release candidate)
    """

    major: int
    minor: int = 0
    patch: int = 0
    pre_release: Optional[str] = None
    pre_release_num: Optional[int] = None

    def __str__(self) -> str:
        """Convert version to string."""
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_release:
            base += f"{self.pre_release}{self.pre_release_num or ''}"
        return base

    def as_tuple(self) -> Tuple[int, int, int, int, int]:
        """
        Convert to tuple for comparison.

        Pre-releases are sorted before releases:
        - a/alpha = -3
        - b/beta = -2
        - rc = -1
        - release = 0
        """
        pre_order = 0
        pre_num = 0

        if self.pre_release:
            pre_lower = self.pre_release.lower()
            if pre_lower in ("a", "alpha"):
                pre_order = -3
            elif pre_lower in ("b", "beta"):
                pre_order = -2
            elif pre_lower in ("rc", "c"):
                pre_order = -1
            pre_num = self.pre_release_num or 0

        return (self.major, self.minor, self.patch, pre_order, pre_num)

    def __lt__(self, other: "Version") -> bool:
        return self.as_tuple() < other.as_tuple()

    def __le__(self, other: "Version") -> bool:
        return self.as_tuple() <= other.as_tuple()

    def __gt__(self, other: "Version") -> bool:
        return self.as_tuple() > other.as_tuple()

    def __ge__(self, other: "Version") -> bool:
        return self.as_tuple() >= other.as_tuple()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return False
        return self.as_tuple() == other.as_tuple()

    def __hash__(self) -> int:
        return hash(self.as_tuple())


def parse_version(version_str: str) -> Version:
    """
    Parse a version string into a Version object.

    Args:
        version_str: Version string like "1.0.0", "2.5", "1.0.0a1"

    Returns:
        Version object

    Raises:
        ValueError: If version string is invalid
    """
    version_str = version_str.strip()

    # Handle version with pre-release
    # Pattern: major.minor.patch[pre_release][pre_release_num]
    pattern = r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:(a|b|rc|alpha|beta|c)(\d+)?)?$"
    match = re.match(pattern, version_str, re.IGNORECASE)

    if not match:
        raise ValueError(f"Invalid version string: '{version_str}'")

    major = int(match.group(1))
    minor = int(match.group(2)) if match.group(2) else 0
    patch = int(match.group(3)) if match.group(3) else 0
    pre_release = match.group(4) if match.group(4) else None
    pre_release_num = int(match.group(5)) if match.group(5) else None

    return Version(
        major=major,
        minor=minor,
        patch=patch,
        pre_release=pre_release,
        pre_release_num=pre_release_num,
    )


@dataclass
class VersionConstraint:
    """
    Represents a version constraint like >=1.0.0 or ==2.5.3.

    Multiple constraints can be combined (e.g., >=1.0.0,<2.0.0).
    """

    operator: VersionOperator
    version: Version

    def __str__(self) -> str:
        return f"{self.operator.value}{self.version}"

    def is_satisfied_by(self, version: Version) -> bool:
        """Check if a version satisfies this constraint."""
        if self.operator == VersionOperator.EQ:
            return version == self.version
        elif self.operator == VersionOperator.NE:
            return version != self.version
        elif self.operator == VersionOperator.GE:
            return version >= self.version
        elif self.operator == VersionOperator.GT:
            return version > self.version
        elif self.operator == VersionOperator.LE:
            return version <= self.version
        elif self.operator == VersionOperator.LT:
            return version < self.version
        elif self.operator == VersionOperator.COMPAT:
            # ~=X.Y.Z means >=X.Y.Z and <X.(Y+1).0
            # ~=X.Y means >=X.Y and <(X+1).0.0
            if version < self.version:
                return False
            if self.version.patch > 0:
                # ~=1.2.3 means >=1.2.3, <1.3.0
                upper = Version(self.version.major, self.version.minor + 1, 0)
            else:
                # ~=1.2 means >=1.2.0, <2.0.0
                upper = Version(self.version.major + 1, 0, 0)
            return version < upper
        return False


def parse_version_constraint(constraint_str: str) -> VersionConstraint:
    """
    Parse a version constraint string.

    Args:
        constraint_str: Constraint like ">=1.0.0", "==2.5.3", "~=1.2"

    Returns:
        VersionConstraint object

    Raises:
        ValueError: If constraint string is invalid
    """
    constraint_str = constraint_str.strip()

    # Try each operator (longer ones first to avoid partial matches)
    operators = sorted(VersionOperator, key=lambda x: -len(x.value))

    for op in operators:
        if constraint_str.startswith(op.value):
            version_part = constraint_str[len(op.value) :].strip()
            version = parse_version(version_part)
            return VersionConstraint(operator=op, version=version)

    # No operator found - assume exact match
    version = parse_version(constraint_str)
    return VersionConstraint(operator=VersionOperator.EQ, version=version)


def parse_constraints(constraints_str: str) -> List[VersionConstraint]:
    """
    Parse multiple version constraints (comma-separated).

    Args:
        constraints_str: String like ">=1.0.0,<2.0.0"

    Returns:
        List of VersionConstraint objects
    """
    constraints = []
    for part in constraints_str.split(","):
        part = part.strip()
        if part:
            constraints.append(parse_version_constraint(part))
    return constraints


def constraints_are_compatible(
    constraints1: List[VersionConstraint],
    constraints2: List[VersionConstraint],
) -> bool:
    """
    Check if two sets of constraints have any overlapping valid versions.

    This is a simplified check that looks for obvious incompatibilities.
    """
    # Get the effective range for each set
    min1, max1 = _get_constraint_range(constraints1)
    min2, max2 = _get_constraint_range(constraints2)

    # Check for overlap
    # If min of one is greater than max of other, no overlap
    if min1 and max2 and min1 > max2:
        return False
    if min2 and max1 and min2 > max1:
        return False

    return True


def _get_constraint_range(
    constraints: List[VersionConstraint],
) -> Tuple[Optional[Version], Optional[Version]]:
    """Get the effective min and max versions from constraints."""
    min_ver: Optional[Version] = None
    max_ver: Optional[Version] = None

    for c in constraints:
        if c.operator in (VersionOperator.GE, VersionOperator.GT, VersionOperator.COMPAT):
            if min_ver is None or c.version > min_ver:
                min_ver = c.version
        elif c.operator in (VersionOperator.LE, VersionOperator.LT):
            if max_ver is None or c.version < max_ver:
                max_ver = c.version
        elif c.operator == VersionOperator.EQ:
            # Exact match - both min and max
            min_ver = c.version
            max_ver = c.version

    return min_ver, max_ver

