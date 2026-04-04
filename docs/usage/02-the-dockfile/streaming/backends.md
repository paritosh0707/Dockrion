# Backends

[Home](../../../README.md) > [The Dockfile](../README.md) > [Streaming](README.md)

Backends store and distribute streaming events. The choice of backend affects durability, scalability, and whether events survive process restarts.

## Available Backends

| Backend | Value | Best for | Persistence |
|---------|-------|----------|-------------|
| Memory | `"memory"` | Development, single-instance | No — events lost on restart |
| Redis | `"redis"` | Production, multi-instance | Yes — events stored in Redis Streams |

## Memory Backend (default)

```yaml
streaming:
  backend: memory
```

No additional configuration needed. Events are stored in Python dicts and distributed via `asyncio.Queue`.

### How It Works

- `InMemoryBackend` stores events in `_events` dict (keyed by `run_id`)
- Subscribers receive events via `asyncio.Queue` instances per subscriber
- Events are trimmed to `max_events_per_run` (default from `EventBusFactory`)
- When the process restarts, all events are lost

### Limitations

- Single-process only — subscribers must be in the same Python process
- No event persistence — disconnected clients cannot replay past events from a previous session
- Memory usage grows with event volume

## Redis Backend

```yaml
streaming:
  backend: redis
  redis:
    url: ${REDIS_URL:-redis://localhost:6379}
    stream_ttl_seconds: 3600
    max_events_per_run: 1000
    connection_pool_size: 10
```

### Fields (RedisStreamingConfig)

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `url` | `string` | `"${REDIS_URL}"` | — | Redis connection URL |
| `stream_ttl_seconds` | `int` | `3600` | 60–604800 | How long to retain events in Redis |
| `max_events_per_run` | `int` | `1000` | 10–100000 | Max events stored per run |
| `connection_pool_size` | `int` | `10` | — | Redis connection pool size |

### How It Works

- `RedisBackend` uses Redis Pub/Sub for real-time event distribution
- Events are also stored in Redis Streams (via `XADD`) for replay
- `stream_ttl_seconds` sets the Redis `EXPIRE` on stream keys
- Subscribers receive events via Pub/Sub; replay uses `XRANGE`
- Multi-process safe — any instance can publish, any instance can subscribe

### Requirements

The Redis backend requires the `aioredis` library (or `redis` with async support). If not installed, the backend falls back to memory.

### Auto-Initialization

If `backend: redis` is set but the `redis` sub-config is missing, the schema auto-creates a `RedisStreamingConfig()` with defaults:

```yaml
# This:
streaming:
  backend: redis

# Is equivalent to:
streaming:
  backend: redis
  redis:
    url: "${REDIS_URL}"
    stream_ttl_seconds: 3600
    max_events_per_run: 1000
    connection_pool_size: 10
```

## Choosing a Backend

| Criterion | Memory | Redis |
|-----------|--------|-------|
| Setup | Zero config | Requires Redis instance |
| Multi-process | No | Yes |
| Event replay | Same session only | Across restarts |
| Suitable for production | Single-instance only | Yes |
| Latency | Lowest | Slightly higher (network) |

> **Source:** `InMemoryBackend` in `packages/events/dockrion_events/backends/memory.py`; `RedisBackend` in `packages/events/dockrion_events/backends/redis.py`; `RedisStreamingConfig` in `packages/schema/dockrion_schema/dockfile_v1.py`

---

**Previous:** [Event Types](event-types.md) | **Next:** [StreamContext →](stream-context.md)
