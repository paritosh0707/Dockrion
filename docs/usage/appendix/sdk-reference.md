# SDK Reference

[Home](../../README.md) > [Appendix](README.md)

Complete API reference for the `dockrion_sdk` Python package (`v0.1.0`).

## Core Functions

### `load_dockspec(path, env_file=None, validate_secrets=True, strict_secrets=True)`

Load, parse, and validate a Dockfile.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | — | Path to Dockfile YAML |
| `env_file` | `str` | `None` | Optional explicit env file path |
| `validate_secrets` | `bool` | `True` | Whether to check secret availability |
| `strict_secrets` | `bool` | `True` | Raise on missing required secrets |

**Returns:** `DockSpec` — validated Pydantic model

**Process:** Loads env files → reads YAML → `expand_env_vars()` → `DockSpec.model_validate()` → optionally validates secrets.

### `validate_dockspec(path)`

Validate a Dockfile without loading the agent.

**Returns:** `dict` with keys:
- `valid` (bool)
- `errors` (list)
- `warnings` (list)
- `spec` (DockSpec or None)
- `message` (str)

Checks entrypoint/handler path format, framework support, timeout warnings.

### `validate(path)`

Legacy wrapper. Calls `validate_dockspec()`. Raises `ValidationError` if invalid; returns `{"valid": True}` on success.

### `invoke_local(dockfile_path, payload, env_file=None)`

Invoke the agent locally without an HTTP server.

| Parameter | Type | Description |
|-----------|------|-------------|
| `dockfile_path` | `str` | Path to Dockfile |
| `payload` | `dict` | Input data |
| `env_file` | `str` | Optional env file |

**Returns:** `dict` — agent output

**Process:** Loads spec → adds project to `sys.path` → gets adapter → loads handler/entrypoint → `adapter.invoke(payload)`.

### `expand_env_vars(data)`

Recursively expand `${VAR}` and `${VAR:-default}` in a data structure.

**Returns:** Expanded data (same structure, strings replaced)

**Raises:** `ValidationError` if a required variable (no default) is missing.

## Deployment Functions

### `deploy(dockfile_path, target="local", tag="dev", no_cache=False, env_file=None, allow_missing_secrets=False, use_local_dockrion_packages=False, **kwargs)`

Full deployment pipeline: load spec → generate runtime → build Docker image.

**Returns:** `dict` with `image`, `status`, `agent_name`, `runtime_dir`

### `run_local(dockfile_path, host=None, port=None, reload=False, env_file=None)`

Start a local uvicorn dev server.

**Returns:** `subprocess.Popen` — the uvicorn process

**Process:** Generates runtime → installs requirements → starts `uvicorn main:app`.

### `generate_runtime(dockfile_path, output_dir=None, include_dockerfile=True, env_file=None)`

Generate runtime files without building.

**Returns:** `dict[str, Path]` mapping logical names to file paths

### `clean_runtime(base_path=None)`

Remove the `.dockrion_runtime` directory.

**Returns:** `bool` — whether cleanup succeeded

## Docker Helpers

### `docker_build(image, dockerfile_content, build_context, no_cache=False)`

Build a Docker image from Dockerfile content passed via stdin.

### `docker_run(image, port=8080, env_vars=None, detach=True, name=None)`

Run a Docker container. Returns container ID.

### `docker_stop(container)`

Stop a running container. Returns `bool`.

### `docker_logs(container, follow=False, tail=None)`

Get container logs. If `follow=True`, starts a background process and returns `""`.

### `check_docker_available()`

Check if Docker is installed and running. Returns `bool`.

## Template System

### `TemplateRenderer`

Jinja2 renderer for generating runtime files.

```python
renderer = TemplateRenderer(template_dirs=None, strict_mode=True)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `render(template_name, context)` | Render any template with a context dict |
| `render_runtime(spec, extra_context=None, project_root=None)` | Generate `main.py` |
| `render_dockerfile(spec, extra_context=None, agent_path=".", local_pypi_url=None, project_root=None)` | Generate `Dockerfile` |
| `render_requirements(spec, extra_context=None, project_root=None, use_merged=True)` | Generate `requirements.txt` |
| `render_all(spec, ...)` | Generate all three files, returns `dict[str, str]` |
| `list_templates()` | List available `.j2` template files |

### `TemplateContext`

Builds the full Jinja2 context from a DockSpec.

```python
ctx = TemplateContext(spec, project_root=None)
context = ctx.build(extra_context=None)
```

Uses `BuildResolver` for build context and `DependencyMerger` for requirements.

### Module-level Helpers

| Function | Description |
|----------|-------------|
| `get_renderer()` | Get or create the singleton `TemplateRenderer` |
| `render_runtime(spec, **kwargs)` | Shortcut using singleton renderer |
| `render_dockerfile(spec, **kwargs)` | Shortcut |
| `render_requirements(spec, **kwargs)` | Shortcut |

## Runtime Generation

### `ensure_runtime_dir(base_path=None)`

Create `.dockrion_runtime/` directory. Returns `Path`.

### `write_runtime_files(spec, runtime_dir, renderer=None)`

Write `main.py` and `requirements.txt` to the runtime directory.

**Returns:** `dict[str, Path]` — paths to generated files

## Logging and Tailing

| Function | Description |
|----------|-------------|
| `get_local_logs(agent_name, lines=100)` | Read last N lines from `.dockrion_runtime/logs/{agent}.log` |
| `stream_agent_logs(agent_name, follow=False)` | Yield log lines (follow mode is a stub in v1) |
| `tail_build_logs(build_id)` | Placeholder generator for build log streaming |

## Schema Utilities

These are in `dockrion_schema` but commonly used:

| Function | Description |
|----------|-------------|
| `generate_json_schema()` | Returns `DockSpec.model_json_schema()` |
| `write_json_schema(output_path)` | Writes JSON Schema file |
| `get_schema_version()` | Returns `"1.0"` |

## ControllerClient

> **Status: Stub.** All methods return placeholder data.

```python
client = ControllerClient(base_url="http://localhost:8000")
```

| Method | Returns |
|--------|---------|
| `status()` | `{"ok": True, "ts": ...}` |
| `health()` | `{"status": "healthy", ...}` |
| `deploy(dockfile_path, target, **kwargs)` | Not implemented placeholder |
| `list_agents()` | Empty list placeholder |

## Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `DOCKRION_IMAGE_PREFIX` | `"dockrion"` | Docker image name prefix |
| `RUNTIME_DIR_NAME` | `".dockrion_runtime"` | Runtime output directory name |

## Utility Functions

| Function | Description |
|----------|-------------|
| `find_workspace_root(start_path=None)` | Walk up directories looking for `packages/common-py` |
| `check_uv_available()` | Check if `uv` package manager is installed |
| `install_requirements(requirements_dir, use_uv=True)` | Install from `requirements.txt` |

> **Source:** `packages/sdk-python/dockrion_sdk/`

---

**Next:** [Adapters Reference →](adapters-reference.md)
