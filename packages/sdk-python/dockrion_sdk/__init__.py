"""Dockrion SDK - Python SDK for deploying and managing AI agents.

This package provides tools for:
- Loading and validating Dockfiles
- Deploying agents locally or via Docker
- Template-based runtime generation
- Invoking agents programmatically
- Managing agent logs and monitoring

Example:
    >>> from dockrion_sdk import load_dockspec, deploy, run_local
    >>> spec = load_dockspec("Dockfile.yaml")
    >>> result = deploy("Dockfile.yaml")  # Build Docker image
    >>> proc = run_local("Dockfile.yaml")  # Run locally for development

Package Structure:
    dockrion_sdk/
    ├── core/           - Core SDK functionality (loader, invoker, validate)
    ├── deployment/     - Deployment operations (docker, runtime generation)
    ├── remote/         - Remote service clients (controller, logs)
    ├── templates/      - Template rendering system
    └── utils/          - Shared utilities (workspace, package manager)
"""

# Core loading and invocation
from .core import load_dockspec, expand_env_vars, invoke_local, validate_dockspec, validate

# Remote services
from .remote import ControllerClient, get_local_logs, tail_build_logs, stream_agent_logs

# Deployment
from .deployment import (
    deploy,
    run_local,
    generate_runtime,
    clean_runtime,
    docker_run,
    docker_stop,
    docker_logs,
    docker_build,
    check_docker_available,
    ensure_runtime_dir,
    write_runtime_files,
    start_local_pypi_server,
    stop_local_pypi_server,
    DOCKRION_IMAGE_PREFIX,
    RUNTIME_DIR_NAME,
)

# Templates
from .templates import (
    TemplateRenderer,
    TemplateContext,
    render_runtime,
    render_dockerfile,
    render_requirements,
    get_renderer,
)

# Utilities
from .utils import (
    find_workspace_root,
    get_relative_agent_path,
    check_uv_available,
    print_uv_setup_instructions,
    install_requirements,
)

__version__ = "0.1.0"

__all__ = [
    # Core functions
    "load_dockspec",
    "invoke_local",
    "expand_env_vars",
    
    # Validation
    "validate_dockspec",
    "validate",
    
    # Deployment
    "deploy",
    "run_local",
    "generate_runtime",
    "clean_runtime",
    "DOCKRION_IMAGE_PREFIX",
    "RUNTIME_DIR_NAME",
    
    # Docker operations
    "docker_run",
    "docker_stop",
    "docker_logs",
    "docker_build",
    "check_docker_available",
    
    # Templates
    "TemplateRenderer",
    "TemplateContext",
    "render_runtime",
    "render_dockerfile",
    "render_requirements",
    "get_renderer",
    
    # Logs
    "get_local_logs",
    "tail_build_logs",
    "stream_agent_logs",
    
    # Remote client
    "ControllerClient",
    
    # Workspace utilities
    "find_workspace_root",
    "get_relative_agent_path",
    
    # Package manager utilities
    "check_uv_available",
    "print_uv_setup_instructions",
    "install_requirements",
    
    # Runtime generation utilities
    "ensure_runtime_dir",
    "write_runtime_files",
    
    # PyPI server utilities
    "start_local_pypi_server",
    "stop_local_pypi_server",
]
