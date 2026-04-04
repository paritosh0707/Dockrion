# 2.5 secrets

[Home](../../README.md) > [The Dockfile](README.md)

The `secrets` section declares environment variables your agent needs at runtime. Dockrion validates their presence during `run` and `build`, catching missing secrets before deployment.

## Fields

### SecretsConfig (root `secrets` key)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `required` | `list[SecretDefinition]` | `[]` | Secrets that **must** be present. Missing required secrets cause an error. |
| `optional` | `list[SecretDefinition]` | `[]` | Secrets that are used if present but not required |

### SecretDefinition

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `string` | *(required)* | Environment variable name. Must match `^[A-Z_][A-Z0-9_]*$` (UPPER_SNAKE_CASE). |
| `description` | `string` | `null` | What this secret is for (documentation only) |
| `default` | `string` | `null` | Default value if the variable is not set |

## Validation Rules

1. **Naming:** Secret names must be UPPER_SNAKE_CASE, starting with a letter or underscore. Examples: `OPENAI_API_KEY`, `DATABASE_URL`, `_INTERNAL_TOKEN`.
2. **Uniqueness:** No duplicate names across both `required` and `optional` lists. The `validate_no_duplicate_names` model validator enforces this.
3. **Non-empty:** Secret names must be non-empty after trimming whitespace.

## How Secrets Are Resolved

When you run `dockrion run` or `dockrion build`, the SDK resolves secrets in this order:

1. **Shell environment** — `os.environ`
2. **`.env` file** — auto-detected in the project directory
3. **`env.yaml` / `env.yml`** — YAML-format env files
4. **`--env-file` flag** — explicitly specified env file

The `resolve_secrets()` function from `dockrion_common.env_utils` merges these sources. Required secrets that cannot be found raise a `MissingSecretError`.

## Strict vs Non-Strict Mode

| Scenario | Behavior |
|----------|----------|
| `dockrion run` | Missing required secrets → error (strict by default) |
| `dockrion build` | Missing required secrets → error unless `--allow-missing-secrets` is passed |
| `dockrion build --allow-missing-secrets` | Warnings for missing secrets but build continues |
| `dockrion test` | Secrets are resolved from env; missing secrets may cause runtime errors |

The SDK's `load_dockspec()` accepts `strict_secrets` and `validate_secrets` parameters that control this behavior programmatically.

## Example

```yaml
secrets:
  required:
    - name: OPENAI_API_KEY
      description: "OpenAI API key for LLM calls"
    - name: DATABASE_URL
      description: "PostgreSQL connection string"
  optional:
    - name: LANGFUSE_PUBLIC_KEY
      description: "Langfuse tracing public key"
    - name: REDIS_URL
      description: "Redis URL for streaming backend"
      default: "redis://localhost:6379"
```

In this example, `OPENAI_API_KEY` and `DATABASE_URL` must be set. `LANGFUSE_PUBLIC_KEY` is optional (no error if missing). `REDIS_URL` has a default value that's used when the variable is not set.

## Quick Add via CLI

```bash
dockrion add secrets OPENAI_API_KEY,DATABASE_URL
dockrion add secrets LANGFUSE_PUBLIC_KEY --optional
```

This merges new secrets into your existing Dockfile. See [CLI: add secrets](../03-cli-reference/utility-commands.md) for details.

> **Source:** `SecretsConfig`, `SecretDefinition` in `packages/schema/dockrion_schema/dockfile_v1.py`; `resolve_secrets()`, `validate_secrets()` in `packages/common-py/dockrion_common/env_utils.py`

---

**Previous:** [2.4 Policies](policies/README.md) | **Next:** [2.6 Streaming →](streaming/README.md)
