"""
Version Conflict Resolution
===========================

Handles version conflicts between user-specified dependencies
and dockrion's required dependencies.

Resolution Rules:
1. User version compatible with dockrion requirement → User version wins
2. User version incompatible with dockrion core requirements → Error
3. User version for dockrion-added packages (telemetry, langchain) →
   User version wins if compatible with other dockrion packages

Version Source:
- Versions are read from pyproject.toml files (single source of truth)
- Fallback to hardcoded values when pyproject.toml is not available
  (e.g., when running inside Docker without source code)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

# Import pyproject utilities for single source of truth
from ..utils.workspace import (
    get_core_dependencies_from_pyproject,
    get_framework_dependencies_from_pyproject,
    get_runtime_dependencies_from_pyproject,
)
from .parser import Requirement, normalize_package_name
from .version import (
    Version,
    VersionConstraint,
    VersionOperator,
    constraints_are_compatible,
)


class ConflictResolution(str, Enum):
    """How a version conflict was resolved."""

    USER_OVERRIDE = "user_override"  # User version overrides dockrion
    DOCKRION_WINS = "dockrion_wins"  # Dockrion version is required
    MERGED = "merged"  # Both constraints are compatible
    ERROR = "error"  # Incompatible versions


class DependencyType(str, Enum):
    """Classification of dependency origin."""

    CORE = "core"  # Core dockrion dependency (pydantic, etc.)
    RUNTIME = "runtime"  # Runtime dependencies (fastapi, uvicorn)
    FRAMEWORK = "framework"  # Framework deps (langgraph, langchain)
    OPTIONAL = "optional"  # Optional/telemetry deps (langfuse, etc.)
    USER = "user"  # User-specified only


# ============================================================================
# Fallback Values (used when pyproject.toml is not available)
# ============================================================================
# These are used when running inside Docker or when source code is not present.
# The primary source of truth is pyproject.toml - these are safety fallbacks.

_FALLBACK_CORE_DEPENDENCIES = {
    "pydantic": ">=2.5",
    "pyyaml": ">=6.0",
    "jinja2": ">=3.1.0",
    "typer": ">=0.12.0",
    "rich": ">=13.7.0",
    "requests": ">=2.31",
}

_FALLBACK_RUNTIME_DEPENDENCIES = {
    "fastapi": ">=0.109.0",
    "uvicorn": ">=0.27.0",
    "prometheus-client": ">=0.20",
    "httpx": ">=0.26.0",
    "aiohttp": ">=3.9.0",
}

_FALLBACK_FRAMEWORK_DEPENDENCIES = {
    "langgraph": {
        "langgraph": ">=0.0.20",
        "langchain-core": ">=0.1.0",
    },
    "langchain": {
        "langchain": ">=0.1.0",
        "langchain-core": ">=0.1.0",
    },
    "crewai": {
        "crewai": ">=0.28.0",
        "crewai-tools": ">=0.2.0",
    },
    "autogen": {
        "pyautogen": ">=0.2.0",
    },
    "llamaindex": {
        "llama-index": ">=0.10.0",
        "llama-index-core": ">=0.10.0",
    },
}


# ============================================================================
# Dynamic Dependencies (loaded from pyproject.toml)
# ============================================================================


def _get_core_dependencies() -> Dict[str, str]:
    """
    Get core dependencies, preferring pyproject.toml values.

    Falls back to hardcoded values when pyproject.toml is not available.
    """
    deps = get_core_dependencies_from_pyproject()
    if deps:
        return deps
    return _FALLBACK_CORE_DEPENDENCIES.copy()


def _get_runtime_dependencies() -> Dict[str, str]:
    """
    Get runtime dependencies, preferring pyproject.toml values.

    Falls back to hardcoded values when pyproject.toml is not available.
    """
    deps = get_runtime_dependencies_from_pyproject()
    if deps:
        return deps
    return _FALLBACK_RUNTIME_DEPENDENCIES.copy()


def _get_framework_dependencies(framework: str) -> Dict[str, str]:
    """
    Get framework dependencies, preferring pyproject.toml values.

    Falls back to hardcoded values when pyproject.toml is not available.
    """
    deps = get_framework_dependencies_from_pyproject(framework)
    if deps:
        return deps
    return _FALLBACK_FRAMEWORK_DEPENDENCIES.get(framework.lower(), {}).copy()


# Exported constants (computed on first access)
# These are the dependencies that will be used throughout the codebase
CORE_DEPENDENCIES = _get_core_dependencies()
RUNTIME_DEPENDENCIES = _get_runtime_dependencies()
FRAMEWORK_DEPENDENCIES = {
    fw: _get_framework_dependencies(fw)
    for fw in ["langgraph", "langchain", "crewai", "autogen", "llamaindex"]
}

# Optional dependencies (telemetry, observability) - not in pyproject.toml
OPTIONAL_DEPENDENCIES = {
    "langfuse": ">=2.0.0",
    "langsmith": ">=0.1.0",
    "regex": ">=2023.12.0",
}


class DependencyConflictError(Exception):
    """
    Raised when user and dockrion dependencies are incompatible.

    Provides detailed information about the conflict and resolution hints.
    """

    def __init__(
        self,
        package: str,
        user_constraint: str,
        dockrion_constraint: str,
        message: str,
        resolution_hints: Optional[List[str]] = None,
    ):
        self.package = package
        self.user_constraint = user_constraint
        self.dockrion_constraint = dockrion_constraint
        self.resolution_hints = resolution_hints or []

        hint_text = ""
        if self.resolution_hints:
            hint_text = "\n\nHow to resolve:\n" + "\n".join(
                f"  {i+1}. {h}" for i, h in enumerate(self.resolution_hints)
            )

        full_message = (
            f"Dependency conflict for '{package}':\n"
            f"  - Your requirement: {user_constraint}\n"
            f"  - Dockrion requires: {dockrion_constraint}\n"
            f"\n{message}{hint_text}"
        )
        super().__init__(full_message)


@dataclass
class ResolvedDependency:
    """Result of resolving a dependency conflict."""

    package: str
    constraint: str
    resolution: ConflictResolution
    source: str  # "user", "dockrion", or "merged"
    original_user: Optional[str] = None
    original_dockrion: Optional[str] = None


class VersionResolver:
    """
    Resolves version conflicts between user and dockrion dependencies.

    The resolver follows these rules:
    1. Core dependencies: User can override IF their version satisfies
       dockrion's minimum requirement
    2. Framework dependencies: User can override with compatibility check
    3. Optional dependencies: User always wins (but warns if incompatible)
    """

    def __init__(self, framework: Optional[str] = None):
        """
        Initialize resolver.

        Args:
            framework: The agent framework (langgraph, langchain, etc.)
        """
        self.framework = framework.lower() if framework else None
        self._build_dockrion_deps()

    def _build_dockrion_deps(self) -> None:
        """Build the complete dockrion dependency map."""
        self.dockrion_deps: dict[str, tuple[str, DependencyType]] = {}

        # Add core dependencies
        for pkg, constraint in CORE_DEPENDENCIES.items():
            self.dockrion_deps[normalize_package_name(pkg)] = (constraint, DependencyType.CORE)

        # Add runtime dependencies
        for pkg, constraint in RUNTIME_DEPENDENCIES.items():
            self.dockrion_deps[normalize_package_name(pkg)] = (constraint, DependencyType.RUNTIME)

        # Add framework-specific dependencies
        if self.framework and self.framework in FRAMEWORK_DEPENDENCIES:
            for pkg, constraint in FRAMEWORK_DEPENDENCIES[self.framework].items():
                self.dockrion_deps[normalize_package_name(pkg)] = (
                    constraint,
                    DependencyType.FRAMEWORK,
                )

        # Add optional dependencies
        for pkg, constraint in OPTIONAL_DEPENDENCIES.items():
            self.dockrion_deps[normalize_package_name(pkg)] = (constraint, DependencyType.OPTIONAL)

    def get_dependency_type(self, package: str) -> DependencyType:
        """Get the type of a dependency."""
        normalized = normalize_package_name(package)
        if normalized in self.dockrion_deps:
            return self.dockrion_deps[normalized][1]
        return DependencyType.USER

    def resolve(
        self,
        user_req: Requirement,
        dockrion_constraint: Optional[str] = None,
    ) -> ResolvedDependency:
        """
        Resolve a potential conflict between user and dockrion requirements.

        Args:
            user_req: User's requirement
            dockrion_constraint: Dockrion's constraint (if any)

        Returns:
            ResolvedDependency with resolution details

        Raises:
            DependencyConflictError: If versions are incompatible
        """
        normalized_name = user_req.normalized_name
        dep_type = self.get_dependency_type(normalized_name)

        # If dockrion doesn't care about this package, user wins
        if dep_type == DependencyType.USER:
            return ResolvedDependency(
                package=user_req.name,
                constraint=user_req.to_pip_string(),
                resolution=ConflictResolution.USER_OVERRIDE,
                source="user",
                original_user=user_req.to_pip_string(),
            )

        # Get dockrion's constraint
        if dockrion_constraint is None:
            dockrion_constraint = self.dockrion_deps.get(normalized_name, (None, None))[0]

        if dockrion_constraint is None:
            # No dockrion constraint, user wins
            return ResolvedDependency(
                package=user_req.name,
                constraint=user_req.to_pip_string(),
                resolution=ConflictResolution.USER_OVERRIDE,
                source="user",
                original_user=user_req.to_pip_string(),
            )

        # Check compatibility
        user_constraint_str = ",".join(str(c) for c in user_req.constraints)
        if not user_constraint_str:
            # User didn't specify version, use dockrion's
            return ResolvedDependency(
                package=user_req.name,
                constraint=f"{user_req.name}{dockrion_constraint}",
                resolution=ConflictResolution.DOCKRION_WINS,
                source="dockrion",
                original_user=user_req.to_pip_string(),
                original_dockrion=f"{normalized_name}{dockrion_constraint}",
            )

        # Check if user's constraints are compatible with dockrion's
        compatible = self._check_compatibility(user_req.constraints, dockrion_constraint)

        if compatible:
            # User's version is compatible - user wins
            return ResolvedDependency(
                package=user_req.name,
                constraint=user_req.to_pip_string(),
                resolution=ConflictResolution.USER_OVERRIDE,
                source="user",
                original_user=user_req.to_pip_string(),
                original_dockrion=f"{normalized_name}{dockrion_constraint}",
            )
        else:
            # Incompatible - handle based on dependency type
            if dep_type in (DependencyType.CORE, DependencyType.RUNTIME):
                # Critical dependencies - raise error
                raise DependencyConflictError(
                    package=user_req.name,
                    user_constraint=user_req.to_pip_string(),
                    dockrion_constraint=f"{normalized_name}{dockrion_constraint}",
                    message=(
                        f"This is a {'core' if dep_type == DependencyType.CORE else 'runtime'} "
                        f"dockrion dependency. The version you specified is not compatible "
                        f"with dockrion's requirements."
                    ),
                    resolution_hints=[
                        f"Update your requirement to satisfy {dockrion_constraint}",
                        "Remove the version constraint to use dockrion's default",
                        "Check dockrion's compatibility matrix for supported versions",
                    ],
                )
            elif dep_type == DependencyType.FRAMEWORK:
                # Framework dependencies - try to find compatible version
                # For now, prefer dockrion's version but warn
                return ResolvedDependency(
                    package=user_req.name,
                    constraint=f"{user_req.name}{dockrion_constraint}",
                    resolution=ConflictResolution.DOCKRION_WINS,
                    source="dockrion",
                    original_user=user_req.to_pip_string(),
                    original_dockrion=f"{normalized_name}{dockrion_constraint}",
                )
            else:
                # Optional dependencies - user wins with warning
                return ResolvedDependency(
                    package=user_req.name,
                    constraint=user_req.to_pip_string(),
                    resolution=ConflictResolution.USER_OVERRIDE,
                    source="user",
                    original_user=user_req.to_pip_string(),
                    original_dockrion=f"{normalized_name}{dockrion_constraint}",
                )

    def _check_compatibility(
        self,
        user_constraints: List[VersionConstraint],
        dockrion_constraint_str: str,
    ) -> bool:
        """
        Check if user constraints are compatible with dockrion's.

        Returns True if user's specified version(s) satisfy dockrion's minimum.
        """
        from .version import parse_constraints

        dockrion_constraints = parse_constraints(dockrion_constraint_str)

        # Check if the constraint ranges overlap
        return constraints_are_compatible(user_constraints, dockrion_constraints)

    def _satisfies_minimum(
        self,
        user_constraints: List[VersionConstraint],
        min_version: Version,
    ) -> bool:
        """Check if user constraints allow at least the minimum version."""
        for constraint in user_constraints:
            if constraint.operator == VersionOperator.EQ:
                # Exact version - must be >= minimum
                if constraint.version < min_version:
                    return False
            elif constraint.operator == VersionOperator.LT:
                # Less than - upper bound must be > minimum
                if constraint.version <= min_version:
                    return False
            elif constraint.operator == VersionOperator.LE:
                # Less than or equal - upper bound must be >= minimum
                if constraint.version < min_version:
                    return False
            # GE, GT, NE, COMPAT are all compatible with minimum by definition
        return True


def resolve_version_conflict(
    user_requirement: str,
    dockrion_constraint: str,
    package_name: str,
    dependency_type: str = "core",
) -> ResolvedDependency:
    """
    Convenience function to resolve a single version conflict.

    Args:
        user_requirement: User's full requirement string (e.g., "pydantic==2.4")
        dockrion_constraint: Dockrion's constraint (e.g., ">=2.5")
        package_name: Package name for error messages
        dependency_type: Type of dependency ("core", "runtime", "optional")

    Returns:
        ResolvedDependency with resolution details
    """
    from .parser import parse_requirement

    user_req = parse_requirement(user_requirement)
    if not user_req:
        raise ValueError(f"Invalid requirement string: {user_requirement}")

    resolver = VersionResolver()
    return resolver.resolve(user_req, dockrion_constraint)

