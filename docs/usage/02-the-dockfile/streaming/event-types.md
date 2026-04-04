# Event Types

[Home](../../../README.md) > [The Dockfile](../README.md) > [Streaming](README.md)

Every SSE event has a `type` field that identifies what kind of event it is. Events are defined as Pydantic models in `dockrion_events/models.py`.

## All Event Types

| Type | Class | Category | Description |
|------|-------|----------|-------------|
| `started` | `StartedEvent` | Mandatory | Run started. Contains `agent_name` and `framework`. |
| `complete` | `CompleteEvent` | Mandatory | Run finished. Contains `output`, `latency_seconds`, `metadata`. |
| `error` | `ErrorEvent` | Mandatory | Run failed. Contains `error` message, `code`, `details`. |
| `cancelled` | `CancelledEvent` | Mandatory | Run was cancelled. Contains `reason`. |
| `progress` | `ProgressEvent` | Configurable | Progress update. Contains `step`, `progress` (0.0–1.0), `message`. |
| `token` | `TokenEvent` | Configurable | Streaming token. Contains `content`, optional `finish_reason`. |
| `step` | `StepEvent` | Configurable | Graph node completed. Contains `node_name`, `duration_ms`, `input_keys`, `output_keys`. |
| `checkpoint` | `CheckpointEvent` | Configurable | Checkpoint saved. Contains `name`, `data`. |
| `heartbeat` | `HeartbeatEvent` | Configurable | Keep-alive signal. No extra fields. |

### Mandatory vs Configurable

**Mandatory events** (`started`, `complete`, `error`, `cancelled`) are always emitted regardless of event configuration. They define the run lifecycle.

**Configurable events** can be included or excluded using presets or explicit lists.

### Common Fields (BaseEvent)

Every event includes:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique event ID (auto-generated UUID) |
| `type` | `string` | Event type name |
| `run_id` | `string` | Run this event belongs to |
| `sequence` | `int` | Monotonic sequence number within the run |
| `timestamp` | `string` | ISO 8601 UTC timestamp |

### Terminal Events

`TERMINAL_EVENT_TYPES = {"complete", "error", "cancelled"}`

When a terminal event is received on an SSE connection, the client should expect the connection to close.

## Event Presets

Configure which events are emitted using the `streaming.events.allowed` field:

```yaml
streaming:
  events:
    allowed: chat    # preset name or explicit list
```

### Preset Definitions

| Preset | Included Events |
|--------|----------------|
| `minimal` | *(mandatory only)* — `started`, `complete`, `error`, `cancelled` |
| `chat` | `token` + mandatory |
| `debug` | `token`, `step`, `progress`, `checkpoint`, `heartbeat` + mandatory |
| `all` | All event types + mandatory |

### Explicit List

Instead of a preset, you can specify individual event types:

```yaml
streaming:
  events:
    allowed:
      - token
      - progress
      - heartbeat
```

Mandatory events are always included even if not listed.

## Custom Events

Your agent can emit custom events using the `custom:` prefix:

```yaml
streaming:
  events:
    allowed:
      - token
      - custom              # allow ALL custom events
      - custom:my_event     # or allow specific custom events
```

Custom event names must match `^[a-zA-Z_][a-zA-Z0-9_]*$`.

To emit custom events from your agent code, use `StreamContext.emit()` — see [StreamContext](stream-context.md).

## Heartbeat Configuration

```yaml
streaming:
  events:
    heartbeat_interval: 15       # seconds between heartbeats (1–300)
    max_run_duration: 3600       # max run lifetime in seconds (1–86400)
```

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `heartbeat_interval` | `int` | `15` | 1–300 | Seconds between heartbeat events |
| `max_run_duration` | `int` | `3600` | 1–86400 | Maximum run duration before timeout |

## SSE Wire Format

Each event is serialized to SSE format by `BaseEvent.to_sse()`:

```
event: token
data: {"id":"evt_abc","type":"token","run_id":"run_123","sequence":5,"timestamp":"2025-01-15T10:30:05Z","content":"Hello","finish_reason":null}

```

> **Source:** Event models in `packages/events/dockrion_events/models.py`; `EventsFilter` in `packages/events/dockrion_events/filter.py`; `StreamingEventsConfig` in `packages/schema/dockrion_schema/dockfile_v1.py`

---

**Previous:** [Async Runs](async-runs.md) | **Next:** [Backends →](backends.md)
