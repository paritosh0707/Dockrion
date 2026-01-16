# Streaming Feature Specification

## Overview

The Streaming feature enables real-time event delivery from AgentDock agent executions to clients. It provides a robust, scalable mechanism for streaming progress updates, intermediate results, tokens, and custom events during long-running agent invocations.

### Key Capabilities

- **Real-time Event Streaming**: Deliver events as they occur during agent execution
- **Async Execution Model**: Fire-and-forget invocation with separate event subscription
- **Event Replay**: Reconnecting clients can receive missed events
- **Multiple Subscribers**: Multiple clients can subscribe to the same run
- **Custom Events**: Users can emit domain-specific events from their agent code
- **Pluggable Backends**: Support for Redis (production) and in-memory (development)
- **Framework Agnostic**: Works with LangGraph, custom handlers, and future frameworks

---

## Architecture

The streaming system is built on a three-layer architecture that separates concerns and enables extensibility.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     LAYER 3: Domain Events                              │ │
│  │                                                                         │ │
│  │  Event models that represent what happened during execution:            │ │
│  │  • ProgressEvent    - Execution progress updates                       │ │
│  │  • CheckpointEvent  - Intermediate state/data snapshots                │ │
│  │  • TokenEvent       - LLM token streaming                              │ │
│  │  • StepEvent        - Agent step/node completion                       │ │
│  │  • CompleteEvent    - Successful completion                            │ │
│  │  • ErrorEvent       - Execution failure                                │ │
│  │  • Custom events    - User-defined domain events                       │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     LAYER 2: Event Bus                                  │ │
│  │                                                                         │ │
│  │  Abstraction layer for event routing and delivery:                     │ │
│  │  • publish(run_id, event)  - Send event to channel                    │ │
│  │  • subscribe(run_id)       - Receive events from channel              │ │
│  │  • Channel management      - run:{id} naming convention               │ │
│  │  • Event serialization     - JSON encoding/decoding                   │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     LAYER 1: Transport Backends                         │ │
│  │                                                                         │ │
│  │  Pluggable infrastructure for event delivery:                          │ │
│  │  • InMemoryBackend  - Single-instance, development/testing             │ │
│  │  • RedisBackend     - Production, multi-instance, durable              │ │
│  │  • Future: Kafka, NATS, etc.                                           │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns**: Each layer has a single responsibility
2. **Backend Agnostic**: Swap Redis for Kafka without changing application code
3. **Framework Agnostic**: Same streaming API regardless of agent framework
4. **Graceful Degradation**: Works without Redis in development mode
5. **Event Ordering**: Sequence numbers ensure correct event ordering

---

## Streaming Patterns

AgentDock supports two streaming patterns to accommodate different use cases.

### Pattern A: Direct Streaming

The client makes a single request and receives a streaming response in the same connection.

```
┌──────────┐                              ┌──────────────┐
│  Client  │                              │   Runtime    │
└────┬─────┘                              └──────┬───────┘
     │                                           │
     │  POST /invoke/stream                      │
     │  {"payload": {...}}                       │
     │ ─────────────────────────────────────────►│
     │                                           │
     │  HTTP 200 (text/event-stream)             │
     │◄─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
     │                                           │
     │  event: progress                          │
     │  data: {"step": "parsing"}                │
     │◄─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
     │                                           │
     │  event: token                             │
     │  data: {"content": "The invoice..."}      │
     │◄─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
     │                                           │
     │  event: complete                          │
     │  data: {"output": {...}}                  │
     │◄─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
     │                                           │
```

**Use When**:
- Simple streaming needs
- Single consumer per invocation
- No need for reconnection or replay

**Limitations**:
- Connection must stay open for entire execution
- Cannot reconnect and resume if connection drops
- Single subscriber only

### Pattern B: Async + Subscribe (Recommended)

The client starts an async run, then subscribes to events separately.

```
┌──────────┐                              ┌──────────────┐
│  Client  │                              │   Runtime    │
└────┬─────┘                              └──────┬───────┘
     │                                           │
     │  POST /runs                               │
     │  {"payload": {...}}                       │
     │ ─────────────────────────────────────────►│
     │                                           │
     │  HTTP 202 Accepted                        │
     │  {"run_id": "abc123"}                     │
     │◄──────────────────────────────────────────│
     │                                           │
     │  GET /runs/abc123/events                  │
     │ ─────────────────────────────────────────►│
     │                                           │
     │  HTTP 200 (text/event-stream)             │
     │◄─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
     │                                           │
     │  event: started                           │
     │  data: {"run_id": "abc123", ...}          │
     │◄─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
     │                                           │
     │  event: progress                          │
     │  data: {"step": "parsing", ...}           │
     │◄─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
     │                                           │
     │  event: complete                          │
     │  data: {"output": {...}}                  │
     │◄─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
     │                                           │
```

**Use When**:
- Long-running agent executions
- Multiple clients need to observe same run
- Reconnection and event replay required
- Production deployments

**Advantages**:
- Decoupled execution from subscription
- Multiple subscribers per run
- Reconnectable with event replay
- Run status queryable independently

---

## API Endpoints

### Runs Resource (Pattern B)

#### Create Run

Starts an async agent execution and returns immediately with a run identifier.

```
POST /runs
Content-Type: application/json

Request Body:
{
  "payload": {
    // Agent input payload (matches io_schema.input)
  },
  "run_id": "optional-custom-id",  // Optional: client-provided ID
  "config": {                       // Optional: execution config
    "timeout_seconds": 300,
    "metadata": {}
  }
}

Response: 202 Accepted
{
  "run_id": "abc123-def456-...",
  "status": "accepted",
  "events_url": "/runs/abc123-def456-.../events",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Get Run Status

Retrieves the current status and result of a run.

```
GET /runs/{run_id}

Response: 200 OK
{
  "run_id": "abc123-def456-...",
  "status": "running" | "completed" | "failed" | "cancelled",
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:30:05Z",  // If completed
  "output": {...},                          // If completed
  "error": {...},                           // If failed
  "metadata": {}
}
```

#### Subscribe to Events (SSE)

Server-Sent Events stream for real-time event delivery.

```
GET /runs/{run_id}/events
Accept: text/event-stream

Query Parameters:
- timeout: Connection timeout in seconds (default: 300)
- from_sequence: Resume from specific sequence number (for replay)

Response: 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

event: started
data: {"run_id":"abc123","type":"started","sequence":1,...}

event: progress
data: {"run_id":"abc123","type":"progress","step":"parsing","progress":0.3,...}

event: checkpoint
data: {"run_id":"abc123","type":"checkpoint","name":"parsed_doc","data":{...},...}

event: complete
data: {"run_id":"abc123","type":"complete","output":{...},"latency_seconds":2.5,...}
```

#### Cancel Run

Cancels a running execution.

```
DELETE /runs/{run_id}

Response: 200 OK
{
  "run_id": "abc123-def456-...",
  "status": "cancelled"
}
```

### Invoke Endpoints (Pattern A)

These are the existing endpoints, with streaming variant.

#### Synchronous Invoke

```
POST /invoke
Content-Type: application/json

Request Body:
{
  // Agent input payload
}

Response: 200 OK
{
  "success": true,
  "output": {...},
  "metadata": {
    "latency_seconds": 2.5,
    "agent": "my-agent"
  }
}
```

#### Direct Streaming Invoke

```
POST /invoke/stream
Content-Type: application/json
Accept: text/event-stream

Request Body:
{
  // Agent input payload
}

Response: 200 OK
Content-Type: text/event-stream

event: token
data: {"content": "The"}

event: token
data: {"content": " invoice"}

event: complete
data: {"output": {...}}
```

---

## Event Types

All events share a common base structure and are extended for specific purposes.

### Base Event Structure

Every event contains these fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique event identifier (UUID) |
| `type` | string | Event type (see below) |
| `run_id` | string | Parent run identifier |
| `sequence` | integer | Ordering sequence within run |
| `timestamp` | ISO8601 | When event was created |

### Event Type Reference

#### `started`

Emitted when a run begins execution.

```json
{
  "id": "evt-001",
  "type": "started",
  "run_id": "run-abc123",
  "sequence": 1,
  "timestamp": "2024-01-15T10:30:00.000Z",
  "agent_name": "invoice-copilot",
  "framework": "langgraph"
}
```

**Emitted By**: Runtime (automatic)

---

#### `progress`

Indicates execution progress.

```json
{
  "id": "evt-002",
  "type": "progress",
  "run_id": "run-abc123",
  "sequence": 2,
  "timestamp": "2024-01-15T10:30:01.000Z",
  "step": "parsing",
  "progress": 0.3,
  "message": "Parsing document structure"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `step` | string | Current step/phase name |
| `progress` | float | Progress percentage (0.0 to 1.0) |
| `message` | string? | Optional human-readable message |

**Emitted By**: User code via StreamContext

---

#### `checkpoint`

Captures intermediate state or data during execution.

```json
{
  "id": "evt-003",
  "type": "checkpoint",
  "run_id": "run-abc123",
  "sequence": 3,
  "timestamp": "2024-01-15T10:30:02.000Z",
  "name": "parsed_document",
  "data": {
    "fields_found": 15,
    "confidence": 0.92
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Checkpoint identifier |
| `data` | object | Checkpoint data payload |

**Emitted By**: User code via StreamContext

---

#### `token`

LLM token for streaming text generation.

```json
{
  "id": "evt-004",
  "type": "token",
  "run_id": "run-abc123",
  "sequence": 4,
  "timestamp": "2024-01-15T10:30:02.100Z",
  "content": "The invoice shows",
  "finish_reason": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `content` | string | Token text content |
| `finish_reason` | string? | Why generation stopped (if final) |

**Emitted By**: LLM streaming integration or user code

---

#### `step`

Indicates completion of an agent step (e.g., LangGraph node).

```json
{
  "id": "evt-005",
  "type": "step",
  "run_id": "run-abc123",
  "sequence": 5,
  "timestamp": "2024-01-15T10:30:03.000Z",
  "node_name": "extract_fields",
  "duration_ms": 1250,
  "input_keys": ["document"],
  "output_keys": ["extracted_fields"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `node_name` | string | Name of completed step/node |
| `duration_ms` | integer | Step execution time in milliseconds |
| `input_keys` | array | Keys present in step input |
| `output_keys` | array | Keys present in step output |

**Emitted By**: Framework integration (LangGraph) or user code

---

#### `complete`

Indicates successful run completion.

```json
{
  "id": "evt-010",
  "type": "complete",
  "run_id": "run-abc123",
  "sequence": 10,
  "timestamp": "2024-01-15T10:30:05.000Z",
  "output": {
    "vendor": "Acme Corp",
    "amount": 1500.00,
    "currency": "USD"
  },
  "latency_seconds": 5.0,
  "metadata": {
    "agent": "invoice-copilot",
    "framework": "langgraph"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `output` | object | Final agent output |
| `latency_seconds` | float | Total execution time |
| `metadata` | object | Additional execution metadata |

**Emitted By**: Runtime (automatic)

---

#### `error`

Indicates run failure.

```json
{
  "id": "evt-010",
  "type": "error",
  "run_id": "run-abc123",
  "sequence": 10,
  "timestamp": "2024-01-15T10:30:05.000Z",
  "error": "Failed to parse document: Invalid format",
  "code": "PARSE_ERROR",
  "details": {
    "line": 42,
    "expected": "date",
    "got": "string"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `error` | string | Error message |
| `code` | string | Error code |
| `details` | object? | Additional error context |

**Emitted By**: Runtime (automatic on exception)

---

#### `heartbeat`

Keep-alive signal for long-running connections.

```json
{
  "id": "evt-hb-001",
  "type": "heartbeat",
  "run_id": "run-abc123",
  "sequence": 6,
  "timestamp": "2024-01-15T10:30:15.000Z"
}
```

**Emitted By**: Runtime (automatic, every 15 seconds)

---

#### `cancelled`

Indicates run was cancelled.

```json
{
  "id": "evt-011",
  "type": "cancelled",
  "run_id": "run-abc123",
  "sequence": 11,
  "timestamp": "2024-01-15T10:30:06.000Z",
  "reason": "User requested cancellation"
}
```

**Emitted By**: Runtime (on DELETE /runs/{id})

---

### Terminal Events

The following events are terminal - they signal the end of a run:
- `complete`
- `error`
- `cancelled`

When a subscriber receives a terminal event, the SSE connection should be closed.

---

## StreamContext API

The `StreamContext` is the interface through which user agent code emits events to the stream.

### Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  USER'S AGENT CODE                                                   │
│                                                                      │
│  def process_document(state, context: StreamContext):               │
│      │                                                               │
│      ├── context.emit_progress("parsing", 0.2)                      │
│      │         │                                                     │
│      │         └── Creates ProgressEvent, publishes to EventBus     │
│      │                                                               │
│      ├── context.checkpoint("parsed", data={...})                   │
│      │         │                                                     │
│      │         └── Creates CheckpointEvent, publishes to EventBus   │
│      │                                                               │
│      └── context.emit("custom_event", data={...})                   │
│                │                                                     │
│                └── Creates custom event, publishes to EventBus      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### StreamContext Methods

#### `emit_progress(step, progress, message=None)`

Emit a progress update event.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `step` | string | Yes | Current step/phase name |
| `progress` | float | Yes | Progress (0.0 to 1.0) |
| `message` | string | No | Human-readable message |

**Example Usage**:
```
context.emit_progress(
    step="extracting_fields",
    progress=0.5,
    message="Extracted 15 of 30 fields"
)
```

---

#### `checkpoint(name, data)`

Emit a checkpoint with intermediate data.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Checkpoint identifier |
| `data` | dict | Yes | Data to include in checkpoint |

**Example Usage**:
```
context.checkpoint(
    name="parsed_document",
    data={
        "sections": ["header", "line_items", "footer"],
        "confidence": 0.95
    }
)
```

---

#### `emit_token(content, finish_reason=None)`

Emit an LLM token for text streaming.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | string | Yes | Token text |
| `finish_reason` | string | No | Reason for stopping (if final) |

**Example Usage**:
```
context.emit_token(content="The invoice")
context.emit_token(content=" total is")
context.emit_token(content=" $1,500", finish_reason="stop")
```

---

#### `emit_step(node_name, duration_ms=None, input_keys=None, output_keys=None)`

Emit a step completion event.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node_name` | string | Yes | Name of completed step |
| `duration_ms` | integer | No | Step execution time |
| `input_keys` | list | No | Input data keys |
| `output_keys` | list | No | Output data keys |

**Example Usage**:
```
context.emit_step(
    node_name="validate_invoice",
    duration_ms=250,
    output_keys=["validation_result"]
)
```

---

#### `emit(event_type, data)`

Emit a custom event with arbitrary data.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_type` | string | Yes | Custom event type name |
| `data` | dict | Yes | Event payload |

**Example Usage**:
```
context.emit(
    event_type="fraud_check_result",
    data={
        "passed": True,
        "score": 0.02,
        "checks_run": ["velocity", "pattern", "amount"]
    }
)
```

---

### Context Properties

#### `run_id`

The current run identifier (read-only).

```
current_run = context.run_id  # "run-abc123..."
```

---

### How Context Reaches User Code

The StreamContext is provided to user code through different mechanisms depending on the agent type.

#### Handler Mode

For handler-based agents, the context is passed as a parameter:

```
# User's Dockfile.yaml
agent:
  name: my-handler
  handler: myapp.service:process_request
  framework: custom
```

```
# User's handler function signature
def process_request(payload: dict, context: StreamContext) -> dict:
    context.emit_progress("starting", 0.0)
    # ... processing ...
    context.checkpoint("intermediate", data={...})
    # ... more processing ...
    return result
```

The runtime automatically injects the context when calling the handler.

#### LangGraph Mode

For LangGraph agents, the context is available through configuration:

**Option A: Via Config Parameter**
```
# In LangGraph node
def my_node(state, config):
    context = config.get("stream_context")
    if context:
        context.emit_progress("processing", 0.5)
    return state
```

**Option B: Via Context Variable**
```
from dockrion.streaming import get_current_context

def my_node(state):
    context = get_current_context()  # Thread-local context
    if context:
        context.checkpoint("node_output", data=state)
    return state
```

**Option C: Via Callbacks**
```
# Runtime registers a callback that intercepts LangGraph events
# and publishes them to the EventBus automatically
```

---

## Run ID Generation

### Default Behavior

By default, run IDs are generated as UUIDs (v4) by the runtime:

```
run_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

### Client-Provided IDs

Clients can provide their own run ID in the request:

```
POST /runs
{
  "run_id": "my-custom-id-12345",
  "payload": {...}
}
```

**Validation Rules**:
- Must be unique (runtime rejects duplicates)
- Must be 1-128 characters
- Allowed characters: alphanumeric, hyphens, underscores
- Cannot start with underscore (reserved for internal use)

**Use Cases**:
- Correlation with external systems
- Deterministic IDs for idempotency
- Integration with existing job schedulers

### Custom ID Generator (Enterprise)

For enterprise deployments requiring specific ID formats, a custom generator can be configured.

#### Configuration in Dockfile

```yaml
streaming:
  id_generator:
    type: custom
    handler: myapp.ids:generate_run_id
```

#### Generator Function Signature

```
def generate_run_id(context: RunIdContext) -> str:
    """
    Generate a custom run ID.
    
    Args:
        context: Contains agent_name, tenant_id, timestamp, etc.
    
    Returns:
        Unique run identifier string
    """
    return f"{context.tenant_id}-{context.agent_name}-{uuid.uuid4()}"
```

#### RunIdContext Fields

| Field | Type | Description |
|-------|------|-------------|
| `agent_name` | string | Name of the agent |
| `tenant_id` | string? | Tenant identifier (if multi-tenant) |
| `timestamp` | datetime | Request timestamp |
| `client_ip` | string? | Client IP address |
| `correlation_id` | string? | Trace correlation ID |

---

## Event Sources

Events come from two sources, each handled differently.

### Runtime-Generated Events (Automatic)

These events are emitted automatically by the runtime without user code involvement:

| Event | When Emitted |
|-------|--------------|
| `started` | Run begins execution |
| `complete` | Run finishes successfully |
| `error` | Exception during execution |
| `cancelled` | Run cancelled via API |
| `heartbeat` | Every N seconds during execution |

Users **do not** need to emit these events - the runtime handles them.

### User-Generated Events (Explicit)

These events are emitted by user code via the StreamContext:

| Event | How to Emit |
|-------|-------------|
| `progress` | `context.emit_progress(...)` |
| `checkpoint` | `context.checkpoint(...)` |
| `token` | `context.emit_token(...)` |
| `step` | `context.emit_step(...)` |
| Custom | `context.emit(type, data)` |

Users explicitly emit these when they want to communicate state to subscribers.

---

## Backend Configuration

### In-Memory Backend

For development and testing. No external dependencies.

```yaml
# Dockfile.yaml
streaming:
  backend: memory
```

**Characteristics**:
- Events stored in process memory
- Lost on restart
- Single instance only
- No event replay after disconnect

### Redis Backend

For production deployments. Supports multi-instance and durability.

```yaml
# Dockfile.yaml
streaming:
  backend: redis
  redis:
    url: ${REDIS_URL}  # e.g., redis://localhost:6379
    
    # Optional settings
    stream_ttl_seconds: 3600    # Event retention (default: 1 hour)
    max_events_per_run: 1000    # Max events to retain per run
    connection_pool_size: 10    # Connection pool size
```

**Characteristics**:
- Events published via Redis Pub/Sub (real-time)
- Events persisted in Redis Streams (durability)
- Reconnecting clients receive missed events
- Multiple instances can publish/subscribe
- Automatic event cleanup after TTL

### Backend Selection Logic

```
1. If streaming.backend specified in Dockfile → use that
2. If REDIS_URL environment variable set → use Redis
3. Otherwise → use in-memory
```

---

## Dockfile Configuration

Complete streaming configuration options in Dockfile.yaml:

```yaml
version: "1.0"

agent:
  name: my-agent
  entrypoint: app.graph:build_graph
  framework: langgraph

expose:
  rest: true
  streaming: sse        # sse | websocket | none
  port: 8080

# Streaming configuration section
streaming:
  # Enable async runs (Pattern B)
  async_runs: true
  
  # Backend selection
  backend: redis        # redis | memory
  
  # Redis-specific settings
  redis:
    url: ${REDIS_URL}
    stream_ttl_seconds: 3600
    max_events_per_run: 1000
    connection_pool_size: 10
  
  # Run ID configuration
  id_generator:
    type: uuid          # uuid | custom
    # For custom:
    # handler: myapp.ids:generate_run_id
  
  # Allow client-provided IDs
  allow_client_ids: true
  
  # Event configuration
  events:
    # Heartbeat interval (seconds)
    heartbeat_interval: 15
    
    # Max run duration before timeout
    max_run_duration: 3600
    
    # What automatic events to emit
    emit:
      started: true
      heartbeat: true
      step_events: true     # Auto-emit for LangGraph nodes
      token_events: true    # Auto-emit LLM tokens
  
  # Connection settings
  connection:
    # Default SSE timeout
    default_timeout: 300
    
    # Max subscribers per run
    max_subscribers_per_run: 100
```

---

## Use Cases

### Use Case 1: Long-Running Document Processing

A document processing agent that takes 30+ seconds to complete.

**Flow**:
1. Client submits document via `POST /runs`
2. Client opens SSE connection to `/runs/{id}/events`
3. Agent emits progress events as it processes
4. Agent emits checkpoints with extracted data
5. Client receives final result in `complete` event

**Events Emitted**:
```
started     → {"agent": "doc-processor"}
progress    → {"step": "uploading", "progress": 0.1}
progress    → {"step": "ocr", "progress": 0.3}
checkpoint  → {"name": "ocr_result", "data": {"pages": 5}}
progress    → {"step": "extraction", "progress": 0.6}
checkpoint  → {"name": "fields", "data": {"count": 25}}
progress    → {"step": "validation", "progress": 0.9}
complete    → {"output": {...}}
```

### Use Case 2: LLM Token Streaming

A conversational agent that streams LLM responses.

**Flow**:
1. Client submits query via `POST /invoke/stream` (Pattern A)
2. Agent processes and calls LLM
3. LLM tokens are streamed as they're generated
4. Final response delivered on completion

**Events Emitted**:
```
token       → {"content": "Based"}
token       → {"content": " on"}
token       → {"content": " the"}
token       → {"content": " invoice"}
token       → {"content": ","}
token       → {"content": " the"}
token       → {"content": " total"}
token       → {"content": " is"}
token       → {"content": " $1,500."}
complete    → {"output": {"response": "Based on the invoice, the total is $1,500."}}
```

### Use Case 3: Multi-Step Workflow Monitoring

A complex agent with multiple processing stages.

**Flow**:
1. Client starts run and subscribes to events
2. Agent progresses through multiple steps
3. Each step emits completion event
4. Checkpoints capture intermediate state
5. Client can monitor and display progress

**Events Emitted**:
```
started     → {}
step        → {"node_name": "parse_input", "duration_ms": 150}
step        → {"node_name": "validate_data", "duration_ms": 200}
step        → {"node_name": "enrich_data", "duration_ms": 1500}
checkpoint  → {"name": "enriched", "data": {...}}
step        → {"node_name": "generate_output", "duration_ms": 500}
complete    → {"output": {...}}
```

### Use Case 4: Reconnection and Replay

Client connection drops mid-execution.

**Flow**:
1. Client subscribes to events, receives events 1-5
2. Connection drops
3. Client reconnects with `?from_sequence=5`
4. Server replays events 6+ from Redis Streams
5. Client continues receiving live events

**Request**:
```
GET /runs/{id}/events?from_sequence=5
```

**Response**:
```
event: checkpoint    (sequence: 6, replayed)
event: progress      (sequence: 7, replayed)
event: step          (sequence: 8, live)
event: complete      (sequence: 9, live)
```

---

## Error Handling

### Connection Errors

| Scenario | Behavior |
|----------|----------|
| SSE connection timeout | Server closes with timeout event |
| Client disconnects | Server cleans up subscription |
| Redis unavailable | Falls back to in-memory (if configured) |
| Invalid run_id | Returns 404 Not Found |
| Run already completed | Returns complete/error event immediately |

### Execution Errors

| Scenario | Event Emitted |
|----------|---------------|
| Agent raises exception | `error` event with details |
| Timeout exceeded | `error` event with timeout code |
| Cancellation requested | `cancelled` event |
| Policy violation | `error` event with policy code |

### Event Delivery Guarantees

| Backend | Guarantee |
|---------|-----------|
| In-Memory | At-most-once (no persistence) |
| Redis Pub/Sub | At-most-once (real-time) |
| Redis Streams | At-least-once (with replay) |

The Redis backend uses both Pub/Sub (for real-time) and Streams (for durability), providing best-effort real-time delivery with replay capability.

---

## Implementation Phases

### Phase 1: Foundation

**Goal**: Minimal viable streaming with in-memory backend

- [ ] Create `dockrion_events` package structure
- [ ] Implement base event models (Pydantic)
- [ ] Implement InMemoryBackend
- [ ] Implement EventBus abstraction
- [ ] Add `POST /runs` endpoint
- [ ] Add `GET /runs/{run_id}/events` SSE endpoint
- [ ] Add `GET /runs/{run_id}` status endpoint
- [ ] Implement StreamContext for handler mode
- [ ] Update runtime to emit automatic events

### Phase 2: Redis Backend

**Goal**: Production-ready backend with durability

- [ ] Implement RedisBackend with Pub/Sub
- [ ] Add Redis Streams for event persistence
- [ ] Implement event replay on reconnection
- [ ] Add connection pooling and error handling
- [ ] Add heartbeat event emission
- [ ] Add configuration via Dockfile

### Phase 3: Framework Integration

**Goal**: Seamless LangGraph streaming

- [ ] Integrate with LangGraph's `.stream()` method
- [ ] Auto-emit step events for graph nodes
- [ ] Auto-emit token events for LLM calls
- [ ] Implement context injection for LangGraph
- [ ] Add callback-based event emission

### Phase 4: Advanced Features

**Goal**: Enterprise-ready capabilities

- [ ] Custom ID generator support
- [ ] Client-provided ID validation
- [ ] Event filtering (subscribe to specific types)
- [ ] Multi-run pattern subscriptions
- [ ] WebSocket transport option
- [ ] Run cancellation with cleanup
- [ ] Metrics and observability

---

## Security Considerations

### Authentication

All streaming endpoints respect the agent's authentication configuration:

- `/runs` endpoints require same auth as `/invoke`
- SSE connections validate auth on connection
- Long-lived connections may need token refresh handling

### Authorization

- Users can only subscribe to runs they created (or have access to)
- Run IDs are unpredictable (UUID) to prevent enumeration
- Custom IDs should be validated for format and uniqueness

### Data Privacy

- Event data may contain sensitive information
- Redis backend should use TLS in production
- Consider event data redaction policies
- Checkpoint data should follow io_schema.output policies

---

## Observability

### Metrics

The streaming system should expose these metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `runs_created_total` | Counter | Total runs created |
| `runs_active` | Gauge | Currently running |
| `events_published_total` | Counter | Events published (by type) |
| `subscribers_active` | Gauge | Active SSE connections |
| `event_latency_seconds` | Histogram | Publish-to-deliver latency |

### Logging

Structured logging for key operations:

```
{"event": "run_created", "run_id": "...", "agent": "..."}
{"event": "subscriber_connected", "run_id": "...", "client_ip": "..."}
{"event": "event_published", "run_id": "...", "type": "progress", "sequence": 5}
{"event": "run_completed", "run_id": "...", "latency_s": 2.5}
```

### Tracing

Events should carry trace context for distributed tracing:

- `trace_id` from incoming request propagated to events
- Each run creates a child span
- Events can be correlated with traces

---

## Glossary

| Term | Definition |
|------|------------|
| **Run** | A single execution of an agent, identified by run_id |
| **Event** | A discrete occurrence during a run (progress, checkpoint, etc.) |
| **Channel** | A named stream of events (format: `run:{run_id}`) |
| **Subscriber** | A client receiving events via SSE |
| **Terminal Event** | An event that signals run completion (complete, error, cancelled) |
| **Checkpoint** | A named snapshot of intermediate state/data |
| **StreamContext** | The API object used to emit events from user code |
| **EventBus** | The abstraction layer for event routing |
| **Backend** | The infrastructure handling event delivery (Redis, memory) |

---

## References

- [Server-Sent Events (SSE) Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [Redis Pub/Sub Documentation](https://redis.io/docs/manual/pubsub/)
- [Redis Streams Documentation](https://redis.io/docs/data-types/streams/)
- [LangGraph Streaming](https://langchain-ai.github.io/langgraph/how-tos/streaming/)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-15 | Initial specification |
