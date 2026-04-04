# Prompt Injection Blocking

[Home](../../../README.md) > [The Dockfile](../README.md) > [Policies](README.md)

Prompt injection blocking scans incoming payloads for patterns that attempt to override or manipulate the agent's instructions.

## Configuration

```yaml
policies:
  safety:
    block_prompt_injection: true
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `block_prompt_injection` | `bool` | `true` | When `true`, input is scanned against built-in injection patterns before invocation |

This is enabled by default whenever a `safety` block is present.

## Built-in Patterns

The `RuntimePolicyEngine` in `dockrion_runtime/policies.py` maintains a compiled list of regex patterns (`_injection_patterns`) that match common prompt injection techniques:

- "ignore previous instructions" variants
- "you are now" role reassignment attempts
- "system:" or "### system" prompt override patterns
- Attempts to extract system prompts
- Common jailbreak patterns

These patterns are compiled at startup for performance. The exact list is defined in the `RuntimePolicyEngine.__init__()` method.

## How It Works

1. Before the adapter's `invoke()` is called, `validate_input()` runs on the serialized input
2. Each string value in the input payload is checked against all injection patterns
3. If a match is found:
   - With `halt_on_violation: false` (default) → the request is **rejected** with a `PolicyViolationError`
   - With `halt_on_violation: true` → same behavior (injection blocking always rejects; `halt_on_violation` primarily affects output policies)

The check is performed by `RuntimePolicyEngine.validate_input()`, which serializes the payload to JSON and runs regex matching against the entire string.

## Limitations

- Pattern-based detection is not foolproof — sophisticated injection attacks may bypass regex patterns
- No ML-based injection detection is included (future consideration)
- Only string values in the payload are checked; binary or encoded content is not analyzed

## Disabling

If your agent handles untrusted input by design (e.g., a red-teaming tool):

```yaml
policies:
  safety:
    block_prompt_injection: false
```

> **Source:** `SafetyPolicy.block_prompt_injection` in `packages/schema/dockrion_schema/dockfile_v1.py`; `RuntimePolicyEngine._injection_patterns` in `packages/runtime/dockrion_runtime/policies.py`

---

**Up:** [Policies Overview](README.md) | **Next:** [Output Controls →](output-controls.md)
