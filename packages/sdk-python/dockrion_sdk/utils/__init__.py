"""
Utilities Module
================

Shared utilities for the Dockrion SDK:
- Workspace/monorepo detection
- Package manager utilities (uv/pip)
"""

from .workspace import find_workspace_root, get_relative_agent_path
from .package_manager import (
    check_uv_available,
    print_uv_setup_instructions,
    install_requirements,
)

__all__ = [
    "find_workspace_root",
    "get_relative_agent_path",
    "check_uv_available",
    "print_uv_setup_instructions",
    "install_requirements",
]

