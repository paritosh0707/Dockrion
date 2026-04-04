# 1.4 Quickstart

[Home](../../README.md) > [Introduction](README.md)

Two tutorials to get your first Dockrion agent running in under 5 minutes.

## Prerequisites

- Python 3.11+
- pip (or uv)
- Docker (for `dockrion build` only)

```bash
pip install dockrion
```

See [Installation & Extras](../05-guides-and-recipes/installation.md) for optional packages.

---

## Tutorial A: Handler Mode (Simplest Path)

### Step 1: Initialize the Project

```bash
mkdir my-agent && cd my-agent
dockrion init my-agent --handler
```

This creates a `Dockfile.yaml` pre-configured for handler mode with `framework: custom`.

### Step 2: Write Your Handler

Create `app/service.py`:

```python
def handle(payload: dict) -> dict:
    query = payload.get("query", "")
    return {"answer": f"Echo: {query}"}
```

Update `Dockfile.yaml` to point to your handler:

```yaml
version: "1.0"
agent:
  name: my-agent
  handler: app.service:handle
io_schema:
  input:
    type: object
    properties:
      query:
        type: string
    required: [query]
  output:
    type: object
    properties:
      answer:
        type: string
expose:
  rest: true
  streaming: none
```

### Step 3: Validate

```bash
dockrion validate
```

Expected output:

```
✓ Dockfile is valid
  Agent: my-agent
  Mode: handler (app.service:handle)
  Framework: custom
```

### Step 4: Run the Server

```bash
dockrion run
```

The server starts on `http://0.0.0.0:8080`. You'll see uvicorn startup logs.

### Step 5: Call Your Agent

```bash
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"query": "hello"}'
```

Response:

```json
{
  "success": true,
  "output": { "answer": "Echo: hello" },
  "metadata": {}
}
```

### Step 6: Explore the Swagger UI

Open `http://localhost:8080/docs` in your browser. You'll see all endpoints, with the `/invoke` request body shaped by your `io_schema`.

---

## Tutorial B: Entrypoint Mode (LangGraph)

### Step 1: Initialize

```bash
pip install dockrion[langgraph]
mkdir my-graph-agent && cd my-graph-agent
dockrion init my-graph-agent --framework langgraph
```

### Step 2: Write Your Graph Factory

Create `app/graph.py`:

```python
from langgraph.graph import StateGraph, END

def create_graph():
    class State(dict):
        pass

    def process(state):
        query = state.get("query", "")
        state["answer"] = f"Processed: {query}"
        return state

    graph = StateGraph(State)
    graph.add_node("process", process)
    graph.set_entry_point("process")
    graph.add_edge("process", END)
    return graph.compile()
```

Update `Dockfile.yaml`:

```yaml
version: "1.0"
agent:
  name: my-graph-agent
  entrypoint: app.graph:create_graph
  framework: langgraph
io_schema:
  input:
    type: object
    properties:
      query:
        type: string
  output:
    type: object
expose:
  rest: true
```

### Step 3: Validate, Run, and Test

```bash
dockrion validate
dockrion run
```

```bash
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"query": "hello from langgraph"}'
```

### Key Difference from Handler Mode

In entrypoint mode, `create_graph()` is called **once** at startup. The returned compiled graph's `.invoke()` method handles each request. In handler mode, your function is called **directly** for every request.

---

## Quick Test Without a Server

To invoke your agent without starting an HTTP server:

```bash
dockrion test -p '{"query": "quick test"}'
```

This uses `invoke_local()` from the SDK — it loads your Dockfile, imports your handler/entrypoint, and calls it directly.

---

**Previous:** [1.3 Architecture Overview](architecture-overview.md) | **Next:** [1.5 Roadmap →](roadmap.md)
