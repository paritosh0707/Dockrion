"""
Dependency Merger
=================

Merges user-specified dependencies with dockrion's requirements,
applying smart conflict resolution.

This is the main entry point for dependency management.

Version Source:
- The dockrion meta-package version is read from pyproject.toml
- This ensures version consistency across the codebase
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

# Import version utilities for single source of truth
from ..utils.workspace import get_dockrion_version
from .parser import Requirement, normalize_package_name, parse_requirements_file
from .resolver import (
    CORE_DEPENDENCIES,
    FRAMEWORK_DEPENDENCIES,
    OPTIONAL_DEPENDENCIES,
    RUNTIME_DEPENDENCIES,
    ConflictResolution,
    DependencyType,
    ResolvedDependency,
    VersionResolver,
)


def _get_dockrion_meta_package() -> str:
    """
    Get the dockrion meta-package requirement string.

    Uses the version from pyproject.toml as single source of truth.
    Falls back to a safe default if pyproject.toml is not available.
    """
    version = get_dockrion_version()
    return f"dockrion>={version}"


# Dockrion meta-package version constraint (computed from pyproject.toml)
DOCKRION_META_PACKAGE = _get_dockrion_meta_package()

logger = logging.getLogger(__name__)


@dataclass
class MergeResult:
    """Result of merging user and dockrion dependencies."""

    # Final merged requirements (ready for requirements.txt)
    requirements: List[str]

    # Resolution details for each package
    resolutions: Dict[str, ResolvedDependency] = field(default_factory=dict)

    # Warnings (non-fatal issues)
    warnings: List[str] = field(default_factory=list)

    # Packages that were user-overridden
    user_overrides: List[str] = field(default_factory=list)

    # Packages where dockrion version was used
    dockrion_versions: List[str] = field(default_factory=list)


class DependencyMerger:
    """
    Merges user dependencies with dockrion's requirements.

    Handles:
    - Reading user's requirements.txt
    - Resolving version conflicts
    - Generating merged requirements list
    - Reporting warnings and errors
    """

    def __init__(
        self,
        framework: str = "custom",
        observability: Optional[Dict[str, bool]] = None,
        has_safety_policies: bool = False,
    ):
        """
        Initialize the merger.

        Args:
            framework: Agent framework (langgraph, langchain, etc.)
            observability: Dict of enabled observability features
            has_safety_policies: Whether safety policies with redact_patterns are enabled
        """
        self.framework = framework.lower() if framework else "custom"
        self.observability = observability or {}
        self.has_safety_policies = has_safety_policies
        self.resolver = VersionResolver(framework=self.framework)

    def get_dockrion_requirements(self) -> Dict[str, str]:
        """
        Get all dockrion requirements based on configuration.

        Returns:
            Dict mapping package name to version constraint
        """
        deps: Dict[str, str] = {}

        # Core dependencies (always included)
        deps.update(CORE_DEPENDENCIES)

        # Runtime dependencies (always included for deployment)
        deps.update(RUNTIME_DEPENDENCIES)

        # Framework-specific dependencies
        if self.framework in FRAMEWORK_DEPENDENCIES:
            deps.update(FRAMEWORK_DEPENDENCIES[self.framework])

        # Observability dependencies
        if self.observability.get("langfuse"):
            deps["langfuse"] = OPTIONAL_DEPENDENCIES["langfuse"]
        if self.observability.get("langsmith"):
            deps["langsmith"] = OPTIONAL_DEPENDENCIES["langsmith"]

        # Safety policy dependencies
        if self.has_safety_policies:
            deps["regex"] = OPTIONAL_DEPENDENCIES["regex"]

        return deps

    def merge(
        self,
        user_requirements: Optional[List[Requirement]] = None,
        user_requirements_file: Optional[Path] = None,
        extra_dependencies: Optional[List[str]] = None,
    ) -> MergeResult:
        """
        Merge user requirements with dockrion requirements.

        Args:
            user_requirements: Parsed user requirements
            user_requirements_file: Path to user's requirements.txt
            extra_dependencies: Additional dependencies from Dockfile.yaml

        Returns:
            MergeResult with merged requirements and resolution details

        Raises:
            DependencyConflictError: If incompatible versions are detected
        """
        result = MergeResult(requirements=[])

        # Collect user requirements from all sources
        all_user_reqs: List[Requirement] = []

        if user_requirements:
            all_user_reqs.extend(user_requirements)

        if user_requirements_file and user_requirements_file.exists():
            try:
                file_reqs = parse_requirements_file(user_requirements_file)
                all_user_reqs.extend(file_reqs)
                logger.info(f"Loaded {len(file_reqs)} requirements from {user_requirements_file}")
            except FileNotFoundError:
                result.warnings.append(f"Requirements file not found: {user_requirements_file}")

        if extra_dependencies:
            from .parser import parse_requirement

            for dep_str in extra_dependencies:
                req = parse_requirement(dep_str)
                if req:
                    all_user_reqs.append(req)

        # Build user requirements map (normalized name -> requirement)
        user_req_map: Dict[str, Requirement] = {}
        for req in all_user_reqs:
            normalized = req.normalized_name
            if normalized in user_req_map:
                # Merge constraints from duplicate entries
                existing = user_req_map[normalized]
                existing.constraints.extend(req.constraints)
                if req.extras:
                    for extra in req.extras:
                        if extra not in existing.extras:
                            existing.extras.append(extra)
            else:
                user_req_map[normalized] = req

        # Get dockrion requirements
        dockrion_reqs = self.get_dockrion_requirements()

        # Track which packages we've processed
        processed: Set[str] = set()
        final_requirements: List[str] = []

        # Process user requirements first (they take priority)
        for normalized_name, user_req in user_req_map.items():
            dockrion_constraint = dockrion_reqs.get(normalized_name)

            if dockrion_constraint:
                # This package is in both user and dockrion requirements
                resolved = self.resolver.resolve(user_req, dockrion_constraint)
                result.resolutions[normalized_name] = resolved

                if resolved.resolution == ConflictResolution.USER_OVERRIDE:
                    result.user_overrides.append(resolved.package)
                    logger.debug(
                        f"User override for {resolved.package}: "
                        f"{resolved.original_user} (dockrion wanted {resolved.original_dockrion})"
                    )
                elif resolved.resolution == ConflictResolution.DOCKRION_WINS:
                    result.dockrion_versions.append(resolved.package)
                    result.warnings.append(
                        f"Using dockrion's version for {resolved.package}: "
                        f"{dockrion_constraint} (you specified {resolved.original_user})"
                    )

                final_requirements.append(resolved.constraint)
            else:
                # User-only package
                final_requirements.append(user_req.to_pip_string())
                result.resolutions[normalized_name] = ResolvedDependency(
                    package=user_req.name,
                    constraint=user_req.to_pip_string(),
                    resolution=ConflictResolution.USER_OVERRIDE,
                    source="user",
                    original_user=user_req.to_pip_string(),
                )

            processed.add(normalized_name)

        # Add dockrion requirements that user didn't specify
        for pkg_name, constraint in dockrion_reqs.items():
            normalized = normalize_package_name(pkg_name)
            if normalized not in processed:
                req_str = f"{pkg_name}{constraint}"
                final_requirements.append(req_str)
                result.resolutions[normalized] = ResolvedDependency(
                    package=pkg_name,
                    constraint=req_str,
                    resolution=ConflictResolution.DOCKRION_WINS,
                    source="dockrion",
                    original_dockrion=req_str,
                )
                result.dockrion_versions.append(pkg_name)
                processed.add(normalized)

        # Add dockrion meta-package if user didn't specify it
        # This ensures the dockrion package is always in requirements.txt
        # and Docker doesn't need a separate RUN command for it
        dockrion_normalized = normalize_package_name("dockrion")
        if dockrion_normalized not in processed:
            final_requirements.append(DOCKRION_META_PACKAGE)
            result.resolutions[dockrion_normalized] = ResolvedDependency(
                package="dockrion",
                constraint=DOCKRION_META_PACKAGE,
                resolution=ConflictResolution.DOCKRION_WINS,
                source="dockrion",
                original_dockrion=DOCKRION_META_PACKAGE,
            )
            result.dockrion_versions.append("dockrion")
            processed.add(dockrion_normalized)
            logger.debug(f"Added dockrion meta-package: {DOCKRION_META_PACKAGE}")

        result.requirements = final_requirements
        return result

    def generate_requirements_content(
        self,
        user_requirements_file: Optional[Path] = None,
        extra_dependencies: Optional[List[str]] = None,
        include_comments: bool = True,
    ) -> str:
        """
        Generate the final requirements.txt content.

        Args:
            user_requirements_file: Path to user's requirements.txt
            extra_dependencies: Additional dependencies from Dockfile.yaml
            include_comments: Whether to include section comments

        Returns:
            String content for requirements.txt
        """
        merge_result = self.merge(
            user_requirements_file=user_requirements_file,
            extra_dependencies=extra_dependencies,
        )

        lines: List[str] = []

        if include_comments:
            lines.extend(
                [
                    "# ============================================================================",
                    "# Dockrion Agent Runtime - Python Dependencies",
                    "# ============================================================================",
                    f"# Framework: {self.framework}",
                    "# Generated by Dockrion SDK",
                    "# ============================================================================",
                    "",
                ]
            )

        # Group requirements by type
        core_reqs: List[str] = []
        runtime_reqs: List[str] = []
        framework_reqs: List[str] = []
        optional_reqs: List[str] = []
        user_only_reqs: List[str] = []

        for normalized_name, resolution in merge_result.resolutions.items():
            dep_type = self.resolver.get_dependency_type(normalized_name)

            if dep_type == DependencyType.CORE:
                core_reqs.append(resolution.constraint)
            elif dep_type == DependencyType.RUNTIME:
                runtime_reqs.append(resolution.constraint)
            elif dep_type == DependencyType.FRAMEWORK:
                framework_reqs.append(resolution.constraint)
            elif dep_type == DependencyType.OPTIONAL:
                optional_reqs.append(resolution.constraint)
            else:
                user_only_reqs.append(resolution.constraint)

        # Write sections
        if include_comments and core_reqs:
            lines.append("# Core Dependencies")
            lines.append("# -----------------")
        lines.extend(sorted(core_reqs))
        if core_reqs:
            lines.append("")

        if include_comments and runtime_reqs:
            lines.append("# Runtime Dependencies")
            lines.append("# --------------------")
        lines.extend(sorted(runtime_reqs))
        if runtime_reqs:
            lines.append("")

        if include_comments and framework_reqs:
            lines.append(f"# {self.framework.title()} Framework")
            lines.append("# " + "-" * (len(self.framework) + 10))
        lines.extend(sorted(framework_reqs))
        if framework_reqs:
            lines.append("")

        if include_comments and optional_reqs:
            lines.append("# Observability & Telemetry")
            lines.append("# -------------------------")
        lines.extend(sorted(optional_reqs))
        if optional_reqs:
            lines.append("")

        if include_comments and user_only_reqs:
            lines.append("# User Dependencies")
            lines.append("# -----------------")
        lines.extend(sorted(user_only_reqs))
        if user_only_reqs:
            lines.append("")

        return "\n".join(lines)


def merge_dependencies(
    framework: str = "custom",
    user_requirements_file: Optional[Path] = None,
    extra_dependencies: Optional[List[str]] = None,
    observability: Optional[Dict[str, bool]] = None,
    has_safety_policies: bool = False,
) -> MergeResult:
    """
    Convenience function to merge dependencies.

    Args:
        framework: Agent framework
        user_requirements_file: Path to user's requirements.txt
        extra_dependencies: Additional dependencies from Dockfile.yaml
        observability: Dict of enabled observability features
        has_safety_policies: Whether safety policies are enabled

    Returns:
        MergeResult with merged requirements and details
    """
    merger = DependencyMerger(
        framework=framework,
        observability=observability,
        has_safety_policies=has_safety_policies,
    )
    return merger.merge(
        user_requirements_file=user_requirements_file,
        extra_dependencies=extra_dependencies,
    )
