# 1.3 Architecture Overview

[Home](../../README.md) > [Introduction](README.md)

## Package Hierarchy

Dockrion is a monorepo with seven Python packages, each with a single responsibility:

```
dockrion/packages/
├── common-py/     dockrion_common      Shared constants, errors, validation, env utils
├── schema/        dockrion_schema      Dockfile Pydantic models (DockSpec)
├── adapters/      dockrion_adapters    Framework adapters (LangGraph, Handler)
├── events/        dockrion_events      Streaming events, EventBus, RunManager
├── policy-engine/ dockrion_policy      Policy engine (tool guard, redactor)
├── telemetry/     dockrion_telemetry   Prometheus metrics, structured logging
├── runtime/       dockrion_runtime     FastAPI app generation and serving
├── sdk-python/    dockrion_sdk         Orchestration: load, validate, build, deploy
└── cli/           dockrion_cli         Typer CLI wrapping the SDK
```

**Dependency flow:**

```
dockrion_cli
    └── dockrion_sdk
            ├── dockrion_schema ──► dockrion_common
            ├── dockrion_adapters ──► dockrion_common
            ├── dockrion_runtime
            │       ├── dockrion_schema
            │       ├── dockrion_adapters
            │       ├── dockrion_events (optional)
            │       ├── dockrion_policy
            │       └── dockrion_telemetry
            └── dockrion_common
```

The `dockrion_events` package is optional — streaming features degrade gracefully if it's not installed.

## The Two Invocation Modes

Every Dockrion agent uses one of two invocation modes. This is the first decision you make when creating an agent.

### Entrypoint Mode (Factory Pattern)

```yaml
agent:
  name: my-graph-agent
  entrypoint: app.graph:create_graph
  framework: langgraph
```

Your entrypoint is a **factory function** that returns a compiled graph or runner object. Dockrion calls the factory once at startup, then calls `.invoke()` on the returned object for each request.

**When to use:** LangGraph agents, any framework that produces a stateful runner object.

### Handler Mode (Direct Callable)

```yaml
agent:
  name: my-simple-agent
  handler: app.service:handle
```

Your handler is a **plain function** (sync or async) that receives a payload dict and returns a result dict. Dockrion calls it directly for each request.

```python
def handle(payload: dict) -> dict:
    query = payload.get("query", "")
    return {"answer": f"You asked: {query}"}
```

**When to use:** Simple agents, any custom logic that doesn't need a framework.

### How the Mode Is Determined

| Dockfile has | `framework` | Mode | Adapter |
|-------------|-------------|------|---------|
| `entrypoint` only | required (e.g., `langgraph`) | Entrypoint | `LangGraphAdapter` |
| `handler` only | auto-set to `custom` | Handler | `HandlerAdapter` |
| Both | from Dockfile | Handler takes priority for invocation | `HandlerAdapter` |
| Neither | — | Validation error | — |

The `framework` field is **required** when using entrypoint mode (Dockrion cannot infer the framework from a module path alone). In handler mode, `framework` is automatically set to `"custom"` if not specified.

## Request Lifecycle

When a caller hits `POST /invoke`:

```
Request
  │
  ▼
CORSMiddleware
  │
  ▼
verify_auth (FastAPI dependency)
  │  ├── NoAuthHandler    → AuthContext.anonymous()
  │  ├── ApiKeyAuthHandler → validate key → AuthContext
  │  └── JWTAuthHandler    → decode JWT → AuthContext.from_jwt()
  │
  ▼
validate_input (PolicyEngine)
  │  └── check prompt injection patterns
  │
  ▼
InputModel validation (Pydantic, from io_schema)
  │
  ▼
adapter.invoke(payload)
  │  ├── LangGraphAdapter → factory().invoke(payload)
  │  └── HandlerAdapter   → handler(payload)
  │
  ▼
apply_output_policies (PolicyEngine)
  │  ├── redact_patterns → regex substitution
  │  └── max_output_chars → truncation
  │
  ▼
OutputModel validation (if strict mode)
  │
  ▼
InvokeResponseModel { success, output, metadata }
```

## Supported Frameworks

| Framework | Value | Adapter | Status |
|-----------|-------|---------|--------|
| LangGraph | `langgraph` | `LangGraphAdapter` | Implemented |
| LangChain | `langchain` | — | **Planned** (accepted by schema but no adapter yet) |
| Custom | `custom` | `HandlerAdapter` | Implemented |

---

**Previous:** [1.2 Core Concepts](core-concepts.md) | **Next:** [1.4 Quickstart →](quickstart.md)
