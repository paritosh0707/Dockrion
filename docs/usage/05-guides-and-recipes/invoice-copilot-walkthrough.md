# 5.10 Walkthrough: Invoice Copilot

[Home](../../README.md) > [Guides & Recipes](README.md)

A guided tutorial building a complete agent that demonstrates most Dockrion features: LangGraph entrypoint mode, authentication, streaming, secrets, policies, and observability.

## What We're Building

An AI copilot that processes invoices and answers questions about them. It uses:

- LangGraph for the agent graph
- API key authentication
- SSE streaming with the `chat` preset
- Secrets for the OpenAI key
- Output redaction for PII
- Prometheus metrics

## 1. The Dockfile (`Dockfile.yaml`)

```yaml
version: "1.0"

agent:
  name: invoice-copilot
  entrypoint: app.graph:create_graph
  framework: langgraph
  description: "AI copilot for invoice processing"

io_schema:
  strict: true
  input:
    type: object
    properties:
      query:
        type: string
        description: "Question or instruction about invoices"
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
  streaming: sse
  port: 8080
  cors:
    origins: ["http://localhost:3000"]
    methods: ["GET", "POST"]

auth:
  mode: api_key
  api_keys:
    env_var: DOCKRION_API_KEY
    header: X-API-Key
    allow_bearer: true
  roles:
    - name: admin
      permissions: [deploy, invoke, view_metrics]
    - name: user
      permissions: [invoke]
  rate_limits:
    admin: "5000/hour"
    user: "200/hour"

policies:
  tools:
    allowed: [invoice_lookup, calculator]
    deny_by_default: true
  safety:
    block_prompt_injection: true
    redact_patterns:
      - '\b\d{3}-\d{2}-\d{4}\b'
    max_output_chars: 20000

secrets:
  required:
    - name: OPENAI_API_KEY
      description: "OpenAI API key"
    - name: DOCKRION_API_KEY
      description: "API key for callers"
  optional:
    - name: LANGFUSE_PUBLIC_KEY
    - name: LANGFUSE_SECRET_KEY

streaming:
  async_runs: false
  backend: memory
  events:
    allowed: chat
    heartbeat_interval: 15

observability:
  log_level: info
  tracing: true
  metrics:
    latency: true
    tokens: true

build:
  auto_detect_imports: true
  include:
    directories: [app]
  exclude:
    - tests
    - __pycache__

metadata:
  maintainer: "ai-team@company.com"
  version: "1.0.0"
  tags: [production, invoice, langgraph]
```

## 2. Handler Code (`app/service.py`)

Even in entrypoint mode, you might have helper functions:

```python
import os

def get_openai_client():
    from openai import OpenAI
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def lookup_invoice(invoice_id: str) -> dict:
    # In production, query your database
    return {
        "id": invoice_id,
        "amount": 1500.00,
        "vendor": "Acme Corp",
        "status": "pending"
    }
```

## 3. Graph Code (`app/graph.py`)

```python
from langgraph.graph import StateGraph, END
from app.service import get_openai_client, lookup_invoice

class InvoiceState(dict):
    pass

def process_query(state: InvoiceState) -> InvoiceState:
    query = state.get("query", "")
    invoice_id = state.get("invoice_id")
    
    context = ""
    sources = []
    
    if invoice_id:
        invoice = lookup_invoice(invoice_id)
        context = f"Invoice {invoice['id']}: ${invoice['amount']} from {invoice['vendor']} ({invoice['status']})"
        sources.append(f"invoice:{invoice_id}")
    
    client = get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": f"You are an invoice processing assistant. Context: {context}"},
            {"role": "user", "content": query}
        ]
    )
    
    state["answer"] = response.choices[0].message.content
    state["confidence"] = 0.9
    state["sources"] = sources
    return state

def create_graph():
    graph = StateGraph(InvoiceState)
    graph.add_node("process", process_query)
    graph.set_entry_point("process")
    graph.add_edge("process", END)
    return graph.compile()
```

## 4. Local Environment (`.env`)

```bash
OPENAI_API_KEY=sk-your-openai-key
DOCKRION_API_KEY=my-dev-key-123
```

## 5. Validate, Run, and Invoke

```bash
# Validate the Dockfile
dockrion validate
# ✓ Dockfile is valid
#   Agent: invoice-copilot
#   Mode: entrypoint (app.graph:create_graph)
#   Framework: langgraph

# Start the server
dockrion run

# Invoke (synchronous)
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: my-dev-key-123" \
  -d '{"query": "What is the status of invoice #1234?", "invoice_id": "1234"}'

# Invoke (streaming)
curl -N -X POST http://localhost:8080/invoke/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: my-dev-key-123" \
  -d '{"query": "Summarize all pending invoices"}'

# Check health
curl http://localhost:8080/health

# Check metrics
curl http://localhost:8080/metrics
```

## 6. Key Features Recap

| Feature | How it's configured | What it does |
|---------|-------------------|-------------|
| LangGraph | `entrypoint` + `framework: langgraph` | Factory function returns compiled graph |
| Auth | `auth.mode: api_key` | `X-API-Key` header required on `/invoke` |
| Streaming | `expose.streaming: sse` | `POST /invoke/stream` returns SSE events |
| Secrets | `secrets.required` | `OPENAI_API_KEY` validated before run/build |
| Redaction | `policies.safety.redact_patterns` | SSN patterns replaced with `[REDACTED]` |
| Injection blocking | `policies.safety.block_prompt_injection` | Malicious prompts rejected |
| Tool gating | `policies.tools.allowed` | Only `invoice_lookup` and `calculator` allowed |
| Metrics | `observability.metrics` | Prometheus at `/metrics` |
| Swagger | `io_schema` types | Typed request/response at `/docs` |

## 7. Build for Deployment

```bash
# Build Docker image
dockrion build --tag v1.0.0

# Run the image
docker run -d \
  -p 8080:8080 \
  -e OPENAI_API_KEY=sk-prod-key \
  -e DOCKRION_API_KEY=prod-key-456 \
  dockrion/invoice-copilot:v1.0.0
```

---

**Previous:** [5.9 FAQ](faq.md) | **Next:** [Appendix →](../appendix/README.md)
