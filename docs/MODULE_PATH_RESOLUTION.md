# Module Path Resolution - Implementation Summary

## Problem

When running `dockrion test`, users encountered the error:
```
No module named 'app'
```

This occurred because Python couldn't find the agent's module when trying to import handlers/entrypoints like `app.service:process_invoice`.

## Root Cause

- **`dockrion run`** worked because the generated runtime template (`main.py.j2`) included smart path resolution logic that automatically found and added the module's directory to `sys.path`
- **`dockrion test`** failed because the SDK's `invoke_local()` function didn't have any path resolution logic

## Solution

We modularized the path resolution logic into a reusable utility in `dockrion_common` and updated both the SDK and runtime template to use it.

## Changes Made

### 1. New Module: `dockrion_common/path_utils.py`

Created a new utility module with three functions:

#### `resolve_module_path(module_path, base_dir, max_levels=5)`
Walks up the directory tree to find where a module's top-level package exists.

**Example:**
```python
# For "app.service:handler" starting from /project/examples/agent1/
# If "app" exists at /project/examples/agent1/app/, returns that path
resolve_module_path("app.service:handler", Path("/project/examples/agent1"))
# Returns: Path("/project/examples/agent1")
```

#### `add_to_python_path(path)`
Adds a directory to Python's `sys.path` if not already present.

**Example:**
```python
add_to_python_path(Path("/my/project"))
# Returns: True (added) or False (already in sys.path)
```

#### `setup_module_path(module_path, base_dir, max_levels=5)`
Convenience function that combines the above two - finds the module and adds it to `sys.path`.

**Example:**
```python
# Setup path for importing "app.service:handler"
project_root = setup_module_path(
    "app.service:handler",
    Path("/project/examples/agent1")
)
# Now you can: import app.service
```

### 2. Updated: `dockrion_sdk/client.py`

**Before (no path resolution):**
```python
def invoke_local(dockfile_path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    spec = load_dockspec(dockfile_path)
    # ... directly tried to load agent, which failed
```

**After (uses shared utility):**
```python
def invoke_local(dockfile_path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    from pathlib import Path
    from dockrion_common import setup_module_path
    
    spec = load_dockspec(dockfile_path)
    
    # Setup Python path for agent module imports
    module_path = spec.agent.handler or spec.agent.entrypoint
    if module_path:
        dockfile_dir = Path(dockfile_path).resolve().parent
        setup_module_path(module_path, dockfile_dir)
    
    # ... rest of the function
```

### 3. Updated: `templates/runtime-fastapi/main.py.j2`

**Before (inline logic):**
```python
# Add project root to Python path for agent module imports
current_dir = Path(__file__).parent
project_root = current_dir.parent

handler_module = "{{ agent.handler }}".split(":")[0]
top_level_module = handler_module.split(".")[0]

# Walk up the directory tree...
max_levels = 5
for _ in range(max_levels):
    if (project_root / top_level_module).exists():
        break
    project_root = project_root.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
```

**After (uses shared utility):**
```python
# Add project root to Python path for agent module imports
from dockrion_common import setup_module_path

current_dir = Path(__file__).parent
module_path = "{{ agent.handler }}"  # or agent.entrypoint

# Setup Python path to find the agent module
project_root = setup_module_path(module_path, current_dir.parent)
```

### 4. Updated: `dockrion_common/__init__.py`

Added exports for the new path utilities:
```python
from .path_utils import (
    resolve_module_path,
    add_to_python_path,
    setup_module_path,
)
```

### 5. New Tests: `tests/test_path_utils.py`

Created comprehensive tests covering:
- Module in base directory
- Module in parent directory
- Module multiple levels up
- Module not found (returns base dir)
- Nested module paths
- Max levels limit
- Adding to sys.path
- Real-world scenarios (invoice_copilot structure)

## Benefits

1. **DRY Principle** - Single source of truth for path resolution logic
2. **Consistency** - `dockrion run` and `dockrion test` now use the same logic
3. **Maintainability** - Changes to path resolution only need to be made in one place
4. **Testability** - Logic is isolated and thoroughly tested
5. **Reusability** - Other packages can use these utilities if needed

## How It Works

1. **Extract module name**: From `app.service:handler`, extract `app` (top-level module)
2. **Walk up directory tree**: Starting from the Dockfile's directory, look for a directory named `app`
3. **Find the module**: Stop when `app/` directory is found or max levels reached
4. **Add to sys.path**: Add the directory containing `app/` to Python's import path
5. **Import succeeds**: Python can now `import app.service`

## Example Flow

For the invoice_copilot example:

```
/Users/user/Dockrion/
└── examples/
    └── invoice_copilot/
        ├── Dockfile.yaml          # handler: app.service:process_invoice
        └── app/
            ├── __init__.py
            └── service.py         # def process_invoice(...)
```

When running `dockrion test`:
1. Load `Dockfile.yaml` from `examples/invoice_copilot/`
2. Extract handler: `app.service:process_invoice`
3. Extract top-level module: `app`
4. Start from: `examples/invoice_copilot/`
5. Check if `examples/invoice_copilot/app/` exists → ✅ Yes!
6. Add `examples/invoice_copilot/` to `sys.path`
7. Import `app.service` → ✅ Success!

## Testing

Verified working with:
```bash
cd examples/invoice_copilot
dockrion test --payload '{"document_text": "test", ...}'
# ✅ Agent invocation successful
```

## Files Modified

- ✅ `packages/common-py/dockrion_common/path_utils.py` (new)
- ✅ `packages/common-py/dockrion_common/__init__.py` (updated exports)
- ✅ `packages/common-py/tests/test_path_utils.py` (new)
- ✅ `packages/sdk-python/dockrion_sdk/client.py` (refactored to use utility)
- ✅ `templates/runtime-fastapi/main.py.j2` (refactored to use utility)

## Version

This change is part of `dockrion-common` v0.1.1+

