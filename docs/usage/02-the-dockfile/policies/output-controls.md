# Output Controls

[Home](../../../README.md) > [The Dockfile](../README.md) > [Policies](README.md)

Output controls filter and limit what your agent returns to callers. Two mechanisms are available: **regex-based redaction** and **character truncation**.

## Redaction (redact_patterns)

### Configuration

```yaml
policies:
  safety:
    redact_patterns:
      - '\b\d{3}-\d{2}-\d{4}\b'                                    # SSN
      - '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'    # email
      - '\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'             # credit card
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `redact_patterns` | `list[str]` | `[]` | Python regex patterns. Matches are replaced with `[REDACTED]`. |

### How It Works

After the adapter returns the agent's output, `apply_output_policies()` in the `RuntimePolicyEngine`:

1. Serializes the output dict to a JSON string
2. For each pattern in `redact_patterns`, runs `re.sub(pattern, "[REDACTED]", text)`
3. Deserializes back to a dict (if the output was a dict)

This means redaction applies to **all string values** in the output, including nested fields.

### Example

Agent output before redaction:

```json
{
  "answer": "Contact john@company.com or call 123-45-6789"
}
```

After redaction (with the patterns above):

```json
{
  "answer": "Contact [REDACTED] or call [REDACTED]"
}
```

## Truncation (max_output_chars)

### Configuration

```yaml
policies:
  safety:
    max_output_chars: 10000
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_output_chars` | `int` | `null` | Maximum characters in the serialized output. Must be > 0 if set. |

### How It Works

After redaction, if the serialized output exceeds `max_output_chars`, it is truncated to that length. This is a hard limit — the output is cut without regard to JSON structure.

Truncation runs **after** redaction, so redaction patterns are applied to the full output before any truncation.

## Combined Example

```yaml
policies:
  safety:
    redact_patterns:
      - '\b\d{3}-\d{2}-\d{4}\b'
    max_output_chars: 5000
    halt_on_violation: false
```

Processing order:

1. Agent produces output
2. Redaction: SSN patterns replaced with `[REDACTED]`
3. Truncation: output capped at 5000 characters
4. Result returned to caller

## halt_on_violation

When `halt_on_violation` is `true`, policy violations raise a `PolicyViolationError` instead of silently filtering. This affects:

- Redaction: if patterns match, an error is raised instead of redacting
- The default (`false`) silently applies filters, which is usually what you want in production

> **Source:** `SafetyPolicy` in `packages/schema/dockrion_schema/dockfile_v1.py`; `redact()` in `packages/policy-engine/dockrion_policy/redactor.py`; `RuntimePolicyEngine.apply_output_policies()` in `packages/runtime/dockrion_runtime/policies.py`

---

**Previous:** [Prompt Injection](prompt-injection.md) | **Next:** [Tool Gating →](tool-gating.md)
