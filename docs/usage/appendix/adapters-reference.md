# Adapters Reference

[Home](../../README.md) > [Appendix](README.md)

Technical reference for the adapter system that bridges Dockrion and AI frameworks.

## AgentAdapter Protocol

The core structural protocol (PEP 544) that all adapters must satisfy:

```python
class AgentAdapter(Protocol):
    def load(self, entrypoint: str) -> None: ...
    def invoke(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...
    def get_metadata(self) -> Dict[str, Any]: ...
```

Implementations need not inherit from `AgentAdapter` — structural typing checks method signatures.

## Extended Protocols

| Protocol | Adds | Description |
|----------|------|-------------|
| `StreamingAgentAdapter` | `invoke_stream(payload) -> Iterator[Dict]` | Sync streaming |
| `AsyncAgentAdapter` | `ainvoke(payload) -> Dict` | Async invocation |
| `StatefulAgentAdapter` | `invoke(payload, config=None) -> Dict` | Config-aware invocation |

## LangGraphAdapter

For agents using LangGraph compiled state graphs.

### Load Behavior

1. Validates the entrypoint format (`module.path:factory_name`)
2. Imports the module and calls the factory function
3. Checks the returned object has a callable `.invoke()` method
4. Optionally validates against `Pregel` / `CompiledStateGraph` types (if strict)
5. Detects streaming support (`.stream()` method) and async support

### Invoke Behavior

1. Clears/sets thread-local `StreamContext`
2. Calls `runner.invoke(payload)` (or `runner.invoke(payload, config)` if supported)
3. Serializes the result with `serialize_for_json()`
4. Validates the output is a dict

### Streaming Behavior (`invoke_stream`)

1. If no `.stream()` method, falls back to single `invoke()` → one `result` event
2. Otherwise, creates a `StreamContext` (queue mode) and optional `LangGraphBackend`
3. Runs `.stream()` in a worker thread, pushes events to a queue
4. Main async loop polls the queue and yields events
5. Uses `events_filter.get_langgraph_stream_modes()` to select LangGraph stream modes (`messages`, `updates`, `custom`, `values`)
6. Drains user-emitted events from `StreamContext`

### Metadata

```python
{
    "framework": "langgraph",
    "adapter_type": "langgraph",
    "adapter_version": "0.1.0",
    "loaded": True,
    "entrypoint": "app.graph:create_graph",
    "supports_streaming": True,
    "supports_async": False,
    "supports_config": True,
    "is_langgraph_type": True
}
```

## HandlerAdapter

For plain Python callables (sync or async).

### Load Behavior

1. Validates the handler format (`module.path:callable_name`)
2. Imports the module and retrieves the callable
3. Checks it's actually callable
4. Detects if it's async (`asyncio.iscoroutinefunction`)
5. Inspects the signature for a `context` parameter (for `StreamContext` injection)

### Invoke Behavior

1. Sets the current `StreamContext` (if provided)
2. For sync handlers: calls `handler(payload)` or `handler(payload, context=context)`
3. For async handlers: runs via `asyncio.run()` or `ThreadPoolExecutor` if a loop exists
4. Validates the output is a dict
5. Serializes with `serialize_for_json()`

### Streaming Behavior (`invoke_stream`)

1. Calls `invoke()` with a queue-mode `StreamContext`
2. Yields `{"type": "result", "data": ...}` for the invoke result
3. Drains queued events from the `StreamContext`
4. Yields each queued event as `{"type": "custom", ...}`

### Metadata

```python
{
    "framework": "custom",
    "adapter_type": "handler",
    "adapter_version": "0.1.0",
    "loaded": True,
    "handler_path": "app.service:handle",
    "is_async": False,
    "accepts_context": True,
    "signature": "(payload: dict, context=None) -> dict"
}
```

## Adapter Registry

| Function | Description |
|----------|-------------|
| `get_adapter(framework)` | Instantiate the adapter for a framework. Raises `ValidationError` for unknown frameworks. |
| `get_handler_adapter()` | Shortcut for `HandlerAdapter()` |
| `register_adapter(framework, adapter_class)` | Register a custom adapter. Checks for `load`, `invoke`, `get_metadata` methods. |
| `list_supported_frameworks()` | Returns sorted list of registered framework names |
| `is_framework_supported(framework)` | Check if a framework has a registered adapter |

### Default Registry

```python
_ADAPTER_REGISTRY = {
    "langgraph": LangGraphAdapter,
    "custom": HandlerAdapter,
}
```

`langchain` is a valid framework in the schema but has **no registered adapter** yet.

## Writing a Custom Adapter

```python
from dockrion_adapters import register_adapter

class MyFrameworkAdapter:
    def __init__(self):
        self._runner = None
    
    def load(self, entrypoint: str) -> None:
        module_path, callable_name = entrypoint.rsplit(":", 1)
        # ... import and prepare ...
        
    def invoke(self, payload: dict) -> dict:
        return self._runner.run(payload)
    
    def get_metadata(self) -> dict:
        return {"framework": "my_framework", "adapter_type": "custom"}

register_adapter("my_framework", MyFrameworkAdapter)
```

After registration, `framework: my_framework` works in Dockfiles.

## Output Serialization

| Function | Description |
|----------|-------------|
| `deep_serialize(obj, max_depth=50)` | Recursively convert any Python object to JSON-serializable form. Handles: primitives, bytes, collections, Pydantic models, dataclasses, datetime, UUID, Decimal, Enum, Path, callables |
| `serialize_for_json(data: dict)` | `deep_serialize()` then ensure dict output (wraps in `{"result": ...}` if needed) |

## Error Hierarchy

All adapter errors extend `AdapterError` which extends `DockrionError`:

| Error | Code | When |
|-------|------|------|
| `AdapterError` | `ADAPTER_ERROR` | Base |
| `AdapterLoadError` | `ADAPTER_LOAD_ERROR` | `load()` fails |
| `ModuleNotFoundError` | `MODULE_NOT_FOUND` | Import fails |
| `CallableNotFoundError` | `CALLABLE_NOT_FOUND` | Symbol not in module |
| `InvalidAgentError` | `INVALID_AGENT` | Wrong shape |
| `AdapterNotLoadedError` | `ADAPTER_NOT_LOADED` | `invoke()` before `load()` |
| `AgentExecutionError` | `AGENT_EXECUTION_ERROR` | Runtime error in agent |
| `AgentCrashedError` | `AGENT_CRASHED` | Unexpected crash |
| `InvalidOutputError` | `INVALID_OUTPUT` | Non-dict return |

> **Source:** `packages/adapters/dockrion_adapters/`

---

**Previous:** [SDK Reference](sdk-reference.md) | **Next:** [Error Hierarchy →](error-hierarchy.md)
