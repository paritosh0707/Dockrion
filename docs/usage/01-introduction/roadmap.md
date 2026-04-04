# 1.5 Roadmap

[Home](../../README.md) > [Introduction](README.md)

## How to Read This Page

Features are grouped by implementation status. "Implemented" means the code is working and tested. "Scaffolded" means the schema accepts the configuration but runtime behavior is partial or absent. "Planned" means design or placeholder code exists but the feature is not functional.

## Currently Implemented (v1.0)

- **Dockfile v1.0 schema** — full Pydantic validation with `extra="allow"` for forward compatibility
- **Handler mode** — sync and async Python callables as agents
- **Entrypoint mode** — factory functions returning LangGraph compiled graphs
- **LangGraph adapter** — load, invoke, and stream with compiled state graphs
- **Handler adapter** — load, invoke, and stream with plain functions
- **FastAPI runtime generation** — `main.py`, `requirements.txt`, `Dockerfile` from templates
- **CLI** — `init`, `validate`, `run`, `build`, `test`, `inspect`, `add`, `doctor`, `logs`, `version`
- **API key authentication** — single key, multi-key with prefix, env var, custom header, bearer token
- **JWT authentication** — JWKS URL, static public key, claims mapping, algorithm selection
- **Roles and permissions** — role definitions with granular permissions (`deploy`, `invoke`, `view_metrics`, etc.)
- **Rate limits** — per-role rate limit configuration (schema validated; enforcement is partial)
- **Policies** — prompt injection blocking, output redaction (regex), output truncation, tool gating
- **SSE streaming** — `POST /invoke/stream` with Server-Sent Events
- **Async runs** — `POST /runs` → `GET /runs/{id}/events` lifecycle
- **Event types** — `started`, `progress`, `token`, `step`, `checkpoint`, `complete`, `error`, `heartbeat`, `cancelled`
- **Event presets** — `minimal`, `chat`, `debug`, `all`
- **In-memory event backend** — default for development
- **Redis event backend** — production streaming backend
- **Prometheus metrics** — request count, latency histogram, active requests gauge
- **Structured logging** — JSON-formatted with request IDs
- **Secrets management** — required/optional declaration, env resolution, strict mode
- **Environment variable substitution** — `${VAR}` and `${VAR:-default}` in Dockfile YAML
- **Docker build** — image generation with dependency merging and build context control
- **Swagger UI and ReDoc** — auto-generated from `io_schema`
- **Dynamic Pydantic models** — `io_schema` types map to Swagger request/response models

## Coming Soon (Scaffolded, Not Yet Functional)

- **OAuth2 authentication** — `OAuth2Config` schema exists, no runtime handler implemented
- **WebSocket streaming** — accepted by `expose.streaming` validator, no WebSocket endpoint exists
- **LangChain adapter** — `langchain` is a valid `framework` value, but no `LangChainAdapter` is registered
- **`dockrion deploy`** — CLI command placeholder exists, not implemented (reserved for controller integration)
- **Langfuse integration** — `observability.langfuse` config exists, env var names defined in constants, but no runtime Langfuse client code
- **Rate limit enforcement** — rate limit parsing and validation work, but runtime enforcement middleware is not yet wired

## Planned (v1.1+)

- **Controller service** — remote deployment management (`ControllerClient` stub exists)
- **Multi-agent orchestration** — deploying and routing between multiple agents
- **Custom adapter registration** — `register_adapter()` API exists, docs/examples pending
- **Tracing integration** — OpenTelemetry support (telemetry package currently has Prometheus only)

## Under Consideration

- Agent versioning and rollback
- A/B testing between agent versions
- Dashboard for monitoring deployed agents
- Plugin system for extending the runtime

---

**Previous:** [1.4 Quickstart](quickstart.md) | **Next:** [2. The Dockfile →](../02-the-dockfile/README.md)
