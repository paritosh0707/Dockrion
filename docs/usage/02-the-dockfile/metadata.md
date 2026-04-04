# 2.10 metadata

[Home](../../README.md) > [The Dockfile](README.md)

The `metadata` section is optional descriptive information about your agent. It is surfaced in the `/info` API endpoint and Docker image labels.

## Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `maintainer` | `string` | `null` | Name or email of the person/team maintaining this agent |
| `version` | `string` | `null` | Version string for this agent (separate from Dockrion's version) |
| `tags` | `list[str]` | `[]` | Arbitrary tags for categorization |

No validation rules beyond basic type checking. All fields are optional.

## Example

```yaml
metadata:
  maintainer: "ai-team@company.com"
  version: "2.1.0"
  tags:
    - production
    - customer-support
    - langgraph
```

## Where Metadata Appears

- **`GET /info`** — returns metadata alongside agent name, auth status, and version info
- **Docker labels** — included in the generated Dockerfile for image inspection
- **`dockrion validate --verbose`** — displayed in validation output

> **Source:** `Metadata` in `packages/schema/dockrion_schema/dockfile_v1.py`; `InfoResponse` in `packages/common-py/dockrion_common/http_models.py`

---

**Previous:** [2.9 env substitution](env-substitution.md) | **Next:** [2.11 Complete example →](complete-example.md)
