# OAuth2 Authentication

[Home](../../../README.md) > [The Dockfile](../README.md) > [Auth](README.md)

> **Status: Coming soon.** The `OAuth2Config` schema is defined and validated, but no runtime OAuth2 handler is implemented yet. Setting `mode: oauth2` will not enforce authentication at runtime.

## Planned Design

OAuth2 mode will validate tokens via **token introspection** — your agent calls an external OAuth2 server to verify each access token.

## Schema (accepted today)

```yaml
auth:
  mode: oauth2
  oauth2:
    introspection_url: https://auth.company.com/oauth2/introspect
    client_id_env: OAUTH2_CLIENT_ID
    client_secret_env: OAUTH2_CLIENT_SECRET
    required_scopes:
      - agent:invoke
      - agent:read
```

## Fields (OAuth2Config)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `introspection_url` | `string` | `null` | Token introspection endpoint URL |
| `client_id_env` | `string` | `null` | Env var holding the OAuth2 client ID |
| `client_secret_env` | `string` | `null` | Env var holding the OAuth2 client secret |
| `required_scopes` | `list[str]` | `[]` | Scopes that must be present in the token |

No validation rules beyond basic type checking. All fields are optional at the schema level.

## When It's Available

OAuth2 support is planned for **Phase 2** (noted in the source code docstring). Until then:

- Use `mode: jwt` if your OAuth2 provider issues JWTs (most modern providers do)
- Use `mode: api_key` for simple token-based auth

> **Source:** `OAuth2Config` in `packages/schema/dockrion_schema/dockfile_v1.py`

---

**Previous:** [JWT](jwt.md) | **Next:** [Roles & Rate Limits →](roles-and-rate-limits.md)
