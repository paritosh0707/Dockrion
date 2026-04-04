# 2.8 build config

[Home](../../README.md) > [The Dockfile](README.md)

The `build` section controls what goes into the Docker image when you run `dockrion build`.

## Fields

### BuildConfig (root `build` key)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `include` | `BuildIncludeConfig` | `null` | Additional files, directories, and patterns to include |
| `exclude` | `list[str]` | `[]` | Glob patterns to exclude from the build context |
| `auto_detect_imports` | `bool` | `false` | Parse your Python entry file's AST to find local imports and include them automatically |

### BuildIncludeConfig (nested `build.include`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `directories` | `list[str]` | `[]` | Directory paths to copy into the image |
| `files` | `list[str]` | `[]` | Individual file paths to copy |
| `patterns` | `list[str]` | `[]` | Glob patterns (e.g., `*.py`, `data/*.json`) |

All list entries must be non-empty strings after trimming whitespace.

## How Build Context Works

When `dockrion build` runs:

1. The `BuildResolver` reads your Dockfile's `agent.entrypoint` or `agent.handler` to identify the agent's module
2. If `auto_detect_imports` is `true`, it parses the entry file's AST to discover local imports and adds their directories/files
3. Explicit `include.directories`, `include.files`, and `include.patterns` are resolved via glob matching
4. `exclude` patterns filter out unwanted files (applied after includes)
5. The resolved set of files is copied into the `.dockrion_runtime/` directory for Docker build context

## Examples

### Minimal (auto-detect)

```yaml
build:
  auto_detect_imports: true
```

Dockrion scans your entry file, finds local imports, and includes their source files. No manual configuration needed for simple projects.

### Explicit includes

```yaml
build:
  include:
    directories:
      - app
      - lib
    files:
      - config.json
      - prompts/system.txt
    patterns:
      - "data/*.csv"
  exclude:
    - "__pycache__"
    - "*.pyc"
    - ".git"
```

### Combined approach

```yaml
build:
  auto_detect_imports: true
  include:
    directories:
      - data
    files:
      - .env.production
  exclude:
    - "tests"
    - "*.test.py"
```

Auto-detect finds the code dependencies, explicit includes add data files that AST analysis can't discover, and excludes remove test files from the image.

## What Gets Generated

The build process creates a `.dockrion_runtime/` directory containing:

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app entry point (rendered from Jinja2 template) |
| `requirements.txt` | Merged dependencies (your requirements + Dockrion's) |
| `Dockerfile` | Multi-step Docker build instructions |
| Agent source files | Copied based on build resolution |

See [5.6 Docker Build & Deployment](../05-guides-and-recipes/docker-build-and-deployment.md) for the full build workflow.

> **Source:** `BuildConfig`, `BuildIncludeConfig` in `packages/schema/dockrion_schema/dockfile_v1.py`; `BuildResolver` in `packages/sdk-python/dockrion_sdk/build/`

---

**Previous:** [2.7 observability](observability.md) | **Next:** [2.9 env substitution →](env-substitution.md)
