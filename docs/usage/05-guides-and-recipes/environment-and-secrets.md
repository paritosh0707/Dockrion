# 5.2 Environment & Secrets Management

[Home](../../README.md) > [Guides & Recipes](README.md)

How environment variables and secrets flow through Dockrion — from `.env` files to your running agent.

## Env File Discovery

When you run `dockrion run` or `dockrion build`, the SDK automatically looks for env files:

| File | Format | Checked |
|------|--------|---------|
| `.env` | `KEY=value` (dotenv) | Always |
| `env.yaml` / `env.yml` | `KEY: value` (YAML) | Always |
| `--env-file <path>` | Either format | When flag is provided |

### Merge Priority (highest wins)

```
1. Shell environment (os.environ)        ← always wins
2. --env-file flag
3. .env file
4. env.yaml / env.yml
```

Later sources **do not** override earlier ones.

## Setting Up Local Development

### Step 1: Create a `.env` file

```bash
# .env
OPENAI_API_KEY=sk-dev-key-...
DOCKRION_API_KEY=my-dev-key
DATABASE_URL=postgresql://localhost/mydb
```

### Step 2: Declare secrets in Dockfile

```yaml
secrets:
  required:
    - name: OPENAI_API_KEY
      description: "OpenAI API key"
    - name: DOCKRION_API_KEY
      description: "API key for callers"
  optional:
    - name: DATABASE_URL
      default: "sqlite:///local.db"
```

### Step 3: Run with env file

```bash
# Auto-detected .env
dockrion run

# Explicit env file
dockrion run --env-file .env.staging
```

## Build Time vs Runtime Secrets

### `dockrion run`

All declared secrets must be resolvable from the environment. Missing required secrets raise `MissingSecretError`.

### `dockrion build`

By default, required secrets must be available for validation. But in CI/CD where production secrets aren't available locally:

```bash
dockrion build --allow-missing-secrets
```

This skips secret validation during build. Secrets are expected to be provided at runtime (via `docker run -e` or orchestrator env injection).

### `dockrion build` with env file

```bash
dockrion build --env-file .env.ci --allow-missing-secrets
```

The env file is used for secret validation only — secrets are **not** baked into the Docker image.

## Resolution Flow

```
Dockfile secrets.required          Shell env + .env files
    │                                     │
    ▼                                     ▼
resolve_secrets(secrets_config, loaded_env, shell_env)
    │
    ▼
For each required secret:
    ├── Found in shell env → use it
    ├── Found in loaded env files → use it
    ├── Has default → use default
    └── Missing → MissingSecretError (if strict)
    
For each optional secret:
    ├── Found → use it
    ├── Has default → use default
    └── Missing → skip (no error)
```

## Debugging

### Verbose mode

```bash
dockrion run --verbose
```

With `--verbose`, the CLI shows an environment summary:

```
Environment Summary:
  Resolved: OPENAI_API_KEY, DOCKRION_API_KEY
  Missing (optional): LANGFUSE_PUBLIC_KEY
  Source: .env (2 vars), shell (1 var)
```

### Common Pitfalls

| Problem | Cause | Fix |
|---------|-------|-----|
| `MissingSecretError: OPENAI_API_KEY` | Not in shell or .env | Add to `.env` or `export` it |
| Secret resolved but wrong value | Shell env overriding `.env` | Check `echo $VAR_NAME` in your shell |
| `.env` not found | Wrong directory | Run from the project root or use `--env-file` |
| YAML env file ignored | Wrong filename | Must be `env.yaml` or `env.yml` (not `environment.yaml`) |

## Docker Runtime Secrets

### `docker run`

```bash
docker run -d \
  -e OPENAI_API_KEY=sk-... \
  -e DOCKRION_API_KEY=my-key \
  -p 8080:8080 \
  dockrion/my-agent:v1.0
```

### Docker Compose

```yaml
services:
  agent:
    image: dockrion/my-agent:v1.0
    ports:
      - "8080:8080"
    env_file:
      - .env.production
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

### Quick Add via CLI

```bash
dockrion add secrets OPENAI_API_KEY,DATABASE_URL
dockrion add secrets LANGFUSE_PUBLIC_KEY --optional
```

> **Source:** `load_env_files()`, `resolve_secrets()`, `validate_secrets()` in `packages/common-py/dockrion_common/env_utils.py`

---

**Previous:** [5.1 Installation](installation.md) | **Next:** [5.3 Adding Auth →](adding-auth.md)
