# 2.3 Authentication

[Home](../../README.md) > [The Dockfile](../README.md) > Auth

Dockrion supports multiple authentication modes for protecting your agent's API. The `auth` section in the Dockfile configures how callers prove their identity.

## Auth Mode Comparison

| Mode | Config key | Status | Best for |
|------|-----------|--------|----------|
| `none` | `mode: none` | Implemented | Internal/dev agents with no auth needed |
| `api_key` | `mode: api_key` | Implemented | Simple deployments, single or multi-key setups |
| `jwt` | `mode: jwt` | Implemented | Enterprise SSO, external identity providers |
| `oauth2` | `mode: oauth2` | **Coming soon** | Token introspection via external OAuth2 server |

The default mode is `api_key`. If you omit the `auth` section entirely, no authentication middleware is applied (same as `mode: none`).

## Decision Guide

- **Just getting started?** Skip auth or use `mode: none`. You can always add it later with `dockrion add auth`.
- **Deploying to production?** Use `mode: api_key` for simplicity, or `mode: jwt` if you already have an identity provider.
- **Multiple teams or roles?** Define `roles` and `rate_limits` under auth, regardless of mode.

## In This Section

| Page | What it covers |
|------|----------------|
| [API Key](api-key.md) | `env_var`, `header`, `prefix`, `allow_bearer`, multi-key setup |
| [JWT](jwt.md) | JWKS, static public key, claims mapping, algorithms |
| [OAuth2](oauth2.md) | Token introspection *(coming soon)* |
| [Roles & Rate Limits](roles-and-rate-limits.md) | Role definitions, permissions, rate limit syntax |

## Dockfile Structure

```yaml
auth:
  mode: api_key          # or: none, jwt, oauth2
  api_keys:              # only relevant when mode: api_key
    env_var: DOCKRION_API_KEY
    header: X-API-Key
    allow_bearer: true
  jwt:                   # only relevant when mode: jwt
    jwks_url: https://...
    algorithms: [RS256]
  roles:                 # works with any mode
    - name: admin
      permissions: [deploy, invoke, view_metrics]
  rate_limits:           # per-role rate limits
    admin: "1000/hour"
    default: "100/hour"
```

> **Source:** `AuthConfig` in `packages/schema/dockrion_schema/dockfile_v1.py`

---

**Up:** [The Dockfile](../README.md) | **Next:** [2.4 Policies →](../policies/README.md)
