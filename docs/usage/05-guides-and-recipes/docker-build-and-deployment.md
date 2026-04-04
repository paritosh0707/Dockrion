# 5.6 Docker Build & Deployment

[Home](../../README.md) > [Guides & Recipes](README.md)

How to build a Docker image from your Dockfile and run it.

## Build Workflow

```
dockrion build
     │
     ├── 1. Load and validate Dockfile
     ├── 2. Check secrets (or --allow-missing-secrets)
     ├── 3. Generate runtime files
     │      ├── main.py         (FastAPI app from Jinja2 template)
     │      ├── requirements.txt (merged: your deps + Dockrion's deps)
     │      └── Dockerfile       (multi-stage build from template)
     ├── 4. Resolve build context
     │      ├── auto_detect_imports → AST scan of entry file
     │      ├── build.include → explicit dirs/files/patterns
     │      └── build.exclude → filter out unwanted files
     └── 5. docker build → dockrion/{agent-name}:{tag}
```

## Running a Build

### Basic Build

```bash
dockrion build
```

Creates image `dockrion/my-agent:dev`.

### Production Build

```bash
dockrion build --tag v1.0.0 --no-cache
```

### CI/CD Build (secrets not available)

```bash
dockrion build --tag $CI_COMMIT_SHA --allow-missing-secrets
```

### With Env File

```bash
dockrion build --env-file .env.production --tag production
```

## Generated Files

The build process creates `.dockrion_runtime/`:

```
.dockrion_runtime/
├── main.py              FastAPI application entry point
├── requirements.txt     Merged dependencies
├── Dockerfile           Docker build instructions
└── (agent source files) Copied from your project
```

### main.py

The generated `main.py` imports Dockrion packages, loads the DockSpec, creates the FastAPI app via `create_app()`, and configures uvicorn. It's rendered from a Jinja2 template in the SDK.

### requirements.txt

The `DependencyMerger` combines:

- Your project's `requirements.txt` (if present)
- Dockrion's core, runtime, and framework dependencies
- Optional dependencies (e.g., `prometheus-client`, `PyJWT`)

Conflicts are resolved with a precedence system: user constraints can override Dockrion's defaults for non-core packages.

### Dockerfile

The generated Dockerfile follows a standard pattern:

1. `FROM python:3.11-slim` base image
2. Install system dependencies
3. Copy `requirements.txt` and install Python packages
4. Copy application source files
5. Set the entrypoint to run `main.py` via uvicorn

## Image Naming

```
dockrion/{agent-name}:{tag}
```

| Component | Source | Default |
|-----------|--------|---------|
| Prefix | `DOCKRION_IMAGE_PREFIX` constant | `dockrion` |
| Agent name | `agent.name` from Dockfile | — |
| Tag | `--tag` flag | `dev` |

Example: `dockrion/invoice-copilot:v1.0.0`

## Running the Image

### Basic Run

```bash
docker run -d \
  -p 8080:8080 \
  -e OPENAI_API_KEY=sk-... \
  dockrion/my-agent:dev
```

### With Environment Variables

```bash
docker run -d \
  -p 8080:8080 \
  -e OPENAI_API_KEY=sk-... \
  -e DOCKRION_API_KEY=my-key \
  -e LOG_LEVEL=debug \
  dockrion/my-agent:v1.0.0
```

### With an Env File

```bash
docker run -d \
  -p 8080:8080 \
  --env-file .env.production \
  dockrion/my-agent:v1.0.0
```

### Health Check

```bash
docker run -d \
  -p 8080:8080 \
  --health-cmd "curl -f http://localhost:8080/health || exit 1" \
  --health-interval 30s \
  --env-file .env \
  dockrion/my-agent:v1.0.0
```

## Docker Compose

```yaml
version: "3.8"
services:
  agent:
    image: dockrion/my-agent:v1.0.0
    ports:
      - "8080:8080"
    env_file:
      - .env.production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

> **Source:** `deploy()` in `packages/sdk-python/dockrion_sdk/`; `TemplateRenderer`, `TemplateContext` in `packages/sdk-python/dockrion_sdk/templates/`

---

**Previous:** [5.5 Adding Policies](adding-policies.md) | **Next:** [5.7 Cloud Deployment →](cloud-deployment.md)
