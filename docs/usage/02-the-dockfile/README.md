# 2. The Dockfile

[Home](../README.md)

The Dockfile (`Dockfile.yaml`) is the single configuration file that defines everything about your AI agent deployment. It is validated against the `DockSpec` Pydantic model in `dockrion_schema`. Unknown fields are allowed (`extra="allow"`) for forward compatibility.

## Minimal Valid Dockfile

```yaml
version: "1.0"
agent:
  name: my-agent
  handler: app.service:handle
io_schema:
  input:
    type: object
    properties:
      query:
        type: string
  output:
    type: object
expose:
  rest: true
```

Only `version`, `agent`, `io_schema`, and `expose` are required. Everything else is optional.

## In This Section

| Page | What it covers |
|------|----------------|
| [2.1 agent](agent.md) | `name`, `entrypoint` vs `handler`, `framework`, validation rules |
| [2.2 io_schema](io-schema.md) | Input/output contracts, types, `strict` mode |
| [2.3 auth](auth/README.md) | Authentication modes: API key, JWT, OAuth2, roles, rate limits |
| [2.4 policies](policies/README.md) | Tool gating, prompt injection blocking, output redaction |
| [2.5 secrets](secrets.md) | Declaring required and optional secrets |
| [2.6 streaming](streaming/README.md) | SSE, async runs, event types, backends, StreamContext |
| [2.7 observability](observability.md) | Prometheus metrics, Langfuse, log levels, structured logging |
| [2.8 build config](build-config.md) | Docker build includes, excludes, auto-detection |
| [2.9 env substitution](env-substitution.md) | `${VAR}` and `${VAR:-default}` syntax, `.env` loading order |
| [2.10 metadata](metadata.md) | Maintainer, version, tags |
| [2.11 Complete example](complete-example.md) | Full annotated Dockfile with every section |

---

**Previous:** [1. Introduction](../01-introduction/README.md) | **Next:** [3. CLI Reference →](../03-cli-reference/README.md)
