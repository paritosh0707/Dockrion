# 4.4 Streaming Consumption

[Home](../../README.md) > [The Generated API](README.md)

How to consume streaming events from your agent in different languages and environments.

## Pattern A: Direct SSE (`POST /invoke/stream`)

### curl

```bash
curl -N -X POST http://localhost:8080/invoke/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"query": "explain quantum computing"}'
```

Use `-N` to disable output buffering. Events stream as they arrive:

```
event: started
data: {"id":"evt_1","type":"started","run_id":"abc","sequence":0,"timestamp":"...","agent_name":"my-agent"}

event: token
data: {"id":"evt_2","type":"token","run_id":"abc","sequence":1,"timestamp":"...","content":"Quantum"}

event: token
data: {"id":"evt_3","type":"token","run_id":"abc","sequence":2,"timestamp":"...","content":" computing"}

event: complete
data: {"id":"evt_4","type":"complete","run_id":"abc","sequence":3,"timestamp":"...","output":{"answer":"..."},"latency_seconds":1.5}
```

### JavaScript (Browser)

The `POST /invoke/stream` endpoint requires a POST body, so native `EventSource` (GET-only) cannot be used directly. Use `fetch` with a readable stream:

```javascript
async function streamInvoke(payload) {
  const response = await fetch('http://localhost:8080/invoke/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'your-key'
    },
    body: JSON.stringify(payload)
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop(); // keep incomplete line in buffer

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const event = JSON.parse(line.slice(6));
        console.log(event.type, event);
        
        if (['complete', 'error', 'cancelled'].includes(event.type)) {
          return event;
        }
      }
    }
  }
}

streamInvoke({ query: 'explain quantum computing' });
```

### Python

```python
import requests
import json

response = requests.post(
    'http://localhost:8080/invoke/stream',
    json={'query': 'explain quantum computing'},
    headers={'X-API-Key': 'your-key'},
    stream=True
)

for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            event = json.loads(line[6:])
            print(f"[{event['type']}] {event.get('content', event.get('output', ''))}")
            
            if event['type'] in ('complete', 'error', 'cancelled'):
                break
```

Or with `sseclient-py`:

```python
import sseclient
import requests

response = requests.post(
    'http://localhost:8080/invoke/stream',
    json={'query': 'explain quantum computing'},
    headers={'X-API-Key': 'your-key'},
    stream=True
)

client = sseclient.SSEClient(response)
for event in client.events():
    data = json.loads(event.data)
    print(f"[{event.event}] {data}")
```

---

## Pattern B: Async Runs (`/runs`)

### Step 1: Create a run

```bash
RUN_ID=$(curl -s -X POST http://localhost:8080/runs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"query": "process invoice #1234"}' | jq -r '.run_id')
```

### Step 2: Subscribe to events

```bash
curl -N http://localhost:8080/runs/$RUN_ID/events \
  -H "X-API-Key: your-key"
```

Since this is a GET endpoint, you can use native `EventSource` in browsers:

```javascript
const runId = '550e8400-e29b-41d4-a716-446655440000';
const eventSource = new EventSource(
  `/runs/${runId}/events`,
  // Note: EventSource doesn't support custom headers.
  // For auth, pass the key as a query parameter or use a proxy.
);

eventSource.addEventListener('token', (e) => {
  const data = JSON.parse(e.data);
  process.stdout.write(data.content);
});

eventSource.addEventListener('complete', (e) => {
  const data = JSON.parse(e.data);
  console.log('\nDone:', data.output);
  eventSource.close();
});

eventSource.addEventListener('error', (e) => {
  console.error('Error:', e.data);
  eventSource.close();
});
```

### Step 3: Check status (optional)

```bash
curl http://localhost:8080/runs/$RUN_ID \
  -H "X-API-Key: your-key"
```

### Reconnection with Event Replay

If a client disconnects, it can reconnect using `from_sequence`:

```bash
# Reconnect and get events from sequence 5 onwards
curl -N "http://localhost:8080/runs/$RUN_ID/events?from_sequence=5" \
  -H "X-API-Key: your-key"
```

Stored events are replayed first, then live events continue.

---

## WebSocket

> **Status: Coming soon.** The Dockfile schema accepts `streaming: websocket` in `expose`, but no WebSocket endpoint is implemented in the runtime. Use SSE for now.

---

## Terminal Events

When you receive an event with type `complete`, `error`, or `cancelled`, the SSE connection will close. Your client should handle this gracefully.

> **Source:** `invoke_agent_stream()` in `packages/runtime/dockrion_runtime/endpoints/invoke.py`; `/runs` endpoints in `packages/runtime/dockrion_runtime/endpoints/runs.py`

---

**Previous:** [4.3 Auth from Caller's Perspective](auth-callers-perspective.md) | **Next:** [5. Guides & Recipes →](../05-guides-and-recipes/README.md)
