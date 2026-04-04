# 2.6 Streaming

[Home](../../README.md) > [The Dockfile](../README.md) > Streaming

Dockrion supports two streaming patterns for delivering real-time events from your agent to callers:

| Pattern | Endpoint | How it works |
|---------|----------|-------------|
| **A — Direct SSE** | `POST /invoke/stream` | Caller sends a payload, receives Server-Sent Events as the agent runs |
| **B — Async Runs** | `POST /runs` → `GET /runs/{id}/events` | Caller starts a run, polls or subscribes for events via a separate SSE endpoint |

Both patterns are configured through the `expose` and `streaming` sections of the Dockfile.

## Expose Config

The `expose` section controls the HTTP surface:

```yaml
expose:
  rest: true
  streaming: sse       # sse | websocket | none
  port: 8080
  host: 0.0.0.0
  cors:
    origins: ["*"]
    methods: ["*"]
```

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `rest` | `bool` | `true` | Enable REST endpoints (`/invoke`, `/health`, etc.) |
| `streaming` | `str` | `"sse"` | `"sse"`, `"websocket"`, or `"none"`. WebSocket is **planned, not yet implemented**. |
| `port` | `int` | `8080` | Must be 1–65535 |
| `host` | `str` | `"0.0.0.0"` | Bind address |
| `cors` | `dict` | `null` | If omitted, defaults to `origins: ["*"]`, `methods: ["*"]` |

**Validation:** At least one of `rest` or `streaming` must be enabled (the model validator rejects `rest: false` with `streaming: none`).

## Streaming Config

The `streaming` section controls async runs, backends, and event behavior:

```yaml
streaming:
  async_runs: true
  backend: memory      # memory | redis
  allow_client_ids: true
  events:
    allowed: chat      # preset or list
    heartbeat_interval: 15
    max_run_duration: 3600
  connection:
    default_timeout: 300
    max_subscribers_per_run: 100
```

## In This Section

| Page | What it covers |
|------|----------------|
| [SSE Streaming](sse.md) | Pattern A configuration, how `/invoke/stream` works |
| [Async Runs](async-runs.md) | Pattern B configuration, `/runs` lifecycle |
| [Event Types](event-types.md) | All event types, presets (minimal/chat/debug/all), custom events |
| [Backends](backends.md) | Memory vs Redis backends |
| [StreamContext](stream-context.md) | Emitting events from your agent code |

> **Source:** `ExposeConfig`, `StreamingConfig` in `packages/schema/dockrion_schema/dockfile_v1.py`; `dockrion_events` package

---

**Up:** [The Dockfile](../README.md) | **Previous:** [2.5 Secrets](../secrets.md) | **Next:** [2.7 Observability →](../observability.md)
