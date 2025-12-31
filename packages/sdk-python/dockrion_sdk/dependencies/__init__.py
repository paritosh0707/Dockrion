"""
Dockrion Dependency Management
==============================

Provides utilities for:
- Parsing requirements files and version specifiers
- Resolving version conflicts between user and dockrion dependencies
- Merging dependencies with smart conflict resolution

This module ensures compatibility between user-specified packages
and dockrion's required packages.
"""

from .merger import DependencyMerger, merge_dependencies
from .parser import (
    Requirement,
    parse_requirement,
    parse_requirements_file,
    parse_requirements_string,
)
from .resolver import (
    ConflictResolution,
    DependencyConflictError,
    VersionResolver,
    resolve_version_conflict,
)
from .version import Version, VersionConstraint, parse_version, parse_version_constraint

__all__ = [
    # Version utilities
    "Version",
    "VersionConstraint",
    "parse_version",
    "parse_version_constraint",
    # Parsing
    "Requirement",
    "parse_requirement",
    "parse_requirements_file",
    "parse_requirements_string",
    # Resolution
    "ConflictResolution",
    "DependencyConflictError",
    "VersionResolver",
    "resolve_version_conflict",
    # Merging
    "DependencyMerger",
    "merge_dependencies",
]

