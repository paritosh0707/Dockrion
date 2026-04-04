# 5.4 Adding Streaming

[Home](../../README.md) > [Guides & Recipes](README.md)

Step-by-step guide to enabling real-time streaming for your agent.

## Option 1: CLI Quick-Add

```bash
# Basic SSE streaming
dockrion add streaming

# With chat events preset and async runs
dockrion add streaming --events chat --async-runs

# Redis backend for production
dockrion add streaming --backend redis --events all

# Custom heartbeat and duration
dockrion add streaming --heartbeat 30 --max-duration 7200
```

## Option 2: Manual Configuration

### Step 1: Enable SSE in expose

```yaml
expose:
  rest: true
  streaming: sse    # this is the default
```

### Step 2: Add streaming config

```yaml
streaming:
  async_runs: true           # enable POST /runs
  backend: memory             # memory for dev, redis for production
  events:
    allowed: chat             # preset: started + token + complete + error
    heartbeat_interval: 15
```

### Step 3: Test with curl

```bash
dockrion run

# Direct SSE (Pattern A)
curl -N -X POST http://localhost:8080/invoke/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "explain AI"}'

# Async run (Pattern B)
curl -X POST http://localhost:8080/runs \
  -H "Content-Type: application/json" \
  -d '{"query": "long analysis task"}'
# Returns: {"run_id": "abc-123", "events_url": "/runs/abc-123/events"}

curl -N http://localhost:8080/runs/abc-123/events
```

## Choosing a Backend

| Scenario | Backend | Config |
|----------|---------|--------|
| Local development | `memory` | `backend: memory` |
| Single-instance production | `memory` | `backend: memory` |
| Multi-instance / HA | `redis` | `backend: redis` with `redis.url` |

For Redis, add the URL to your secrets:

```yaml
streaming:
  backend: redis
  redis:
    url: ${REDIS_URL}

secrets:
  required:
    - name: REDIS_URL
      description: "Redis connection URL"
```

## Emitting Events from Your Agent

If you want your agent to send custom progress updates:

### Handler Mode

```python
def handle(payload: dict, context=None) -> dict:
    if context:
        context.sync_emit_progress(step="loading", progress=0.2, message="Loading data...")
        # ... do work ...
        context.sync_emit_progress(step="processing", progress=0.7, message="Analyzing...")
    
    return {"answer": "done"}
```

### LangGraph Mode

Use `get_current_context()` inside graph nodes:

```python
from dockrion_events import get_current_context

def process_node(state):
    ctx = get_current_context()
    if ctx:
        ctx.sync_emit_progress(step="process", progress=0.5, message="Processing...")
    # ... node logic ...
    return state
```

See [StreamContext for Agent Authors](../02-the-dockfile/streaming/stream-context.md) for the full API.

---

**Previous:** [5.3 Adding Auth](adding-auth.md) | **Next:** [5.5 Adding Policies →](adding-policies.md)
