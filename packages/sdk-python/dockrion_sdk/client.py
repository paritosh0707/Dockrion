import os
import re
import time
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dockrion_schema.dockfile_v1 import DockSpec
from dockrion_common.errors import ValidationError, DockrionError, MissingSecretError
from dockrion_common import (
    load_env_files,
    resolve_secrets,
    validate_secrets as validate_secrets_func,
    inject_env,
    get_env_summary,
    get_logger,
)
from dockrion_adapters import get_adapter

logger = get_logger(__name__)


def expand_env_vars(data: Any) -> Any:
    """Recursively expand ${VAR} and ${VAR:-default} in dict/list values.
    
    Args:
        data: Dictionary, list, string, or other value to process
        
    Returns:
        Data with environment variables expanded
        
    Raises:
        ValidationError: If required environment variable is missing
        
    Examples:
        >>> os.environ["FOO"] = "bar"
        >>> expand_env_vars({"key": "${FOO}"})
        {"key": "bar"}
        >>> expand_env_vars({"key": "${MISSING:-default}"})
        {"key": "default"}
    """
    if isinstance(data, dict):
        return {key: expand_env_vars(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [expand_env_vars(item) for item in data]
    elif isinstance(data, str):
        # Pattern: ${VAR} or ${VAR:-default}
        pattern = r'\$\{([^}:]+)(?::-)?(([^}]*))?\}'
        
        def replacer(match):
            var_name = match.group(1)
            # Group 2 may be empty string or None when no default is provided
            default_value = match.group(2) if match.group(2) else None
            
            if var_name in os.environ:
                return os.environ[var_name]
            elif default_value:
                return default_value
            else:
                raise ValidationError(
                    f"Environment variable '${{{var_name}}}' is required but not set. "
                    f"Either set the variable or use ${{VAR:-default}} syntax for a default value."
                )
        
        return re.sub(pattern, replacer, data)
    else:
        return data


def load_dockspec(
    path: str,
    env_file: Optional[str] = None,
    validate_secrets: bool = True,
    strict_secrets: bool = True
) -> DockSpec:
    """Load and validate a Dockfile from the filesystem with environment resolution.
    
    This function:
    1. Loads environment variables from .env and env.yaml files
    2. Checks if the Dockfile exists
    3. Reads and parses the YAML file
    4. Expands environment variables (${VAR} syntax)
    5. Validates the structure using DockSpec schema
    6. Optionally validates declared secrets
    
    Args:
        path: Path to the Dockfile (typically "Dockfile.yaml")
        env_file: Optional explicit path to .env file (overrides auto-detection)
        validate_secrets: Whether to validate declared secrets (default: True)
        strict_secrets: If True, raise MissingSecretError for missing required secrets
                       If False, only log warnings (default: True)
        
    Returns:
        Validated DockSpec object
        
    Raises:
        ValidationError: If file not found, invalid YAML, or schema validation fails
        MissingSecretError: If strict_secrets=True and required secrets are missing
        
    Example:
        >>> spec = load_dockspec("Dockfile.yaml")
        >>> print(spec.agent.name)
        invoice-copilot
        
        >>> spec = load_dockspec("Dockfile.yaml", env_file="./secrets/.env.local")
        >>> print(spec.agent.name)
        invoice-copilot
    """
    file_path = Path(path).resolve()
    project_root = file_path.parent
    
    # 1. Load environment files BEFORE parsing Dockfile
    # This ensures ${VAR} expansion has access to all env vars
    try:
        loaded_env = load_env_files(project_root, env_file)
        if loaded_env:
            inject_env(loaded_env)
            logger.info(f"Loaded {len(loaded_env)} environment variables")
    except Exception as e:
        logger.warning(f"Failed to load environment files: {e}")
        loaded_env = {}
    
    # 2. Check if file exists
    if not file_path.exists():
        raise ValidationError(
            f"Dockfile not found: {path}\n"
            f"Make sure the file exists and the path is correct."
        )
    
    # 3. Read and parse YAML
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ValidationError(
            f"Invalid YAML in Dockfile: {path}\n"
            f"Error: {str(e)}\n"
            f"Please check the YAML syntax."
        )
    except Exception as e:
        raise ValidationError(
            f"Failed to read Dockfile: {path}\n"
            f"Error: {str(e)}"
        )
    
    if data is None:
        raise ValidationError(
            f"Dockfile is empty: {path}\n"
            f"Please add valid configuration."
        )
    
    # 4. Expand environment variables
    try:
        data = expand_env_vars(data)
    except ValidationError:
        # Re-raise ValidationError as-is
        raise
    except Exception as e:
        raise ValidationError(
            f"Failed to expand environment variables in Dockfile: {path}\n"
            f"Error: {str(e)}"
        )
    
    # 5. Validate against schema
    try:
        spec = DockSpec.model_validate(data)
    except Exception as e:
        raise ValidationError(
            f"Invalid Dockfile structure: {path}\n"
            f"Error: {str(e)}\n"
            f"Please check the Dockfile format against the schema."
        )
    
    # 6. Validate secrets if declared and validation is enabled
    if validate_secrets and spec.secrets:
        # Resolve secrets with full priority chain
        resolved = resolve_secrets(spec.secrets, loaded_env)
        
        # Validate and collect warnings
        warnings = validate_secrets_func(spec.secrets, resolved, strict=strict_secrets)
        for warning in warnings:
            logger.warning(warning)
    
    return spec


def invoke_local(
    dockfile_path: str,
    payload: Dict[str, Any],
    env_file: Optional[str] = None
) -> Dict[str, Any]:
    """Invoke an agent locally without starting a server.
    
    This is useful for:
    - Testing agents during development
    - Running one-off agent invocations
    - Integration testing
    
    Args:
        dockfile_path: Path to the Dockfile
        payload: Input data to pass to the agent
        env_file: Optional explicit path to .env file
        
    Returns:
        Agent response as a dictionary
        
    Raises:
        ValidationError: If Dockfile is invalid
        DockrionError: If agent loading or invocation fails
        MissingSecretError: If required secrets are missing
        
    Example:
        >>> result = invoke_local("Dockfile.yaml", {
        ...     "document_text": "INVOICE #123...",
        ...     "currency_hint": "USD"
        ... })
        >>> print(result["vendor"])
        Acme Corp
    """
    from pathlib import Path
    from dockrion_common import setup_module_path
    
    # Load and validate Dockfile (with env resolution)
    spec = load_dockspec(dockfile_path, env_file=env_file)
    
    # Setup Python path for agent module imports
    # This finds and adds the directory containing the agent's module to sys.path
    module_path = spec.agent.handler or spec.agent.entrypoint
    if module_path:
        dockfile_dir = Path(dockfile_path).resolve().parent
        setup_module_path(module_path, dockfile_dir)
    
    # Get the appropriate adapter for the framework
    try:
        adapter = get_adapter(spec.agent.framework)
    except Exception as e:
        raise DockrionError(
            f"Failed to get adapter for framework '{spec.agent.framework}': {str(e)}"
        )
    
    # Load the agent (entrypoint or handler mode)
    try:
        if spec.agent.handler:
            # Handler mode: load direct callable
            adapter.load(spec.agent.handler)
        elif spec.agent.entrypoint:
            # Entrypoint mode: load framework agent factory
            adapter.load(spec.agent.entrypoint)
        else:
            raise DockrionError("Agent must have either 'handler' or 'entrypoint' specified")
    except Exception as e:
        entrypoint_or_handler = spec.agent.handler or spec.agent.entrypoint
        raise DockrionError(
            f"Failed to load agent from '{entrypoint_or_handler}': {str(e)}\n"
            f"Make sure the module path is correct and the agent is properly implemented."
        )
    
    # Invoke the agent
    try:
        result = adapter.invoke(payload)
        return result
    except Exception as e:
        raise DockrionError(
            f"Agent invocation failed: {str(e)}\n"
            f"Check the agent implementation and input payload."
        )


# In v1 this is a placeholder; v1.1+ will talk to Controller service.
class ControllerClient:
    """Client for interacting with the dockrion Controller service.
    
    Note: V1 implementation is a placeholder. V1.1+ will provide full
    functionality for remote deployments, agent management, and monitoring.
    """
    
    def __init__(self, base_url: str | None = None):
        """Initialize controller client.
        
        Args:
            base_url: Base URL of the controller service (e.g., "http://localhost:8000")
        """
        self.base_url = base_url or "http://localhost:8000"

    def status(self) -> Dict[str, Any]:
        """Get controller status.
        
        Returns:
            Status information including timestamp
        """
        return {"ok": True, "ts": time.time()}
