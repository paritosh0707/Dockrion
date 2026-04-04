# 2.11 Complete Annotated Example

[Home](../../README.md) > [The Dockfile](README.md)

A fully-featured Dockfile demonstrating every configuration section. Comments explain each field.

```yaml
# ── Required ────────────────────────────────────────
version: "1.0"

agent:
  name: invoice-copilot
  entrypoint: app.graph:create_graph    # factory function returning compiled LangGraph
  framework: langgraph                   # required for entrypoint mode
  description: "AI copilot for invoice processing and Q&A"

io_schema:
  strict: true                           # validate output against schema
  input:
    type: object
    properties:
      query:
        type: string
        description: "User question or instruction"
      invoice_id:
        type: string
        description: "Optional invoice reference"
    required: [query]
  output:
    type: object
    properties:
      answer:
        type: string
      confidence:
        type: number
      sources:
        type: array
        items:
          type: string

expose:
  rest: true
  streaming: sse                         # enable SSE (default)
  port: 8080
  host: 0.0.0.0
  cors:
    origins: ["https://app.company.com"]
    methods: ["GET", "POST"]

# ── Optional ────────────────────────────────────────

auth:
  mode: api_key
  api_keys:
    env_var: DOCKRION_API_KEY            # env var holding the key
    header: X-API-Key                    # header name callers use
    allow_bearer: true                   # also accept Authorization: Bearer <key>
    prefix: null                         # set for multi-key (e.g., "prod", "staging")
    rotation_days: 30
  roles:
    - name: admin
      permissions: [deploy, invoke, view_metrics, key_manage]
    - name: user
      permissions: [invoke, read_docs]
  rate_limits:
    admin: "5000/hour"
    user: "100/hour"

policies:
  tools:
    allowed: [web_search, calculator, pdf_reader]
    deny_by_default: true                # block any tool not in the allowed list
  safety:
    block_prompt_injection: true         # check input for injection patterns
    redact_patterns:
      - '\b\d{3}-\d{2}-\d{4}\b'        # redact SSN patterns
      - '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    max_output_chars: 50000
    halt_on_violation: false             # silently filter instead of raising errors

secrets:
  required:
    - name: OPENAI_API_KEY
      description: "OpenAI API key for LLM calls"
    - name: DOCKRION_API_KEY
      description: "API key for authenticating callers"
  optional:
    - name: LANGFUSE_PUBLIC_KEY
      description: "Langfuse tracing (optional)"
    - name: LANGFUSE_SECRET_KEY
    - name: REDIS_URL
      description: "Redis URL for production streaming"
      default: "redis://localhost:6379"

streaming:
  async_runs: true                       # enable POST /runs (Pattern B)
  backend: memory                        # memory (dev) or redis (production)
  allow_client_ids: true                 # clients can provide their own run IDs
  events:
    allowed: chat                        # preset: started, token, complete, error
    heartbeat_interval: 15               # seconds between heartbeat events
    max_run_duration: 3600               # 1 hour max per run
  connection:
    default_timeout: 300                 # SSE connection timeout (seconds)
    max_subscribers_per_run: 50

observability:
  log_level: info
  tracing: true
  metrics:
    latency: true
    tokens: true
    cost: false
  langfuse:                              # coming soon — schema accepted but not wired
    public_key: ${LANGFUSE_PUBLIC_KEY}
    secret_key: ${LANGFUSE_SECRET_KEY}

build:
  auto_detect_imports: true              # scan entry file AST for local imports
  include:
    directories:
      - app
      - prompts
    files:
      - config.json
    patterns:
      - "data/*.csv"
  exclude:
    - "__pycache__"
    - "*.pyc"
    - "tests"
    - ".git"

metadata:
  maintainer: "ai-team@company.com"
  version: "1.0.0"
  tags:
    - production
    - invoice
    - langgraph

# ── Forward Compatibility ─────────────────────────
# Unknown fields are preserved (extra="allow" on all models).
# You can add experimental fields without breaking validation:
# custom_field: "my-value"
```

## What This Dockfile Produces

When you run `dockrion build` with this Dockfile:

1. **Schema validation** — all fields checked against `DockSpec` Pydantic models
2. **Secret resolution** — `OPENAI_API_KEY` and `DOCKRION_API_KEY` must be present
3. **Build resolution** — `app/`, `prompts/`, `config.json`, and `data/*.csv` included; `tests/` excluded
4. **Runtime generation** — `main.py`, `requirements.txt`, `Dockerfile` written to `.dockrion_runtime/`
5. **Docker image** — `dockrion/invoice-copilot:dev` built with all dependencies

The resulting API has:

- `/invoke` (POST, auth required) — synchronous invocation
- `/invoke/stream` (POST, auth required) — SSE streaming
- `/runs` (POST, auth required) — async run creation
- `/runs/{id}` (GET, auth required) — run status
- `/runs/{id}/events` (GET, auth required) — SSE event subscription
- `/health`, `/ready`, `/metrics`, `/schema`, `/info` — public endpoints
- `/docs` — Swagger UI with typed request/response models

---

**Previous:** [2.10 metadata](metadata.md) | **Next:** [3. CLI Reference →](../03-cli-reference/README.md)
