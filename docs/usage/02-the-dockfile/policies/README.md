# 2.4 Policies

[Home](../../README.md) > [The Dockfile](../README.md) > Policies

Policies give you control over what your agent can do and what it outputs. The `policies` section in the Dockfile configures tool access restrictions and safety guardrails. Policies are enforced by the `RuntimePolicyEngine` in the runtime.

## Overview

```yaml
policies:
  tools:
    allowed: [web_search, calculator]
    deny_by_default: true
  safety:
    block_prompt_injection: true
    redact_patterns:
      - '\b\d{3}-\d{2}-\d{4}\b'    # SSN
      - '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # email
    max_output_chars: 10000
    halt_on_violation: false
```

Both `tools` and `safety` are optional. If the `policies` section is omitted, no tool restrictions or safety filters are applied (except `block_prompt_injection` defaults to `true` when safety is present).

## How Policies Wire into the Runtime

1. The `RuntimePolicyEngine` is created from `spec.policies` during app startup
2. Before invocation: `validate_input()` checks for prompt injection patterns
3. After invocation: `apply_output_policies()` runs redaction, then truncation
4. Tool calls: the adapter can check `is_tool_allowed()` before executing tools

If `halt_on_violation` is `true`, a policy violation raises an error instead of silently filtering.

## In This Section

| Page | What it covers |
|------|----------------|
| [Prompt Injection Blocking](prompt-injection.md) | Built-in patterns, `block_prompt_injection` flag |
| [Output Controls](output-controls.md) | `redact_patterns` (regex-based) and `max_output_chars` |
| [Tool Gating](tool-gating.md) | `tools.allowed`, `deny_by_default` |

> **Source:** `Policies`, `ToolPolicy`, `SafetyPolicy` in `packages/schema/dockrion_schema/dockfile_v1.py`; `RuntimePolicyEngine` in `packages/runtime/dockrion_runtime/policies.py`

---

**Up:** [The Dockfile](../README.md) | **Previous:** [2.3 Auth](../auth/README.md) | **Next:** [2.5 Secrets →](../secrets.md)
