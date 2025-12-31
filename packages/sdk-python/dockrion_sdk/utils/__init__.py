"""
Utilities Module
================

Shared utilities for the Dockrion SDK:
- Workspace/monorepo detection
- Package manager utilities (uv/pip)
- PyProject.toml reading (single source of truth for versions)
"""

from .package_manager import (
    check_uv_available,
    install_requirements,
    print_uv_setup_instructions,
)
from .workspace import (
    clear_pyproject_cache,
    find_workspace_root,
    get_core_dependencies_from_pyproject,
    get_dockrion_pyproject,
    get_dockrion_version,
    get_framework_dependencies_from_pyproject,
    get_relative_agent_path,
    get_runtime_dependencies_from_pyproject,
    get_runtime_pyproject,
)

__all__ = [
    # Workspace detection
    "find_workspace_root",
    "get_relative_agent_path",
    # Package manager
    "check_uv_available",
    "print_uv_setup_instructions",
    "install_requirements",
    # PyProject.toml utilities (single source of truth)
    "get_dockrion_pyproject",
    "get_runtime_pyproject",
    "get_dockrion_version",
    "get_core_dependencies_from_pyproject",
    "get_runtime_dependencies_from_pyproject",
    "get_framework_dependencies_from_pyproject",
    "clear_pyproject_cache",
]
