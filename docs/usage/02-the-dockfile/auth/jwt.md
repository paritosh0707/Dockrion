# JWT Authentication

[Home](../../../README.md) > [The Dockfile](../README.md) > [Auth](README.md)

JWT mode validates JSON Web Tokens from an external identity provider. It supports JWKS URL discovery and static public key verification.

## Prerequisites

JWT auth requires the `PyJWT` library:

```bash
pip install dockrion[jwt]
```

If `PyJWT` is not installed and `mode: jwt` is configured, the runtime falls back to `NoAuthHandler` with a warning.

## Dockfile Configuration

```yaml
auth:
  mode: jwt
  jwt:
    jwks_url: https://your-idp.com/.well-known/jwks.json
    issuer: https://your-idp.com/
    audience: my-agent-api
    algorithms: [RS256]
    leeway_seconds: 30
    claims:
      user_id: sub
      email: email
      name: name
      roles: roles
      permissions: permissions
      scopes: scope
      tenant_id: custom.tenant_id
```

## Fields

### JWTConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `jwks_url` | `string` | `null` | URL to JWKS endpoint for public key discovery |
| `public_key_env` | `string` | `null` | Environment variable holding a static PEM public key (alternative to JWKS) |
| `issuer` | `string` | `null` | Expected `iss` claim value. If set, tokens with a different issuer are rejected. |
| `audience` | `string` | `null` | Expected `aud` claim value. If set, tokens for a different audience are rejected. |
| `algorithms` | `list[str]` | `["RS256"]` | Allowed JWT signing algorithms |
| `leeway_seconds` | `int` | `30` | Clock skew tolerance for `exp`/`nbf` claims (0–300) |
| `claims` | `JWTClaimsConfig` | `null` | Maps JWT claim names to Dockrion identity fields |

### JWTClaimsConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `user_id` | `string` | `"sub"` | JWT claim for user ID |
| `email` | `string` | `"email"` | JWT claim for email |
| `name` | `string` | `"name"` | JWT claim for display name |
| `roles` | `string` | `"roles"` | JWT claim containing role list |
| `permissions` | `string` | `"permissions"` | JWT claim containing permissions |
| `scopes` | `string` | `"scope"` | JWT claim for OAuth2 scopes |
| `tenant_id` | `string` | `null` | JWT claim for tenant ID (supports dot paths like `custom.tenant_id`) |

Claims support **dot paths** for nested JWT structures. For example, `custom.tenant_id` reads the `tenant_id` field inside a `custom` object in the JWT payload.

### Supported Algorithms

| Algorithm | Family |
|-----------|--------|
| `RS256`, `RS384`, `RS512` | RSA |
| `ES256`, `ES384`, `ES512` | Elliptic Curve |
| `HS256`, `HS384`, `HS512` | HMAC (symmetric) |

## How It Works at Runtime

The `JWTAuthHandler` processes each request:

1. Extracts the token from `Authorization: Bearer <token>`
2. If `jwks_url` is set, fetches public keys from the JWKS endpoint
3. If `public_key_env` is set, reads the PEM key from the environment variable
4. Decodes and validates the JWT (signature, expiration, issuer, audience)
5. Maps claims to an `AuthContext` via `AuthContext.from_jwt()`
6. On failure → raises `AuthError` (HTTP 401)

## Key Source: JWKS vs Static Key

### JWKS URL (recommended for production)

```yaml
auth:
  mode: jwt
  jwt:
    jwks_url: https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys
    algorithms: [RS256]
```

The runtime fetches keys from the JWKS endpoint. Key rotation is handled automatically by the identity provider.

### Static Public Key (simpler, for testing)

```yaml
auth:
  mode: jwt
  jwt:
    public_key_env: JWT_PUBLIC_KEY
    algorithms: [RS256]
```

```bash
export JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\nMIIB..."
```

## Testing with curl

```bash
# Generate a test token (example using jwt.io or a script)
TOKEN="eyJhbGciOiJSUzI1NiIs..."

curl -X POST http://localhost:8080/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "hello"}'
```

## Combining JWT with Roles

JWT claims can carry role information that maps to Dockrion roles:

```yaml
auth:
  mode: jwt
  jwt:
    jwks_url: https://your-idp.com/.well-known/jwks.json
    claims:
      roles: realm_access.roles   # dot path into JWT payload
  roles:
    - name: admin
      permissions: [deploy, invoke, view_metrics]
    - name: user
      permissions: [invoke]
```

See [Roles & Rate Limits](roles-and-rate-limits.md) for more on RBAC.

> **Source:** `JWTConfig`, `JWTClaimsConfig` in `packages/schema/dockrion_schema/dockfile_v1.py`; `JWTAuthHandler` in `packages/runtime/dockrion_runtime/auth/jwt_handler.py`

---

**Previous:** [API Key](api-key.md) | **Next:** [OAuth2 →](oauth2.md)
