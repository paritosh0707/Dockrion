"""
Requirements Parsing
====================

Parses Python requirements from strings and files.
Handles various requirement formats including:
- Simple: package>=1.0.0
- With extras: package[extra1,extra2]>=1.0.0
- Environment markers: package>=1.0.0; python_version>="3.8"
- Comments and blank lines
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .version import VersionConstraint, parse_version_constraint


@dataclass
class Requirement:
    """
    Represents a parsed Python package requirement.

    Attributes:
        name: Package name (normalized to lowercase with underscores)
        constraints: List of version constraints
        extras: Optional list of extras (e.g., [dev, test])
        marker: Optional environment marker
        original: Original requirement string
    """

    name: str
    constraints: List[VersionConstraint] = field(default_factory=list)
    extras: List[str] = field(default_factory=list)
    marker: Optional[str] = None
    original: str = ""

    def __str__(self) -> str:
        """Convert back to requirement string."""
        result = self.name
        if self.extras:
            result += f"[{','.join(self.extras)}]"
        if self.constraints:
            result += ",".join(str(c) for c in self.constraints)
        if self.marker:
            result += f"; {self.marker}"
        return result

    @property
    def normalized_name(self) -> str:
        """Get normalized package name for comparison."""
        return normalize_package_name(self.name)

    def to_pip_string(self) -> str:
        """Convert to pip-installable string."""
        result = self.name
        if self.extras:
            result += f"[{','.join(self.extras)}]"
        if self.constraints:
            result += ",".join(str(c) for c in self.constraints)
        if self.marker:
            result += f"; {self.marker}"
        return result


def normalize_package_name(name: str) -> str:
    """
    Normalize package name for comparison.

    PEP 503: Replace any run of non-alphanumeric characters with a single hyphen,
    and convert to lowercase.
    """
    return re.sub(r"[-_.]+", "-", name.lower()).strip("-")


def parse_requirement(req_str: str) -> Optional[Requirement]:
    """
    Parse a single requirement string.

    Args:
        req_str: Requirement string like "package>=1.0.0" or "package[extra]>=1.0,<2.0"

    Returns:
        Requirement object, or None if line is empty/comment

    Examples:
        >>> parse_requirement("pydantic>=2.5")
        Requirement(name='pydantic', constraints=[>=2.5], ...)

        >>> parse_requirement("langchain[openai]>=0.1.0,<1.0.0")
        Requirement(name='langchain', extras=['openai'], constraints=[>=0.1.0, <1.0.0], ...)
    """
    req_str = req_str.strip()

    # Skip empty lines and comments
    if not req_str or req_str.startswith("#"):
        return None

    # Skip -r, -e, --index-url, etc.
    if req_str.startswith("-") or req_str.startswith("--"):
        return None

    # Extract environment marker (after semicolon)
    marker = None
    if ";" in req_str:
        req_str, marker = req_str.split(";", 1)
        req_str = req_str.strip()
        marker = marker.strip()

    # Extract extras (in square brackets)
    extras: List[str] = []
    extras_match = re.search(r"\[([^\]]+)\]", req_str)
    if extras_match:
        extras = [e.strip() for e in extras_match.group(1).split(",")]
        req_str = re.sub(r"\[[^\]]+\]", "", req_str)

    # Extract package name and version constraints
    # Pattern: package_name followed by optional version specifiers
    # Version specifiers start with: ==, !=, >=, <=, >, <, ~=
    version_ops = r"(?:==|!=|>=|<=|>|<|~=)"
    match = re.match(rf"^([A-Za-z0-9][-A-Za-z0-9._]*)({version_ops}.*)?$", req_str)

    if not match:
        # Try to extract at least the name
        name_match = re.match(r"^([A-Za-z0-9][-A-Za-z0-9._]*)", req_str)
        if name_match:
            return Requirement(
                name=name_match.group(1),
                extras=extras,
                marker=marker,
                original=req_str,
            )
        return None

    name = match.group(1)
    version_str = match.group(2) or ""

    # Parse version constraints
    constraints: List[VersionConstraint] = []
    if version_str:
        # Split by comma for multiple constraints
        for part in version_str.split(","):
            part = part.strip()
            if part:
                try:
                    constraints.append(parse_version_constraint(part))
                except ValueError:
                    # Skip invalid constraints but keep the requirement
                    pass

    return Requirement(
        name=name,
        constraints=constraints,
        extras=extras,
        marker=marker,
        original=req_str,
    )


def parse_requirements_string(content: str) -> List[Requirement]:
    """
    Parse requirements from a string (e.g., requirements.txt content).

    Args:
        content: Multi-line string with requirements

    Returns:
        List of Requirement objects
    """
    requirements: List[Requirement] = []

    for line in content.splitlines():
        # Handle line continuations
        line = line.split("#")[0].strip()  # Remove inline comments
        if not line:
            continue

        req = parse_requirement(line)
        if req:
            requirements.append(req)

    return requirements


def parse_requirements_file(file_path: Path) -> List[Requirement]:
    """
    Parse requirements from a file.

    Args:
        file_path: Path to requirements.txt or similar file

    Returns:
        List of Requirement objects

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")
    return parse_requirements_string(content)

