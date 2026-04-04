# 2.1 agent

[Home](../../README.md) > [The Dockfile](README.md)

The `agent` section identifies your AI agent: its name, where its code lives, and which framework it uses.

## Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | `string` | **Yes** | — | Agent name. Must match `^[a-z][a-z0-9-]*$` (lowercase, hyphens allowed, starts with letter). |
| `entrypoint` | `string` | Conditional | `null` | Module path to a factory function (`module.path:callable`). The factory is called once at startup; its return value must have an `.invoke()` method. |
| `handler` | `string` | Conditional | `null` | Module path to a callable (`module.path:callable`). Called directly for each request. Can be sync or async. |
| `framework` | `string` | Conditional | `null` | One of `langgraph`, `langchain`, `custom`. Required when using `entrypoint`. Auto-set to `custom` when only `handler` is provided. |
| `description` | `string` | No | `null` | Human-readable description of the agent. |

At least one of `entrypoint` or `handler` must be provided. If both are present, the handler takes priority for invocation.

## Validation Rules

### Name Format

The `name` field is validated by `validate_agent_name()` from `dockrion_common`. It must:

- Start with a lowercase letter
- Contain only lowercase letters, digits, and hyphens
- Match the pattern `^[a-z][a-z0-9-]*$`

### Entrypoint and Handler Format

Both `entrypoint` and `handler` follow the `module.path:callable_name` format. They are validated by `validate_entrypoint()` and `validate_handler()` respectively, which check:

- The string contains exactly one `:` separator
- The module path portion is a valid dotted Python module path
- The callable name is a valid Python identifier

### Cross-Field Validator

The `validate_entrypoint_or_handler` model validator enforces:

1. At least one of `entrypoint` or `handler` must be set
2. If `framework` is `null` and only `handler` is set → `framework` is automatically set to `"custom"`
3. If `framework` is `null` and only `entrypoint` is set → validation error (framework must be explicit for entrypoint mode)

### Supported Frameworks

| Value | Adapter | Status |
|-------|---------|--------|
| `langgraph` | `LangGraphAdapter` | Implemented |
| `langchain` | — | **Coming soon** (schema accepts it; no adapter registered yet) |
| `custom` | `HandlerAdapter` | Implemented |

## Examples

### Handler Mode (simplest)

```yaml
agent:
  name: echo-bot
  handler: app.service:handle
```

`framework` is automatically set to `custom`. The callable `handle` in `app/service.py` is called for every request.

### Entrypoint Mode (LangGraph)

```yaml
agent:
  name: invoice-copilot
  entrypoint: app.graph:create_graph
  framework: langgraph
```

`create_graph()` is called once at startup. The returned compiled graph's `.invoke()` is used for each request.

### Both (handler takes priority)

```yaml
agent:
  name: dual-agent
  entrypoint: app.graph:create_graph
  handler: app.service:handle
  framework: langgraph
```

The handler is used for invocation. The entrypoint is still loaded for metadata/health purposes.

## How the Runtime Loads Your Agent

1. `RuntimeConfig.from_spec()` reads `agent.handler` or `agent.entrypoint` and `agent.framework`
2. During app startup (FastAPI lifespan):
   - Handler mode: `get_handler_adapter().load(config.agent_handler)`
   - Entrypoint mode: `get_adapter(config.agent_framework).load(config.agent_entrypoint)`
3. The adapter imports your module, resolves the callable, and prepares it for invocation
4. The `state.ready` flag is set to `true` once loading succeeds

If loading fails (bad import, missing callable, wrong type), the `/ready` endpoint returns 503 and the agent cannot serve requests.

> **Source:** `AgentConfig` in `packages/schema/dockrion_schema/dockfile_v1.py`; adapter loading in `packages/runtime/dockrion_runtime/app.py`

---

**Next:** [2.2 io_schema →](io-schema.md)
