# Async Runs (Pattern B)

[Home](../../../README.md) > [The Dockfile](../README.md) > [Streaming](README.md)

Pattern B decouples submission from consumption: you **create a run** via `POST /runs`, then **subscribe to events** via `GET /runs/{id}/events`. This is useful for long-running agents, background processing, or when multiple clients need to observe the same run.

## Enabling Async Runs

```yaml
streaming:
  async_runs: true     # required to enable Pattern B
  backend: memory      # or redis for production
```

The `async_runs: true` setting registers the `/runs` router. It also requires the `dockrion_events` package to be installed.

## Configuration Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `async_runs` | `bool` | `true` | Enable the `/runs` endpoint family |
| `allow_client_ids` | `bool` | `true` | Allow callers to provide their own `run_id` via query parameter |

### Run ID Generation

| Config | Behavior |
|--------|----------|
| Default (`id_generator` omitted) | UUID v4 |
| `id_generator.type: uuid` | UUID v4 |
| `id_generator.type: custom` | Custom generator function (requires `id_generator.handler`) |

```yaml
streaming:
  id_generator:
    type: custom
    handler: app.utils:generate_run_id
```

### Connection Settings

```yaml
streaming:
  connection:
    default_timeout: 300              # SSE subscription timeout (seconds, 1–3600)
    max_subscribers_per_run: 100      # max concurrent SSE listeners per run (1–1000)
```

## Run Lifecycle

```
               POST /runs
                   │
                   ▼
             ┌──────────┐
             │ ACCEPTED  │  → 202 response with run_id
             └────┬─────┘
                  │  (agent starts executing)
                  ▼
             ┌──────────┐
             │ RUNNING   │  → emitting events
             └────┬─────┘
                  │
          ┌───────┼───────┐
          ▼       ▼       ▼
    ┌──────────┐ ┌──────┐ ┌──────────┐
    │COMPLETED │ │FAILED│ │CANCELLED │
    └──────────┘ └──────┘ └──────────┘
```

### RunStatus Values

| Status | Description |
|--------|-------------|
| `ACCEPTED` | Run created, waiting to start |
| `RUNNING` | Agent is executing |
| `COMPLETED` | Agent finished successfully |
| `FAILED` | Agent threw an error |
| `CANCELLED` | Run was cancelled via `DELETE /runs/{id}` |

## API Endpoints

### Create a run

```bash
curl -X POST http://localhost:8080/runs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"query": "process invoice #1234"}'
```

Response (202):

```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "ACCEPTED",
  "events_url": "/runs/550e8400-e29b-41d4-a716-446655440000/events",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### Subscribe to events

```bash
curl -N http://localhost:8080/runs/550e8400.../events \
  -H "X-API-Key: your-key"
```

Query parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout` | `int` | `300` | Connection timeout in seconds (1–3600) |
| `from_sequence` | `int` | `0` | Replay events from this sequence number |

The `from_sequence` parameter enables **event replay**: if a client disconnects, it can reconnect and receive events it missed.

### Check run status

```bash
curl http://localhost:8080/runs/550e8400.../  \
  -H "X-API-Key: your-key"
```

### Cancel a run

```bash
curl -X DELETE http://localhost:8080/runs/550e8400... \
  -H "X-API-Key: your-key"
```

Terminal events (complete, error, cancelled) close the SSE connection automatically.

> **Source:** `RunManager`, `Run`, `RunStatus` in `packages/events/dockrion_events/run_manager.py`; `/runs` endpoints in `packages/runtime/dockrion_runtime/endpoints/runs.py`

---

**Previous:** [SSE Streaming](sse.md) | **Next:** [Event Types →](event-types.md)
