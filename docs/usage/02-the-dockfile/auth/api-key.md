# API Key Authentication

[Home](../../../README.md) > [The Dockfile](../README.md) > [Auth](README.md)

API key mode is the default and simplest authentication mode. Callers pass a static key in an HTTP header or as a Bearer token.

## Dockfile Configuration

```yaml
auth:
  mode: api_key
  api_keys:
    env_var: DOCKRION_API_KEY
    header: X-API-Key
    allow_bearer: true
    prefix: null
    enabled: true
    rotation_days: 30
```

## Fields (ApiKeysConfig)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `env_var` | `string` | `"DOCKRION_API_KEY"` | Name of the environment variable holding the API key |
| `prefix` | `string` | `null` | Key prefix for multi-key setups (e.g., `"prod"`, `"staging"`) |
| `header` | `string` | `"X-API-Key"` | HTTP header name where callers send the key. Must be non-empty, max 64 chars. |
| `allow_bearer` | `bool` | `true` | Also accept the key via `Authorization: Bearer <key>` header |
| `enabled` | `bool` | `true` | Whether API key auth is active |
| `rotation_days` | `int` | `30` | Recommended key rotation period (informational; not enforced by runtime) |

## How It Works at Runtime

The `ApiKeyAuthHandler` (in `dockrion_runtime/auth/`) handles authentication:

1. Extracts the key from the configured header (e.g., `X-API-Key`)
2. If not found and `allow_bearer` is `true`, checks `Authorization: Bearer <key>`
3. Compares the provided key against the expected key from the environment variable
4. On match → creates `AuthContext` with identity info
5. On mismatch → raises `AuthError` (HTTP 401)

## Single Key Setup

The simplest configuration:

```yaml
auth:
  mode: api_key
  api_keys:
    env_var: DOCKRION_API_KEY
```

Set the environment variable:

```bash
export DOCKRION_API_KEY="my-secret-key-123"
```

Test with curl:

```bash
# Via custom header (default)
curl -X POST http://localhost:8080/invoke \
  -H "X-API-Key: my-secret-key-123" \
  -H "Content-Type: application/json" \
  -d '{"query": "hello"}'

# Via Bearer token (allow_bearer: true)
curl -X POST http://localhost:8080/invoke \
  -H "Authorization: Bearer my-secret-key-123" \
  -H "Content-Type: application/json" \
  -d '{"query": "hello"}'
```

## Multi-Key Setup with Prefix

For managing separate keys per environment or team, use the `prefix` field:

```yaml
auth:
  mode: api_key
  api_keys:
    env_var: API_KEY
    prefix: prod
```

With `prefix: prod`, the runtime looks for `PROD_API_KEY` (prefix uppercased + `_API_KEY`). You can deploy the same Dockfile with different prefixes for different environments.

## Custom Header

```yaml
auth:
  mode: api_key
  api_keys:
    header: X-Custom-Auth
    allow_bearer: false
```

This only accepts the key via the `X-Custom-Auth` header. Bearer token auth is disabled.

## Swagger UI

When API key mode is enabled, the Swagger UI at `/docs` shows an "Authorize" button. Click it and enter your API key to test authenticated endpoints.

The OpenAPI spec includes a `SecurityScheme` with:
- `APIKeyHeader` — for the configured header
- `BearerAuth` — if `allow_bearer` is `true`

> **Source:** `ApiKeysConfig` in `packages/schema/dockrion_schema/dockfile_v1.py`; `ApiKeyAuthHandler` in `packages/runtime/dockrion_runtime/auth/api_key.py`

---

**Up:** [Auth Overview](README.md) | **Next:** [JWT →](jwt.md)
