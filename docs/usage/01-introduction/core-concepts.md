# 1.2 Core Concepts

[Home](../../README.md) > [Introduction](README.md)

Dockrion is made up of six core components. Understanding these is essential before diving into configuration or CLI usage.

## Dockfile

The **Dockfile** (`Dockfile.yaml`) is the YAML configuration file at the root of your agent project. It declares:

- Which Python callable to use as the agent (`agent.handler` or `agent.entrypoint`)
- What the agent accepts and returns (`io_schema`)
- How to authenticate callers (`auth`)
- Safety policies, secrets, streaming config, observability, and build options

The Dockfile is validated against the `DockSpec` Pydantic model before any operation. Invalid Dockfiles are rejected with clear error messages.

## DockSpec

The **DockSpec** is the Pydantic model that defines the schema for Dockfile validation. It lives in the `dockrion_schema` package. Every field, default value, and validator described in the [Dockfile reference](../02-the-dockfile/README.md) maps directly to a Pydantic class in `DockSpec`.

All DockSpec models use `extra="allow"`, which means unknown fields are preserved (not rejected). This enables forward compatibility — you can add experimental fields without breaking validation.

## Runtime

The **Runtime** is the FastAPI application that Dockrion generates to serve your agent. When you run `dockrion run` or `dockrion build`, the SDK generates:

- A `main.py` that creates the FastAPI app from your DockSpec
- A `requirements.txt` with merged dependencies
- A `Dockerfile` (on build) for containerization

The runtime includes health checks, metrics, auth middleware, streaming support, policy enforcement, and dynamic Swagger documentation — all derived from your Dockfile.

## Adapters

**Adapters** bridge Dockrion and AI frameworks. They implement a common protocol (`AgentAdapter`) with three methods:

| Method | Purpose |
|--------|---------|
| `load(entrypoint)` | Import the agent module and prepare it for invocation |
| `invoke(payload)` | Execute the agent with the given input |
| `get_metadata()` | Return framework-specific metadata |

Dockrion ships with two adapters:

| Adapter | Framework | Agent type |
|---------|-----------|------------|
| `LangGraphAdapter` | `langgraph` | A factory function returning a compiled graph with `.invoke()` |
| `HandlerAdapter` | `custom` | Any Python callable (sync or async) |

The adapter is selected automatically based on `agent.framework` in the Dockfile. You can also register custom adapters via `register_adapter()`.

### Extended Protocols

Beyond the core `AgentAdapter`, optional protocols exist:

- **`StreamingAgentAdapter`** — adds `invoke_stream()` for yielding events
- **`AsyncAgentAdapter`** — adds `ainvoke()` for async invocation
- **`StatefulAgentAdapter`** — adds `config` parameter for stateful runs

## SDK

The **SDK** (`dockrion_sdk`) is the Python library that powers both the CLI and programmatic usage. Key functions:

| Function | What it does |
|----------|-------------|
| `load_dockspec()` | Load and validate a Dockfile, resolve env vars |
| `validate_dockspec()` | Validate without loading the agent |
| `invoke_local()` | Run the agent locally (no HTTP server) |
| `run_local()` | Start a local uvicorn dev server |
| `deploy()` | Generate runtime + build Docker image |
| `generate_runtime()` | Write generated files without building |

See the [SDK Reference](../appendix/sdk-reference.md) for the full API.

## CLI

The **CLI** (`dockrion`) is the command-line interface for all operations. It wraps the SDK into developer-friendly commands:

```bash
dockrion init my-agent        # scaffold a Dockfile
dockrion validate             # check the Dockfile
dockrion run                  # start local dev server
dockrion build                # build Docker image
dockrion test -p '{"q":"hi"}' # invoke locally without HTTP
```

See the [CLI Reference](../03-cli-reference/README.md) for all commands and flags.

---

**Previous:** [1.1 What is Dockrion](what-is-dockrion.md) | **Next:** [1.3 Architecture Overview →](architecture-overview.md)
