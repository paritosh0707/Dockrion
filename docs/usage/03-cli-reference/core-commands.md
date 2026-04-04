# 3.1 Core Commands

[Home](../../README.md) > [CLI Reference](README.md)

The five commands you'll use most: scaffold, validate, run, build, and test.

---

## `dockrion init`

Scaffold a new Dockfile with sensible defaults.

```bash
dockrion init <name> [options]
```

| Argument/Option | Flag | Type | Default | Description |
|-----------------|------|------|---------|-------------|
| `name` | *(positional)* | `str` | **required** | Agent name (lowercase with hyphens) |
| `--output` | `-o` | `str` | `Dockfile.yaml` | Output file path |
| `--force` | `-f` | `bool` | `false` | Overwrite existing file without confirmation |
| `--framework` | `-F` | `str` | `langgraph` | Framework: `langgraph`, `langchain`, or `custom` |
| `--handler` | `-H` | `bool` | `false` | Use handler mode (no `.invoke()` needed) |
| `--auth` | `-a` | `str` | `null` | Auth mode: `none`, `api_key`, or `jwt` |
| `--cors` | | `bool` | `false` | Enable CORS for browser access |
| `--secrets` | | `bool` | `false` | Add secrets section (includes `OPENAI_API_KEY` etc.) |
| `--secret-names` | | `str` | `null` | Custom secret names, comma-separated |
| `--streaming` | `-s` | `str` | `sse` | Streaming: `sse`, `websocket`, or `none` |
| `--streaming-events` | `-E` | `str` | `null` | Events preset or comma-separated list |
| `--async-runs` | `-A` | `bool` | `false` | Enable async `/runs` endpoint |
| `--streaming-backend` | | `str` | `memory` | Backend: `memory` or `redis` |
| `--observability` | `--obs` | `bool` | `false` | Add observability config |
| `--metadata` | `-m` | `bool` | `false` | Add metadata section |
| `--full` | | `bool` | `false` | Include everything: auth, secrets, cors, observability, metadata |

### Examples

```bash
# Simplest handler agent
dockrion init my-bot --handler

# LangGraph with full features
dockrion init invoice-copilot --framework langgraph --auth api_key --streaming sse --async-runs --full

# Custom output path
dockrion init my-agent -o config/agent.yaml --force
```

---

## `dockrion validate`

Validate a Dockfile without running or building.

```bash
dockrion validate [path] [options]
```

| Argument/Option | Flag | Type | Default | Description |
|-----------------|------|------|---------|-------------|
| `path` | *(positional)* | `str` | `Dockfile.yaml` | Path to Dockfile |
| `--verbose` | `-v` | `bool` | `false` | Show full spec details |
| `--quiet` | `-q` | `bool` | `false` | Only show errors |

### What It Checks

- File exists and is valid YAML
- Schema validation against `DockSpec` (all Pydantic validators run)
- Agent name format, entrypoint/handler format
- Framework is supported
- Auth mode, rate limit syntax, permissions
- Secret name format, event type names, port ranges
- Cross-field rules (entrypoint requires framework, array needs items, etc.)

### Example Output

```
✓ Dockfile is valid
  Agent: invoice-copilot
  Mode: entrypoint (app.graph:create_graph)
  Framework: langgraph
```

With `--verbose`, the full parsed spec is printed.

---

## `dockrion run`

Start a local development server using uvicorn.

```bash
dockrion run [path] [options]
```

| Argument/Option | Flag | Type | Default | Description |
|-----------------|------|------|---------|-------------|
| `path` | *(positional)* | `str` | `Dockfile.yaml` | Path to Dockfile |
| `--host` | | `str` | *(from Dockfile)* | Override bind host |
| `--port` | | `int` | *(from Dockfile)* | Override bind port |
| `--reload` | `-r` | `bool` | `false` | Hot reload on file changes |
| `--env-file` | `-e` | `str` | `null` | Path to `.env` file (overrides auto-detection) |
| `--verbose` | `-v` | `bool` | `false` | Show detailed output including env summary |

### What It Does

1. Loads and validates the Dockfile
2. Resolves secrets from environment / `.env` / `--env-file`
3. Generates runtime files in `.dockrion_runtime/`
4. Installs requirements (prefers `uv` if available)
5. Starts uvicorn with `main:app`

### Examples

```bash
# Default (port 8080)
dockrion run

# Custom port with hot reload
dockrion run --port 3000 --reload

# With explicit env file
dockrion run --env-file .env.development -v
```

Press `Ctrl+C` to stop the server (exits with code 0).

---

## `dockrion build`

Generate runtime files and build a Docker image.

```bash
dockrion build [path] [options]
```

| Argument/Option | Flag | Type | Default | Description |
|-----------------|------|------|---------|-------------|
| `path` | *(positional)* | `str` | `Dockfile.yaml` | Path to Dockfile |
| `--target` | | `str` | `local` | Deployment target (only `local` in V1) |
| `--tag` | | `str` | `dev` | Docker image tag |
| `--no-cache` | | `bool` | `false` | Build without Docker layer cache |
| `--env-file` | `-e` | `str` | `null` | Path to `.env` file for secret validation |
| `--allow-missing-secrets` | | `bool` | `false` | Continue even if required secrets are missing |
| `--verbose` | `-v` | `bool` | `false` | Show detailed build output |

Hidden option: `--use-local-dockrion-packages` — for framework developers only.

### What It Does

1. Loads and validates the Dockfile
2. Checks secrets (fails if required secrets missing, unless `--allow-missing-secrets`)
3. Calls `deploy()` from the SDK:
   - Generates `main.py`, `requirements.txt`, `Dockerfile` from templates
   - Resolves build context (includes, excludes, auto-detected imports)
   - Runs `docker build` to create the image
4. Reports the image name: `dockrion/{agent-name}:{tag}`

### Examples

```bash
# Default build
dockrion build

# Production tag, no cache
dockrion build --tag v1.0.0 --no-cache

# CI/CD (secrets not available locally)
dockrion build --allow-missing-secrets --tag $CI_COMMIT_SHA

# With env file for secret validation
dockrion build -e .env.production
```

---

## `dockrion test`

Invoke the agent locally without starting an HTTP server.

```bash
dockrion test [path] [options]
```

| Argument/Option | Flag | Type | Default | Description |
|-----------------|------|------|---------|-------------|
| `path` | *(positional)* | `str` | `Dockfile.yaml` | Path to Dockfile |
| `--payload` | `-p` | `str` | `null` | JSON payload as a string |
| `--payload-file` | `-f` | `str` | `null` | Path to a JSON file with the payload |
| `--output` | `-o` | `str` | `null` | Save output to file |
| `--verbose` | `-v` | `bool` | `false` | Show detailed output |

Either `--payload` or `--payload-file` is required.

### What It Does

1. Parses the JSON payload
2. Calls `invoke_local(path, payload)` from the SDK
3. Prints the result as formatted JSON
4. Optionally saves to a file

### Examples

```bash
# Inline payload
dockrion test -p '{"query": "hello"}'

# From file
dockrion test -f test_payload.json

# Save output
dockrion test -p '{"query": "test"}' -o result.json
```

> **Source:** `packages/cli/dockrion_cli/init_cmd.py`, `validate_cmd.py`, `run_cmd.py`, `build_cmd.py`, `test_cmd.py`

---

**Next:** [3.2 Utility Commands →](utility-commands.md)
