# 2.2 io_schema

[Home](../../README.md) > [The Dockfile](README.md)

The `io_schema` section defines the input/output contract for your agent. It controls:

- What the `/invoke` endpoint accepts (request body shape)
- What the `/invoke` endpoint returns (response body shape)
- Whether output is strictly validated against the schema
- How Swagger UI renders the request/response models

## Fields

### IOSchema (root `io_schema` key)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `strict` | `bool` | `true` | When `true`, the agent's output is validated against the output schema. On validation failure, the raw output is returned instead (no error). |
| `input` | `IOSubSchema` | `null` | JSON Schema for the request body |
| `output` | `IOSubSchema` | `null` | JSON Schema for the response body |

If `output` is `null`, strict validation is automatically disabled regardless of the `strict` field.

### IOSubSchema (used by both `input` and `output`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `type` | `string` | `"object"` | Root type. One of: `object`, `string`, `number`, `integer`, `boolean`, `array`, `null` |
| `properties` | `dict` | `{}` | Property definitions. Each value must be a dict with at least a `type` field. |
| `required` | `list[str]` | `[]` | List of required property names. Must be a subset of `properties` keys (when `type` is `object`). |
| `items` | `dict` | `null` | Schema for array items. **Required** when `type` is `array`. |
| `description` | `string` | `null` | Human-readable description of this schema |

## Supported Types

Types are validated both at the root level and within `properties[].type`:

| Type | Python mapping (for Swagger) |
|------|------------------------------|
| `string` | `str` |
| `number` | `float` |
| `integer` | `int` |
| `boolean` | `bool` |
| `array` | `list` |
| `object` | `dict` |
| `null` | `Any` |

Unknown types result in `Any` in the generated Pydantic model.

## Validation Rules

1. **Property names** must be non-empty strings after stripping whitespace
2. **Nested `type`** values within properties must be one of the supported types
3. **Array properties** must include an `items` key defining the element schema
4. **Required fields** — no duplicate entries allowed; each entry must exist in `properties` (when `type` is `object` and both lists are non-empty)
5. **Array root type** — if root `type` is `"array"`, the `items` field is required

## How io_schema Drives the API

When the runtime starts, it uses `create_pydantic_model_from_schema()` to convert your `io_schema` into dynamic Pydantic models:

```
io_schema.input   →  {AgentName}Input   →  POST /invoke request body
io_schema.output  →  {AgentName}Output  →  output field in response
```

These models appear in the Swagger UI at `/docs`, giving callers exact type information for your agent's API.

The invoke response wraps the output:

```json
{
  "success": true,
  "output": { ... },    // matches your io_schema.output
  "metadata": { ... }
}
```

See [4.2 How io_schema Shapes Swagger](../04-the-generated-api/io-schema-and-swagger.md) for full details on the type mapping.

## Examples

### Simple text in/out

```yaml
io_schema:
  strict: true
  input:
    type: object
    properties:
      query:
        type: string
        description: "The user's question"
    required: [query]
  output:
    type: object
    properties:
      answer:
        type: string
      confidence:
        type: number
```

### Array output

```yaml
io_schema:
  input:
    type: object
    properties:
      topic:
        type: string
  output:
    type: object
    properties:
      suggestions:
        type: array
        items:
          type: string
```

### No schema (permissive)

```yaml
io_schema:
  input:
    type: object
  output:
    type: object
```

When no `properties` are defined, the generated Pydantic model accepts any JSON object. This is useful during early development but means Swagger won't show specific fields.

> **Source:** `IOSchema`, `IOSubSchema` in `packages/schema/dockrion_schema/dockfile_v1.py`; `create_pydantic_model_from_schema()` in `packages/runtime/dockrion_runtime/schema_utils.py`

---

**Previous:** [2.1 agent](agent.md) | **Next:** [2.3 auth →](auth/README.md)
