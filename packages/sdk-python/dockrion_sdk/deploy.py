"""
Dockrion Deployment Module
==========================

Provides deployment functionality for Dockrion agents:
- Local development with hot reload
- Docker image building
- Runtime generation

Uses the template system for generating all deployment artifacts.
"""

import subprocess
import sys
import shutil
import time
import socket
from pathlib import Path
from typing import Dict, Any, Optional

from dockrion_sdk.client import load_dockspec
from dockrion_sdk.templates import (
    TemplateRenderer,
    render_runtime,
    render_dockerfile,
    render_requirements,
)
from dockrion_schema import DockSpec
from dockrion_common.errors import DockrionError
from dockrion_common.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# Constants
# ============================================================================

RUNTIME_DIR_NAME = ".dockrion_runtime"
DOCKRION_IMAGE_PREFIX = "dockrion"
LOCAL_PYPI_PORT = 8099  # Port for local PyPI server during dev builds


# ============================================================================
# Utility Functions
# ============================================================================

def _check_uv_available() -> bool:
    """
    Check if uv package manager is available.
    
    Returns:
        True if uv is available, False otherwise
    """
    try:
        subprocess.check_output(
            ["uv", "--version"],
            stderr=subprocess.STDOUT,
            text=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _check_docker_available() -> bool:
    """
    Check if Docker is available.
    
    Returns:
        True if Docker is available, False otherwise
    """
    try:
        subprocess.check_output(
            ["docker", "--version"],
            stderr=subprocess.STDOUT,
            text=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _print_uv_setup_instructions():
    """Print instructions for installing uv package manager."""
    print("\n" + "=" * 70)
    print("⚠️  UV Package Manager Not Found")
    print("=" * 70)
    print("\nDockrion uses 'uv' for fast, reliable package management.")
    print("\n📦 Quick Setup (recommended):")
    print("\n  On macOS/Linux:")
    print("    curl -LsSf https://astral.sh/uv/install.sh | sh")
    print("\n  On Windows:")
    print('    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"')
    print("\n  Using pip:")
    print("    pip install uv")
    print("\n  Using pipx:")
    print("    pipx install uv")
    print("\n📚 Learn more: https://github.com/astral-sh/uv")
    print("\n💡 Note: Docker builds will still work (uv is installed in the container)")
    print("   but local development benefits from having uv installed.")
    print("=" * 70 + "\n")


def _ensure_runtime_dir(base_path: Path = None) -> Path:
    """
    Ensure the runtime directory exists.
    
    Args:
        base_path: Base directory (defaults to current working directory)
        
    Returns:
        Path to the runtime directory
    """
    base = base_path or Path.cwd()
    runtime_dir = base / RUNTIME_DIR_NAME
    runtime_dir.mkdir(exist_ok=True)
    return runtime_dir


def _find_workspace_root(start_path: Path = None) -> Optional[Path]:
    """
    Find the workspace root containing the packages/ directory.
    
    Walks up the directory tree from start_path looking for a directory
    that contains 'packages/common-py' (indicating the Dockrion monorepo root).
    
    Args:
        start_path: Starting directory (defaults to current working directory)
        
    Returns:
        Path to workspace root, or None if not found
    """
    current = start_path or Path.cwd()
    
    # Walk up directory tree looking for packages/
    for parent in [current] + list(current.parents):
        packages_dir = parent / "packages" / "common-py"
        if packages_dir.exists():
            return parent
    
    return None


def _get_relative_agent_path(workspace_root: Path, agent_dir: Path) -> str:
    """
    Get the relative path from workspace root to agent directory.
    
    Args:
        workspace_root: The workspace root directory
        agent_dir: The agent's directory
        
    Returns:
        Relative path string (e.g., 'examples/invoice_copilot')
    """
    try:
        return str(agent_dir.relative_to(workspace_root))
    except ValueError:
        # agent_dir is not under workspace_root
        return "."


def _find_available_port(start_port: int = 8099) -> int:
    """Find an available port starting from start_port."""
    port = start_port
    while port < start_port + 100:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            port += 1
    raise DockrionError(f"Could not find available port in range {start_port}-{start_port+100}")


def _start_local_pypi_server(dist_dir: Path) -> tuple[subprocess.Popen, int]:
    """
    Start a local PyPI server serving wheels from dist_dir.
    
    Args:
        dist_dir: Directory containing wheel files
        
    Returns:
        Tuple of (server process, port)
    """
    port = _find_available_port(LOCAL_PYPI_PORT)
    
    # Start pypiserver
    cmd = [
        sys.executable, "-m", "pypiserver", 
        "run",
        "-p", str(port),
        str(dist_dir)
    ]
    
    logger.info(f"Starting local PyPI server on port {port}...")
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect(('127.0.0.1', port))
                logger.info(f"Local PyPI server ready on port {port}")
                return proc, port
        except (socket.error, ConnectionRefusedError):
            time.sleep(0.1)
    
    # If we get here, server didn't start
    proc.terminate()
    raise DockrionError("Failed to start local PyPI server")


def _stop_local_pypi_server(proc: subprocess.Popen):
    """Stop the local PyPI server."""
    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        logger.info("Local PyPI server stopped")


def _write_runtime_files(
    spec: DockSpec,
    runtime_dir: Path,
    renderer: Optional[TemplateRenderer] = None
) -> Dict[str, Path]:
    """
    Generate and write all runtime files using templates.
    
    Args:
        spec: Agent specification
        runtime_dir: Directory to write files to
        renderer: Optional custom template renderer
        
    Returns:
        Dictionary mapping file names to their paths
    """
    if renderer is None:
        renderer = TemplateRenderer()
    
    files = {}
    
    # Render and write main.py
    logger.info("Generating runtime code from template...")
    runtime_code = renderer.render_runtime(spec)
    main_file = runtime_dir / "main.py"
    main_file.write_text(runtime_code, encoding="utf-8")
    files["main.py"] = main_file
    logger.debug(f"Written: {main_file}")
    
    # Render and write requirements.txt
    logger.info("Generating requirements from template...")
    requirements = renderer.render_requirements(spec)
    req_file = runtime_dir / "requirements.txt"
    req_file.write_text(requirements, encoding="utf-8")
    files["requirements.txt"] = req_file
    logger.debug(f"Written: {req_file}")
    
    return files


# ============================================================================
# Main Deployment Functions
# ============================================================================

def deploy(
    dockfile_path: str,
    target: str = "local",
    tag: str = "dev",
    no_cache: bool = False,
    env_file: Optional[str] = None,
    allow_missing_secrets: bool = False,
    dev: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Deploy an agent to a target environment.
    
    V1 Implementation: Builds a Docker image locally using uv package manager
    V1.1+: Will support remote deployment via Controller
    
    Args:
        dockfile_path: Path to the Dockfile
        target: Deployment target ("local" for V1)
        tag: Docker image tag (default: "dev")
        no_cache: If True, build without Docker cache
        env_file: Optional explicit path to .env file
        allow_missing_secrets: If True, continue even if required secrets are missing
        dev: If True, use local PyPI server for Dockrion packages (development mode)
        **kwargs: Additional deployment options
        
    Returns:
        Dictionary with deployment information:
        {
            "image": str,  # Docker image name
            "status": str,  # "built" or "failed"
            "agent_name": str
        }
        
    Raises:
        DockrionError: If deployment fails
        MissingSecretError: If required secrets are missing and allow_missing_secrets=False
        
    Example:
        >>> result = deploy("Dockfile.yaml", target="local")
        >>> print(result["image"])
        dockrion/invoice-copilot:dev
    """
    # Check prerequisites
    if not _check_uv_available():
        _print_uv_setup_instructions()
        print("ℹ️  Continuing with Docker build (uv will be installed in container)...\n")
    
    if not _check_docker_available():
        raise DockrionError(
            "Docker is not available. Please install Docker to deploy agents.\n"
            "Visit: https://docs.docker.com/get-docker/"
        )
    
    # Load and validate Dockfile (with env resolution)
    logger.info(f"Loading Dockfile: {dockfile_path}")
    try:
        spec = load_dockspec(
            dockfile_path,
            env_file=env_file,
            validate_secrets=True,
            strict_secrets=not allow_missing_secrets
        )
    except Exception as e:
        raise DockrionError(f"Failed to load Dockfile: {str(e)}")
    
    logger.info(f"Agent: {spec.agent.name} ({spec.agent.framework})")
    
    # Initialize template renderer
    renderer = TemplateRenderer()
    
    # Create runtime directory and generate files
    runtime_dir = _ensure_runtime_dir()
    _write_runtime_files(spec, runtime_dir, renderer)
    
    # Build Docker image
    image = f"{DOCKRION_IMAGE_PREFIX}/{spec.agent.name}:{tag}"
    logger.info(f"Building Docker image: {image}")
    
    # Find workspace root for Docker build context
    agent_dir = Path.cwd()
    workspace_root = _find_workspace_root(agent_dir)
    
    if workspace_root:
        # We're in a monorepo - use workspace root as build context
        relative_agent_path = _get_relative_agent_path(workspace_root, agent_dir)
        build_context = str(workspace_root)
        logger.info(f"Using workspace root as build context: {workspace_root}")
        logger.debug(f"Agent relative path: {relative_agent_path}")
    else:
        # Standalone agent - use current directory
        relative_agent_path = "."
        build_context = "."
        logger.info("No workspace root found, using current directory as build context")
    
    # Handle development mode with local PyPI server
    pypi_server_proc = None
    local_pypi_url = None
    dev_mode = dev
    
    if dev_mode and workspace_root:
        dist_dir = workspace_root / "dist"
        if dist_dir.exists() and list(dist_dir.glob("*.whl")):
            logger.info("Development mode: Starting local PyPI server...")
            pypi_server_proc, port = _start_local_pypi_server(dist_dir)
            # Use host.docker.internal to access host from Docker (Mac/Windows)
            # For Linux, you may need to use --network=host or the host IP
            local_pypi_url = f"http://host.docker.internal:{port}/simple/"
            logger.info(f"Local PyPI URL: {local_pypi_url}")
        else:
            logger.warning(
                "Development mode requested but no wheel files found in dist/. "
                "Run 'uv build --wheel' in each package directory first. "
                "Falling back to PyPI."
            )
            dev_mode = False
    
    try:
        # Generate Dockerfile with correct paths and dev mode settings
        dockerfile_content = renderer.render_dockerfile(
            spec, 
            agent_path=relative_agent_path,
            dev_mode=dev_mode,
            local_pypi_url=local_pypi_url
        )
        
        # Build command
        build_cmd = ["docker", "build", "-t", image, "-f", "-", "."]
        if no_cache:
            build_cmd.insert(2, "--no-cache")
        
        result = subprocess.run(
            build_cmd,
            input=dockerfile_content.encode(),
            cwd=build_context,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        logger.info(f"✅ Docker image built successfully: {image}")
        
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if e.stderr else "Unknown error"
        logger.error(f"Docker build failed: {stderr}")
        raise DockrionError(
            f"Docker build failed for agent '{spec.agent.name}'.\n"
            f"Error: {stderr}"
        )
    finally:
        # Always stop the local PyPI server
        if pypi_server_proc:
            _stop_local_pypi_server(pypi_server_proc)
    
    return {
        "image": image,
        "status": "built",
        "agent_name": spec.agent.name,
        "runtime_dir": str(runtime_dir)
    }


def run_local(
    dockfile_path: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    reload: bool = False,
    env_file: Optional[str] = None
) -> subprocess.Popen:
    """
    Run an agent locally without Docker (development mode).
    
    This function:
    1. Loads the Dockfile (with env resolution)
    2. Generates a FastAPI runtime using templates
    3. Installs dependencies
    4. Starts the server with uvicorn
    
    Args:
        dockfile_path: Path to the Dockfile
        host: Override host (default from Dockfile or 0.0.0.0)
        port: Override port (default from Dockfile or 8080)
        reload: Enable hot reload for development
        env_file: Optional explicit path to .env file
        
    Returns:
        subprocess.Popen object (running server)
        
    Raises:
        DockrionError: If startup fails
        MissingSecretError: If required secrets are missing
        
    Example:
        >>> proc = run_local("Dockfile.yaml", reload=True)
        >>> # Server is now running with hot reload...
        >>> proc.terminate()  # Stop the server
    """
    # Load and validate Dockfile (with env resolution)
    logger.info(f"Loading Dockfile: {dockfile_path}")
    try:
        spec = load_dockspec(dockfile_path, env_file=env_file)
    except Exception as e:
        raise DockrionError(f"Failed to load Dockfile: {str(e)}")
    
    logger.info(f"Agent: {spec.agent.name} ({spec.agent.framework})")
    
    # Initialize template renderer
    renderer = TemplateRenderer()
    
    # Create runtime directory and generate files
    runtime_dir = _ensure_runtime_dir()
    _write_runtime_files(spec, runtime_dir, renderer)
    
    # Determine host and port
    server_host = host or (spec.expose.host if spec.expose else "0.0.0.0")
    server_port = port or (spec.expose.port if spec.expose else 8080)
    
    # Install dependencies
    logger.info("Installing dependencies...")
    use_uv = _check_uv_available()
    
    if use_uv:
        logger.info("  Using uv package manager (fast!)...")
        try:
            subprocess.check_call(
                ["uv", "pip", "install", "-r", "requirements.txt", "-q"],
                cwd=str(runtime_dir),
                stdout=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError as e:
            raise DockrionError(f"Failed to install dependencies with uv: {str(e)}")
    else:
        _print_uv_setup_instructions()
        logger.info("  Using pip (consider installing uv for faster installs)...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
                cwd=str(runtime_dir),
                stdout=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError as e:
            raise DockrionError(f"Failed to install dependencies with pip: {str(e)}")
    
    # Build uvicorn command
    uvicorn_cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", str(server_host),
        "--port", str(server_port)
    ]
    
    if reload:
        uvicorn_cmd.append("--reload")
    
    # Start the server
    logger.info(f"🚀 Starting agent server at http://{server_host}:{server_port}")
    
    try:
        proc = subprocess.Popen(
            uvicorn_cmd,
            cwd=str(runtime_dir)
        )
        return proc
    except Exception as e:
        raise DockrionError(f"Failed to start server: {str(e)}")


def generate_runtime(
    dockfile_path: str,
    output_dir: Optional[str] = None,
    include_dockerfile: bool = True,
    env_file: Optional[str] = None
) -> Dict[str, Path]:
    """
    Generate runtime files without building or running.
    
    Useful for inspection, customization, or CI/CD pipelines.
    
    Args:
        dockfile_path: Path to the Dockfile
        output_dir: Output directory (default: .dockrion_runtime)
        include_dockerfile: Include Dockerfile in output
        env_file: Optional explicit path to .env file
        
    Returns:
        Dictionary mapping file names to their paths
        
    Example:
        >>> files = generate_runtime("Dockfile.yaml", output_dir="./build")
        >>> print(files["main.py"])
        PosixPath('build/main.py')
    """
    # Load spec (with env resolution, non-strict for generation)
    logger.info(f"Loading Dockfile: {dockfile_path}")
    try:
        spec = load_dockspec(dockfile_path, env_file=env_file, strict_secrets=False)
    except Exception as e:
        raise DockrionError(f"Failed to load Dockfile: {str(e)}")
    
    # Determine output directory
    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
    else:
        out_path = _ensure_runtime_dir()
    
    # Initialize renderer
    renderer = TemplateRenderer()
    
    # Generate files
    files = _write_runtime_files(spec, out_path, renderer)
    
    # Optionally include Dockerfile
    if include_dockerfile:
        dockerfile_content = renderer.render_dockerfile(spec)
        dockerfile_path = out_path / "Dockerfile"
        dockerfile_path.write_text(dockerfile_content, encoding="utf-8")
        files["Dockerfile"] = dockerfile_path
        logger.debug(f"Written: {dockerfile_path}")
    
    logger.info(f"✅ Generated {len(files)} files in {out_path}")
    
    return files


def clean_runtime(base_path: Path = None) -> bool:
    """
    Clean up the runtime directory.
    
    Args:
        base_path: Base directory (defaults to cwd)
        
    Returns:
        True if directory was removed, False if it didn't exist
    """
    base = base_path or Path.cwd()
    runtime_dir = base / RUNTIME_DIR_NAME
    
    if runtime_dir.exists():
        shutil.rmtree(runtime_dir)
        logger.info(f"Removed runtime directory: {runtime_dir}")
        return True
    
    return False


# ============================================================================
# Docker Helper Functions
# ============================================================================

def docker_run(
    image: str,
    port: int = 8080,
    env_vars: Optional[Dict[str, str]] = None,
    detach: bool = True,
    name: Optional[str] = None
) -> str:
    """
    Run a built Docker image.
    
    Args:
        image: Docker image name
        port: Port to expose
        env_vars: Environment variables to pass
        detach: Run in detached mode
        name: Container name
        
    Returns:
        Container ID
        
    Raises:
        DockrionError: If docker run fails
    """
    cmd = ["docker", "run"]
    
    if detach:
        cmd.append("-d")
    
    if name:
        cmd.extend(["--name", name])
    
    cmd.extend(["-p", f"{port}:{port}"])
    
    if env_vars:
        for key, value in env_vars.items():
            cmd.extend(["-e", f"{key}={value}"])
    
    cmd.append(image)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        container_id = result.stdout.strip()
        logger.info(f"Container started: {container_id[:12]}")
        return container_id
        
    except subprocess.CalledProcessError as e:
        raise DockrionError(f"Failed to run container: {e.stderr}")


def docker_stop(container: str) -> bool:
    """
    Stop a running Docker container.
    
    Args:
        container: Container ID or name
        
    Returns:
        True if stopped successfully
    """
    try:
        subprocess.run(
            ["docker", "stop", container],
            capture_output=True,
            check=True
        )
        logger.info(f"Container stopped: {container}")
        return True
    except subprocess.CalledProcessError:
        logger.warning(f"Failed to stop container: {container}")
        return False


def docker_logs(
    container: str,
    follow: bool = False,
    tail: Optional[int] = None
) -> str:
    """
    Get logs from a Docker container.
    
    Args:
        container: Container ID or name
        follow: Follow log output
        tail: Number of lines to show from end
        
    Returns:
        Log output as string
    """
    cmd = ["docker", "logs"]
    
    if follow:
        cmd.append("-f")
    
    if tail:
        cmd.extend(["--tail", str(tail)])
    
    cmd.append(container)
    
    if follow:
        # For follow mode, use Popen
        proc = subprocess.Popen(cmd)
        return ""
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout + result.stderr
