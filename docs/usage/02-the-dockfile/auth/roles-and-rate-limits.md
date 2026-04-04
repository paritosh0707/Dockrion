# Roles & Rate Limits

[Home](../../../README.md) > [The Dockfile](../README.md) > [Auth](README.md)

Roles and rate limits work with **any** auth mode (api_key, jwt, or oauth2). They define what authenticated users can do and how often.

## Roles

### Defining Roles

```yaml
auth:
  mode: api_key
  roles:
    - name: admin
      permissions: [deploy, rollback, invoke, view_metrics, key_manage, read_logs, read_docs]
    - name: developer
      permissions: [invoke, view_metrics, read_logs, read_docs]
    - name: viewer
      permissions: [read_docs, view_metrics]
```

### RoleConfig Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **Yes** | Role identifier |
| `permissions` | `list[str]` | **Yes** | Permissions granted to this role |

### Available Permissions

Every permission value is validated against this fixed set:

| Permission | Description |
|-----------|-------------|
| `deploy` | Deploy or update agents |
| `rollback` | Roll back to a previous version |
| `invoke` | Call the agent's `/invoke` endpoint |
| `view_metrics` | Access `/metrics` and observability data |
| `key_manage` | Manage API keys |
| `read_logs` | Access agent logs |
| `read_docs` | Access Swagger UI and documentation |

Using a permission value not in this list causes a `ValidationError`.

### How Roles Are Checked

The `dockrion_common.auth_utils` module provides permission-checking functions:

| Function | Behavior |
|----------|----------|
| `check_permission(user_perms, required)` | Returns `true` if `required` is in `user_perms` |
| `check_any_permission(user_perms, required_list)` | Returns `true` if the user has **any** of the required permissions |
| `check_all_permissions(user_perms, required_list)` | Returns `true` if the user has **all** of the required permissions |

> **Note:** In v1.0, role-based authorization is validated at the schema level but **not enforced by the runtime middleware**. The `AuthContext` carries role/permission data for future enforcement and for your agent code to use.

## Rate Limits

### Configuration

```yaml
auth:
  rate_limits:
    admin: "5000/hour"
    developer: "500/hour"
    default: "100/hour"
```

Rate limits are defined as `role_name: "count/window"` pairs.

### Syntax

The format is `<count>/<window>` where:

| Component | Type | Examples |
|-----------|------|---------|
| `count` | positive integer | `100`, `5000` |
| `window` | time unit | `second`, `minute`, `hour`, `day` |

Examples: `"100/hour"`, `"10/second"`, `"1000/day"`, `"50/minute"`

The `parse_rate_limit()` function from `dockrion_common` validates this format. Invalid formats raise a `ValidationError` with the role name in the error message.

### Current Status

> **Rate limit enforcement is scaffolded but not yet wired into the runtime.** The schema validates rate limit syntax, and the `AuthConfig` stores the parsed values, but no middleware currently counts or rejects requests based on rate limits. This is planned for a future release.

## Combined Example

```yaml
auth:
  mode: jwt
  jwt:
    jwks_url: https://auth.company.com/.well-known/jwks.json
    claims:
      roles: realm_access.roles
  roles:
    - name: admin
      permissions: [deploy, invoke, view_metrics, key_manage]
    - name: service
      permissions: [invoke]
    - name: readonly
      permissions: [view_metrics, read_docs]
  rate_limits:
    admin: "10000/hour"
    service: "1000/hour"
    readonly: "500/hour"
```

> **Source:** `RoleConfig` in `packages/schema/dockrion_schema/dockfile_v1.py`; `PERMISSIONS` in `packages/common-py/dockrion_common/constants.py`; `parse_rate_limit()` in `packages/common-py/dockrion_common/validation.py`

---

**Previous:** [OAuth2](oauth2.md) | **Up:** [Auth Overview](README.md)
