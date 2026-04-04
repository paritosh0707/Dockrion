# 5.9 FAQ

[Home](../../README.md) > [Guides & Recipes](README.md)

## General

**Q: What Python versions does Dockrion support?**
A: Python 3.11 and 3.12. The `requires-python` is `>=3.11`.

**Q: Do I need Docker to use Dockrion?**
A: Not for development. `dockrion run` starts a local server without Docker. Docker is only required for `dockrion build`.

**Q: Can I use Dockrion without LangGraph or LangChain?**
A: Yes. Use handler mode with `framework: custom`. Any Python callable (sync or async) that takes a dict and returns a dict works.

## Dockfile

**Q: What happens if I add unknown fields to the Dockfile?**
A: They are preserved. All DockSpec models use `extra="allow"`, so unknown fields pass validation and are kept in the parsed spec. This ensures forward compatibility.

**Q: Can I use multiple Dockfiles in one project?**
A: Yes. Pass the path to any command: `dockrion validate config/agent-v2.yaml`, `dockrion run my-dockfile.yaml`, etc. The default is always `Dockfile.yaml` in the current directory.

**Q: What's the difference between `entrypoint` and `handler`?**
A: `entrypoint` points to a factory function that returns an object with `.invoke()` — used for frameworks like LangGraph. `handler` points to a plain function called directly for each request. See [Architecture Overview](../01-introduction/architecture-overview.md).

## Authentication

**Q: Can I use both API key and JWT at the same time?**
A: No. The `auth.mode` field selects one mode. Choose the one that fits your use case.

**Q: How do I test auth in Swagger UI?**
A: Open `/docs`, click the "Authorize" button, enter your key or JWT. All subsequent "Try it out" calls will include the credentials.

**Q: What if PyJWT isn't installed and I set `mode: jwt`?**
A: The runtime falls back to `NoAuthHandler` (no auth enforced). Install it with `pip install dockrion[jwt]`.

## Streaming

**Q: Can I use SSE with a regular browser fetch?**
A: `POST /invoke/stream` requires a POST body, so native `EventSource` (GET-only) doesn't work for that endpoint. Use `fetch` with a readable stream. However, `GET /runs/{id}/events` works with native `EventSource`. See [Streaming Consumption](../04-the-generated-api/streaming-consumption.md).

**Q: What happens if I enable streaming but my adapter doesn't support it?**
A: The runtime falls back to calling `invoke()` synchronously and emitting a single `complete` event with the full output.

**Q: Is WebSocket supported?**
A: Not yet. The schema accepts `streaming: websocket` but no WebSocket endpoint exists in the runtime. Use SSE for now.

## Build & Deploy

**Q: Are secrets baked into the Docker image?**
A: No. Secrets are only used for validation during build. They must be provided at runtime via `docker run -e` or your orchestrator's secret management.

**Q: How do I include data files in the Docker image?**
A: Use `build.include` in the Dockfile:

```yaml
build:
  include:
    directories: [data]
    files: [config.json]
    patterns: ["prompts/*.txt"]
```

**Q: What does `auto_detect_imports` do?**
A: It parses your entry file's Python AST to find local import statements, then automatically includes those modules in the Docker build context. Useful for simple projects where manual `include` is tedious.

**Q: Is `dockrion deploy` working?**
A: No. It's a placeholder for future controller integration. Use `dockrion build` and deploy the Docker image with your existing tools.

## Policies

**Q: Can prompt injection detection be customized?**
A: Not currently. The `RuntimePolicyEngine` uses a fixed set of regex patterns. Custom patterns may be supported in a future release.

**Q: Does tool gating automatically block tool calls?**
A: Not automatically. The `is_tool_allowed()` API is available for your agent code or framework to check. Automatic interception at the adapter level is planned.

---

**Previous:** [5.8 Troubleshooting](troubleshooting.md) | **Next:** [5.10 Invoice Copilot Walkthrough →](invoice-copilot-walkthrough.md)
