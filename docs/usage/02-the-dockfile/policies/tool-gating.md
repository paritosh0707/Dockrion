# Tool Gating

[Home](../../../README.md) > [The Dockfile](../README.md) > [Policies](README.md)

Tool gating controls which tools your agent is allowed to call during execution.

## Configuration

```yaml
policies:
  tools:
    allowed: [web_search, calculator, pdf_reader]
    deny_by_default: true
```

## Fields (ToolPolicy)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `allowed` | `list[str]` | `[]` | Tool names the agent is permitted to use |
| `deny_by_default` | `bool` | `true` | When `true`, any tool **not** in `allowed` is blocked. When `false`, all tools are permitted. |

## How It Works

The `is_tool_allowed()` function (in both `dockrion_policy/tool_guard.py` and `RuntimePolicyEngine`):

```
if deny_by_default is false → allow all tools
if deny_by_default is true  → only allow tools in the allowed list
```

| `deny_by_default` | `allowed` list | Tool "web_search" | Tool "send_email" |
|-------------------|---------------|-------------------|-------------------|
| `true` | `[web_search, calculator]` | Allowed | **Blocked** |
| `true` | `[]` (empty) | **Blocked** | **Blocked** |
| `false` | `[web_search]` | Allowed | Allowed |
| `false` | `[]` | Allowed | Allowed |

## Usage Patterns

### Strict allowlist (recommended for production)

```yaml
policies:
  tools:
    allowed: [web_search, calculator, database_query]
    deny_by_default: true
```

Only the three listed tools can be called. Any other tool call is blocked.

### No restrictions (development)

```yaml
policies:
  tools:
    deny_by_default: false
```

All tools are allowed. Useful during development when you're iterating on which tools the agent needs.

### Block everything

```yaml
policies:
  tools:
    allowed: []
    deny_by_default: true
```

No tools can be called. The agent can only use its own logic without external tool calls.

## Integration with Frameworks

Tool gating is **advisory** — the runtime provides the `is_tool_allowed()` check, but enforcement depends on how the adapter/framework is configured:

- **LangGraph:** Your graph can check `is_tool_allowed()` before executing tool nodes
- **Handler mode:** Your handler function can call the policy engine to check tool permissions
- **Future:** Automatic tool interception at the adapter level is planned

> **Source:** `ToolPolicy` in `packages/schema/dockrion_schema/dockfile_v1.py`; `is_tool_allowed()` in `packages/policy-engine/dockrion_policy/tool_guard.py`

---

**Previous:** [Output Controls](output-controls.md) | **Up:** [Policies Overview](README.md)
