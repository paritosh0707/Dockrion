# 2.7 observability

[Home](../../README.md) > [The Dockfile](README.md)

The `observability` section configures metrics, tracing, and logging for your agent.

## Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `langfuse` | `dict[str, str]` | `null` | Langfuse tracing configuration |
| `tracing` | `bool` | `true` | Enable tracing (reserved for future OpenTelemetry integration) |
| `log_level` | `string` | `"info"` | One of `debug`, `info`, `warn`, `error` |
| `metrics` | `dict[str, bool]` | `{"latency": true, "tokens": true, "cost": true}` | Toggle individual metric types |

## Prometheus Metrics

The runtime exposes Prometheus metrics at `GET /metrics`, powered by the `prometheus_client` library.

### Built-in Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `dockrion_requests_total` | Counter | `agent`, `version` | Total requests processed |
| `dockrion_request_latency_seconds` | Histogram | `agent`, `version` | Request latency distribution |
| `dockrion_active_requests` | Gauge | — | Currently in-flight requests |

These metrics are recorded by `RuntimeMetrics` in the runtime. Every `/invoke` and `/runs` call increments the counter and records latency.

### Scraping with Prometheus

Add this to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: dockrion-agent
    scrape_interval: 15s
    static_configs:
      - targets: ["localhost:8080"]
    metrics_path: /metrics
```

The `metrics` dict in the Dockfile controls which metric categories are enabled. Setting `latency: false` disables the latency histogram, etc.

## Langfuse Integration

> **Status: Coming soon.** The Dockfile schema accepts Langfuse config and environment variable names are defined (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`), but no runtime Langfuse client is wired yet.

When implemented, configure it as:

```yaml
observability:
  langfuse:
    public_key: ${LANGFUSE_PUBLIC_KEY}
    secret_key: ${LANGFUSE_SECRET_KEY}
    host: "https://cloud.langfuse.com"
```

The Langfuse keys should be declared in the `secrets` section:

```yaml
secrets:
  optional:
    - name: LANGFUSE_PUBLIC_KEY
    - name: LANGFUSE_SECRET_KEY
```

## Log Levels

| Level | What it shows |
|-------|--------------|
| `debug` | Everything, including internal framework details |
| `info` | Normal operations, request handling |
| `warn` | Warnings about potential issues |
| `error` | Only errors |

The `log_level` is validated to be one of `debug`, `info`, `warn`, `error`.

## Structured Logging

Dockrion uses JSON-formatted structured logging via `DockrionLogger`:

```json
{
  "event": "request_processed",
  "agent": "my-agent",
  "latency_ms": 245,
  "request_id": "abc-123",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

The `log_event()` function from `dockrion_telemetry.logger` writes one JSON line per event to stdout. For service-level logging, use `get_logger()` from `dockrion_common.logger`, which returns a `DockrionLogger` instance supporting `debug()`, `info()`, `warning()`, `error()`, and context propagation via `with_context()`.

## Example

```yaml
observability:
  log_level: info
  tracing: true
  metrics:
    latency: true
    tokens: true
    cost: false
  langfuse:
    public_key: ${LANGFUSE_PUBLIC_KEY}
    secret_key: ${LANGFUSE_SECRET_KEY}
```

> **Source:** `Observability` in `packages/schema/dockrion_schema/dockfile_v1.py`; `RuntimeMetrics` in `packages/runtime/dockrion_runtime/metrics.py`; `dockrion_telemetry` package

---

**Previous:** [2.6 Streaming](streaming/README.md) | **Next:** [2.8 build config →](build-config.md)
