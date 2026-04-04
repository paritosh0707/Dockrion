# 2.9 Environment Variable Substitution

[Home](../../README.md) > [The Dockfile](README.md)

Dockrion supports environment variable substitution in Dockfile YAML values, letting you keep secrets and environment-specific config out of your Dockfile.

## Syntax

| Pattern | Behavior |
|---------|----------|
| `${VAR}` | Replaced with the value of environment variable `VAR`. Raises `ValidationError` if not set. |
| `${VAR:-default}` | Replaced with the value of `VAR` if set, otherwise uses `default`. |

Substitution is applied **recursively** to all string values in the parsed YAML — nested dicts, lists, and scalar values are all processed.

## Examples in Dockfile

```yaml
auth:
  api_keys:
    env_var: ${API_KEY_VAR:-DOCKRION_API_KEY}

secrets:
  required:
    - name: OPENAI_API_KEY

streaming:
  redis:
    url: ${REDIS_URL:-redis://localhost:6379}

observability:
  langfuse:
    public_key: ${LANGFUSE_PUBLIC_KEY}
    secret_key: ${LANGFUSE_SECRET_KEY}
```

## How Env Loading Works

Before substitution, Dockrion loads environment variables from multiple sources. The loading happens in `load_dockspec()` via `load_env_files()`:

### File Discovery and Merge Order

```
1. Shell environment (os.environ)         ← highest priority
2. --env-file flag (if provided)          ← explicit override
3. .env file (auto-detected in project)   ← standard dotenv
4. env.yaml / env.yml (if present)        ← YAML format env file
```

Later sources **do not** override earlier ones. Shell environment always wins.

### Auto-detected File Names

| Type | Files checked (in order) |
|------|--------------------------|
| Dotenv | `.env` |
| YAML env | `env.yaml`, `env.yml` |

### YAML Env File Format

```yaml
OPENAI_API_KEY: sk-...
DATABASE_URL: postgresql://localhost/mydb
REDIS_URL: redis://localhost:6379
```

Plain `key: value` pairs. Nested YAML structures are not supported for env files.

## Expansion Flow

```
Dockfile.yaml (raw)
       │
       ▼
yaml.safe_load()  →  Python dict
       │
       ▼
expand_env_vars(data)
  ├── walks dict/list recursively
  ├── for each string value:
  │   ├── finds ${VAR} patterns
  │   ├── looks up VAR in merged env
  │   ├── ${VAR:-default} → uses default if VAR missing
  │   └── ${VAR} with no default → ValidationError if missing
       │
       ▼
DockSpec.model_validate(expanded_data)
```

The `expand_env_vars()` function from `dockrion_sdk` handles this. It processes the entire YAML data structure before Pydantic validation, so substituted values participate in all schema validation rules.

## Common Patterns

### Per-environment secrets

```bash
# .env (development)
OPENAI_API_KEY=sk-dev-key-...
DATABASE_URL=postgresql://localhost/dev_db

# .env.production
OPENAI_API_KEY=sk-prod-key-...
DATABASE_URL=postgresql://prod-host/prod_db
```

```bash
dockrion run --env-file .env.production
```

### Defaults for optional config

```yaml
expose:
  port: ${PORT:-8080}
  host: ${HOST:-0.0.0.0}
```

This lets you override port and host via environment without changing the Dockfile.

> **Source:** `expand_env_vars()` in `packages/sdk-python/dockrion_sdk/client.py`; `load_env_files()` in `packages/common-py/dockrion_common/env_utils.py`

---

**Previous:** [2.8 build config](build-config.md) | **Next:** [2.10 metadata →](metadata.md)
