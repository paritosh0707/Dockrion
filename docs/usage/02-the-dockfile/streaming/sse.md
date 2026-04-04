# SSE Streaming (Pattern A)

[Home](../../../README.md) > [The Dockfile](../README.md) > [Streaming](README.md)

Pattern A is **direct SSE streaming**: the caller sends a payload to `POST /invoke/stream` and receives Server-Sent Events as the agent executes.

## Enabling SSE

SSE is enabled by default. The `expose.streaming` field controls this:

```yaml
expose:
  rest: true
  streaming: sse    # this is the default
```

When `streaming` is set to `"sse"` or left at its default, the runtime registers the `POST /invoke/stream` endpoint.

## How It Works

```
Client                                  Runtime
  │                                       │
  │  POST /invoke/stream                  │
  │  { "query": "analyze this" }          │
  │ ─────────────────────────────────►    │
  │                                       │  adapter.invoke_stream(payload)
  │  event: started                       │
  │  data: {"run_id":"abc","agent":"..."}│
  │ ◄──────────────────────────────────   │
  │                                       │
  │  event: token                         │
  │  data: {"content":"The"}              │
  │ ◄──────────────────────────────────   │
  │                                       │
  │  event: token                         │
  │  data: {"content":" answer"}          │
  │ ◄──────────────────────────────────   │
  │                                       │
  │  event: complete                      │
  │  data: {"output":{...},"latency":..} │
  │ ◄──────────────────────────────────   │
  │                                       │
  Connection closes after terminal event
```

### Response Format

Each SSE event follows the standard format:

```
event: <event_type>
data: <json_payload>

```

Two newlines separate events. The `Content-Type` is `text/event-stream`.

### Response Headers

| Header | Value |
|--------|-------|
| `Content-Type` | `text/event-stream` |
| `Cache-Control` | `no-cache` |
| `Connection` | `keep-alive` |
| `X-Accel-Buffering` | `no` |

The `X-Accel-Buffering: no` header tells Nginx to disable proxy buffering, ensuring events stream in real time.

## Event Filtering

Events emitted during streaming are filtered by the `events` configuration (see [Event Types](event-types.md)). If you use a preset like `chat`, only `started`, `token`, `complete`, and `error` events are emitted — others are silently dropped.

The runtime creates an `EventsFilter` from `streaming.events.allowed` and passes it to the adapter's `invoke_stream()`.

## Fallback Behavior

If the adapter does not support streaming (no `invoke_stream` method), the runtime:

1. Calls the synchronous `invoke()` method
2. Emits a single `complete` event with the full output
3. Closes the connection

This means SSE always works, even with adapters that don't support incremental streaming.

## curl Example

```bash
curl -N -X POST http://localhost:8080/invoke/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"query": "explain quantum computing"}'
```

The `-N` flag disables curl's output buffering so events appear as they arrive.

> **Source:** `invoke_agent_stream()` in `packages/runtime/dockrion_runtime/endpoints/invoke.py`

---

**Up:** [Streaming Overview](README.md) | **Next:** [Async Runs →](async-runs.md)
