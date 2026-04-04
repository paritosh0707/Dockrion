# 5.8 Troubleshooting

[Home](../../README.md) > [Guides & Recipes](README.md)

## `dockrion doctor`

Run diagnostics to quickly identify common issues:

```bash
dockrion doctor
```

### What Each Check Does

| Check | Tests | Fix if it fails |
|-------|-------|-----------------|
| Docker | `docker --version` runs successfully | Install Docker Desktop or Docker Engine |
| Dockfile | `Dockfile.yaml` exists in current directory | Run `dockrion init` or `cd` to the right directory |
| Validation | `validate_dockspec()` passes | Fix the validation errors reported |
| Packages | Core packages importable | Reinstall with `pip install dockrion[all]` |

Doctor always exits 0 — it reports results but doesn't fail.

## Common Errors

### `ValidationError` (Schema)

```
Error: Validation failed:
  agent.name: must match pattern ^[a-z][a-z0-9-]*$
```

**Cause:** Dockfile field doesn't meet schema requirements.

**Fix:** Check the field rules in the [Dockfile reference](../02-the-dockfile/README.md). Common issues:
- Agent name has uppercase letters or spaces
- `entrypoint` or `handler` missing the `:` separator
- Invalid framework value
- Rate limit format wrong (should be `count/window`)

### `MissingSecretError`

```
Error: Missing required secrets: OPENAI_API_KEY, DATABASE_URL
```

**Cause:** Required secrets declared in Dockfile but not found in environment or `.env` file.

**Fix:**
- Add them to your `.env` file
- Or `export` them in your shell
- Or use `--env-file` to point to the right file
- For builds: use `--allow-missing-secrets` if secrets aren't available locally

### `AdapterLoadError` / `ModuleNotFoundError`

```
Error: Failed to load adapter: Module 'app.graph' not found
```

**Cause:** The module path in `agent.entrypoint` or `agent.handler` can't be imported.

**Fix:**
- Check the module path matches your file structure: `app.graph:create_graph` → `app/graph.py` with function `create_graph`
- Ensure you're running from the project root directory
- Check that `__init__.py` exists in packages if needed
- Verify the function/class exists in the module

### Docker Build Failures

```
Error: Docker build failed
```

**Common causes and fixes:**

| Cause | Fix |
|-------|-----|
| Docker not running | Start Docker Desktop or Docker daemon |
| Missing files in build context | Add them to `build.include` |
| Dependency conflicts | Check `requirements.txt` for version conflicts |
| Network issues during pip install | Retry or use `--no-cache` |

### Auth Errors at Runtime

```
HTTP 401: {"detail": {"message": "API key required", "code": "AUTH_ERROR"}}
```

**Fix:** Include the correct auth header:
- API key mode: `X-API-Key: your-key` or `Authorization: Bearer your-key`
- JWT mode: `Authorization: Bearer <jwt-token>`

### "Agent not ready" on `GET /ready`

```
HTTP 503: {"status": "not_ready"}
```

**Cause:** The agent adapter hasn't finished loading yet, or loading failed.

**Fix:**
- Wait a few seconds (agent loading can take time, especially for LangGraph)
- Check logs for import errors
- Verify the entrypoint/handler module is accessible

### Port Already in Use

```
Error: [Errno 98] Address already in use
```

**Fix:** Use a different port with `--port 3000`, or kill the process using port 8080:

```bash
lsof -i :8080 | grep LISTEN
kill <PID>
```

## Error Hierarchy

All Dockrion errors extend `DockrionError` from `dockrion_common`:

| Error Class | Code | When |
|------------|------|------|
| `DockrionError` | `INTERNAL_ERROR` | Base class |
| `ValidationError` | `VALIDATION_ERROR` | Schema/input validation failures |
| `AuthError` | `AUTH_ERROR` | Authentication failures |
| `RateLimitError` | `RATE_LIMIT_EXCEEDED` | Rate limit exceeded |
| `NotFoundError` | `NOT_FOUND` | Resource not found |
| `ConflictError` | `CONFLICT` | Conflicting state |
| `ServiceUnavailableError` | `SERVICE_UNAVAILABLE` | Service not available |
| `DeploymentError` | `DEPLOYMENT_ERROR` | Build/deploy failures |
| `PolicyViolationError` | `POLICY_VIOLATION` | Safety policy violations |
| `MissingSecretError` | `MISSING_SECRET` | Required secrets not found |
| `BuildConflictError` | `BUILD_CONFLICT` | Dependency conflicts during build |

Adapter-specific errors (from `dockrion_adapters`):

| Error Class | Code | When |
|------------|------|------|
| `AdapterLoadError` | `ADAPTER_LOAD_ERROR` | Failed to load agent |
| `ModuleNotFoundError` | `MODULE_NOT_FOUND` | Import failure |
| `CallableNotFoundError` | `CALLABLE_NOT_FOUND` | Function/class not in module |
| `InvalidAgentError` | `INVALID_AGENT` | Wrong agent shape |
| `AgentExecutionError` | `AGENT_EXECUTION_ERROR` | Agent threw during invocation |
| `AgentCrashedError` | `AGENT_CRASHED` | Unexpected agent crash |
| `InvalidOutputError` | `INVALID_OUTPUT` | Agent returned non-dict |

All errors have a `to_dict()` method that returns `{"message": "...", "code": "..."}`.

---

**Previous:** [5.7 Cloud Deployment](cloud-deployment.md) | **Next:** [5.9 FAQ →](faq.md)
