# 4. The Generated API

[Home](../README.md)

When you run `dockrion run` or build a Docker image with `dockrion build`, Dockrion generates a FastAPI application that serves your agent as an HTTP API. This section documents the API surface your callers interact with.

## Endpoint Summary

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/` | No | Welcome page (HTML) |
| `GET` | `/health` | No | Health check |
| `GET` | `/ready` | No | Readiness probe |
| `GET` | `/metrics` | No | Prometheus metrics |
| `GET` | `/schema` | No | Agent I/O schema |
| `GET` | `/info` | No | Agent metadata |
| `POST` | `/invoke` | **Yes** | Invoke the agent |
| `POST` | `/invoke/stream` | **Yes** | Invoke with SSE streaming |
| `POST` | `/runs` | **Yes** | Create async run |
| `GET` | `/runs/{run_id}` | **Yes** | Get run status |
| `GET` | `/runs/{run_id}/events` | **Yes** | Subscribe to run events (SSE) |
| `DELETE` | `/runs/{run_id}` | **Yes** | Cancel a run |
| `GET` | `/docs` | No | Swagger UI |
| `GET` | `/redoc` | No | ReDoc |
| `GET` | `/openapi.json` | No | OpenAPI spec |

Public endpoints (`/health`, `/ready`, `/schema`, `/info`, `/metrics`) never require authentication, even when auth is enabled.

## In This Section

| Page | What it covers |
|------|----------------|
| [4.1 Endpoints Reference](endpoints-reference.md) | Per-endpoint details, curl examples, response models |
| [4.2 io_schema & Swagger](io-schema-and-swagger.md) | How Dockfile types become Swagger models |
| [4.3 Auth from Caller's Perspective](auth-callers-perspective.md) | How to pass API keys, JWTs, Swagger Authorize |
| [4.4 Streaming Consumption](streaming-consumption.md) | Client-side SSE and async runs code (JS, Python, curl) |

> **Source:** `packages/runtime/dockrion_runtime/app.py`, endpoint modules in `endpoints/`

---

**Previous:** [3. CLI Reference](../03-cli-reference/README.md) | **Next:** [5. Guides & Recipes →](../05-guides-and-recipes/README.md)
