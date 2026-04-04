# 4.3 Auth from the Caller's Perspective

[Home](../../README.md) > [The Generated API](README.md)

This page explains how callers authenticate when consuming your agent's API.

## Which Endpoints Require Auth

When auth is configured in the Dockfile, these endpoints require authentication:

| Requires Auth | Endpoint |
|--------------|----------|
| **Yes** | `POST /invoke`, `POST /invoke/stream`, `POST /runs`, `GET /runs/{id}`, `GET /runs/{id}/events`, `DELETE /runs/{id}` |
| **No** | `GET /health`, `GET /ready`, `GET /metrics`, `GET /schema`, `GET /info`, `GET /docs`, `GET /redoc`, `GET /openapi.json`, `GET /` |

The public endpoints are defined in `PUBLIC_ENDPOINTS = frozenset(["/health", "/ready", "/schema", "/info", "/metrics"])` in `openapi.py`. These never have security requirements in the OpenAPI spec.

## How Auth is Enforced

Auth is **not** middleware — it's a FastAPI dependency. Protected endpoints use `Depends(verify_auth)`, which calls the configured auth handler and converts `AuthError` to HTTP 401/403 responses.

## API Key Mode

### Via Custom Header (default)

```bash
curl -X POST http://localhost:8080/invoke \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "hello"}'
```

The header name is configured by `auth.api_keys.header` (default: `X-API-Key`).

### Via Bearer Token

If `auth.api_keys.allow_bearer` is `true` (default):

```bash
curl -X POST http://localhost:8080/invoke \
  -H "Authorization: Bearer your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "hello"}'
```

Both methods send the same key — the runtime checks the custom header first, then falls back to the Authorization header.

### Error Responses

Missing key:

```json
HTTP 401
{
  "detail": {
    "message": "API key required",
    "code": "AUTH_ERROR"
  }
}
```

Invalid key:

```json
HTTP 401
{
  "detail": {
    "message": "Invalid API key",
    "code": "AUTH_ERROR"
  }
}
```

## JWT Mode

### Via Bearer Token

```bash
curl -X POST http://localhost:8080/invoke \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{"query": "hello"}'
```

The JWT is always passed as a Bearer token in the `Authorization` header.

### Error Responses

Missing token:

```json
HTTP 401
{ "detail": { "message": "Bearer token required", "code": "AUTH_ERROR" } }
```

Invalid/expired token:

```json
HTTP 401
{ "detail": { "message": "JWT validation failed: ...", "code": "AUTH_ERROR" } }
```

## Swagger UI (Try It Out)

When auth is enabled, the Swagger UI at `/docs` shows an **Authorize** button in the top right.

### For API Key mode

1. Click **Authorize**
2. Enter your API key in the `APIKeyHeader` field (for the custom header) or `BearerAuth` field
3. Click **Authorize**
4. Now "Try it out" on any protected endpoint will include the key

### For JWT mode

1. Click **Authorize**
2. Paste your JWT in the `BearerAuth` field
3. Click **Authorize**

### OpenAPI Security Schemes

The runtime generates OpenAPI security schemes based on your auth config:

| Auth mode | Schemes in OpenAPI |
|-----------|-------------------|
| `api_key` | `APIKeyHeader` (custom header) + `BearerAuth` (if `allow_bearer`) |
| `jwt` | `BearerAuth` only |
| `none` | No security schemes |

## No Auth Mode

When `auth.mode` is `none` or the `auth` section is omitted entirely:

- All endpoints are accessible without credentials
- No `Authorize` button appears in Swagger
- `NoAuthHandler` creates `AuthContext.anonymous()` for every request

> **Source:** `verify_auth` closure in `packages/runtime/dockrion_runtime/app.py`; `build_security_schemes()`, `configure_openapi_security()`, `PUBLIC_ENDPOINTS` in `packages/runtime/dockrion_runtime/openapi.py`

---

**Previous:** [4.2 io_schema & Swagger](io-schema-and-swagger.md) | **Next:** [4.4 Streaming Consumption →](streaming-consumption.md)
