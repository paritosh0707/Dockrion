# StreamContext for Agent Authors

[Home](../../../README.md) > [The Dockfile](../README.md) > [Streaming](README.md)

`StreamContext` is the API your agent code uses to emit events during execution. It's available in both handler mode and entrypoint mode.

## Getting the Context

### Handler Mode (second parameter)

If your handler function has a parameter named `context` (or annotated as `StreamContext`), the `HandlerAdapter` automatically passes the streaming context:

```python
def handle(payload: dict, context=None) -> dict:
    if context:
        context.sync_emit_progress(step="processing", progress=0.5, message="Halfway done")
    
    answer = process(payload["query"])
    
    return {"answer": answer}
```

### Thread-Local Access

Anywhere in your code, you can access the current context via the thread-local helper:

```python
from dockrion_events import get_current_context

def my_helper():
    ctx = get_current_context()
    if ctx:
        ctx.sync_emit_progress(step="helper", progress=0.8, message="Almost done")
```

## Emit Methods

### Async Methods (for async handlers)

| Method | Parameters | Description |
|--------|-----------|-------------|
| `emit_started(agent_name, framework=None)` | agent name, optional framework | Emitted automatically by runtime — usually not called manually |
| `emit_progress(step, progress, message)` | step name, 0.0–1.0, message | Progress update |
| `checkpoint(name, data)` | checkpoint name, data dict | Save a checkpoint |
| `emit_token(content, finish_reason=None)` | token text, optional reason | Streaming token (for LLM output) |
| `emit_step(node_name, duration_ms, input_keys, output_keys)` | node details | Graph node completion |
| `emit_complete(output, latency_seconds, metadata=None)` | result, latency, metadata | Emitted automatically by runtime |
| `emit_error(error, code=None, details=None)` | error message, code, details | Emitted automatically by runtime |
| `emit_heartbeat()` | — | Keep-alive signal |
| `emit_cancelled(reason=None)` | cancellation reason | Run cancelled |
| `emit(event_type, **data)` | custom type, arbitrary data | Custom event |

### Sync Methods (for sync handlers)

| Method | Equivalent |
|--------|-----------|
| `sync_emit_progress(...)` | `emit_progress(...)` |
| `sync_checkpoint(...)` | `checkpoint(...)` |
| `sync_emit_token(...)` | `emit_token(...)` |
| `sync_emit_step(...)` | `emit_step(...)` |
| `sync_emit(...)` | `emit(...)` |
| `sync_emit_heartbeat()` | `emit_heartbeat()` |

Use `sync_*` methods from synchronous code. They handle the asyncio event loop bridging internally.

## Event Filtering

Events are automatically filtered by the `EventsFilter` configured in the Dockfile's `streaming.events.allowed`. If your handler emits a `progress` event but the preset is `chat` (which doesn't include progress), the event is silently dropped.

Mandatory events (`started`, `complete`, `error`, `cancelled`) bypass filtering.

## Custom Events

Emit events with your own types:

```python
def handle(payload: dict, context=None) -> dict:
    if context:
        context.sync_emit("custom:analysis_started", document_id="doc_123")
        # ... process ...
        context.sync_emit("custom:analysis_complete", results={"score": 0.95})
    
    return {"answer": "done"}
```

For custom events to reach callers, they must be allowed in the Dockfile:

```yaml
streaming:
  events:
    allowed:
      - token
      - custom:analysis_started
      - custom:analysis_complete
```

Or use `custom` (without a name) to allow all custom events.

## Operating Modes

`StreamContext` operates in two modes, selected automatically:

| Mode | When | Behavior |
|------|------|----------|
| **EventBus mode** | Async runs (`/runs`) | Events published to `EventBus` → `EventBackend` → subscribers |
| **Queue mode** | Direct SSE (`/invoke/stream`), adapters | Events queued internally, drained by the streaming response generator |

In queue mode, events are stored in an internal list and retrieved via `drain_queued_events()`. In EventBus mode, events are published to the configured backend (memory or Redis) for distribution to subscribers.

### Streaming Backends

When a `streaming_backend` is attached to the context (e.g., `LangGraphBackend` or `QueueBackend`), events are first routed through the backend's `emit()` method before the standard path. This enables framework-native streaming integration.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `run_id` | `str` | The current run's ID |
| `queue_mode` | `bool` | Whether operating in queue mode |
| `events_filter` | `EventsFilter` | The active event filter |
| `streaming_backend` | `StreamingBackend` | The attached streaming backend (if any) |

> **Source:** `StreamContext` in `packages/events/dockrion_events/context.py`; `get_current_context()`, `set_current_context()` in the same module

---

**Previous:** [Backends](backends.md) | **Up:** [Streaming Overview](README.md)
