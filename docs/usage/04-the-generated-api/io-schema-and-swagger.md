# 4.2 How io_schema Shapes Swagger

[Home](../../README.md) > [The Generated API](README.md)

Your Dockfile's `io_schema` directly drives the Swagger UI and OpenAPI specification. This page explains the exact mapping.

## The Transformation

```
Dockfile io_schema        →   Pydantic models       →   OpenAPI / Swagger
─────────────────              ─────────────             ─────────────────
io_schema.input           →   {Agent}Input           →   POST /invoke request body
io_schema.output          →   {Agent}Output          →   output field in response
                                                     →   Swagger shows typed fields
```

The runtime uses `create_pydantic_model_from_schema()` in `schema_utils.py` to convert JSON Schema-style definitions into Pydantic v2 models at startup.

## Type Mapping

| Dockfile `type` | Python type | Swagger type |
|-----------------|-------------|--------------|
| `string` | `str` | `string` |
| `number` | `float` | `number` |
| `integer` | `int` | `integer` |
| `boolean` | `bool` | `boolean` |
| `array` | `list` | `array` |
| `object` | `dict` | `object` |
| `null` or unknown | `Any` | no specific type |

## Example

Given this Dockfile:

```yaml
io_schema:
  input:
    type: object
    properties:
      query:
        type: string
        description: "The user's question"
      max_results:
        type: integer
        description: "Max results to return"
    required: [query]
  output:
    type: object
    properties:
      answer:
        type: string
      sources:
        type: array
        items:
          type: string
      confidence:
        type: number
```

Swagger at `/docs` will show:

**Request body** for `POST /invoke`:

```json
{
  "query": "string",        // required
  "max_results": 0          // optional (integer)
}
```

**Response body**:

```json
{
  "success": true,
  "output": {
    "answer": "string",
    "sources": ["string"],
    "confidence": 0.0
  },
  "metadata": {}
}
```

## Required vs Optional Fields

- Fields listed in `io_schema.input.required` become **required** in the Pydantic model (no default)
- Fields not in `required` become **optional** with `default=None`
- This appears in Swagger as required vs optional markers on fields

## No Schema Defined

If `io_schema.input` has no `properties` (or is `null`), the generated model accepts any JSON object. Swagger will show a generic `object` without specific fields. This works but means callers don't get type hints.

## Strict Output Validation

When `io_schema.strict` is `true` (the default) and an output schema is defined:

1. The agent's output is validated against the `{Agent}Output` Pydantic model
2. If validation **succeeds**, the typed output is returned
3. If validation **fails**, the raw output is returned as-is (no error — graceful degradation)

When `io_schema.output` is `null`, strict validation is automatically disabled.

## The Invoke Response Wrapper

The `/invoke` response is wrapped in a dynamic model:

```python
InvokeResponseModel = create_model(
    f"{agent_name}InvokeResponse",
    success=(bool, True),
    output=(OutputModel, ...),
    metadata=(Dict[str, Any], ...)
)
```

This means Swagger shows a typed `output` field matching your `io_schema.output`, not a generic `Any`.

> **Source:** `create_pydantic_model_from_schema()` in `packages/runtime/dockrion_runtime/schema_utils.py`; model creation in `packages/runtime/dockrion_runtime/app.py`

---

**Previous:** [4.1 Endpoints Reference](endpoints-reference.md) | **Next:** [4.3 Auth from Caller's Perspective →](auth-callers-perspective.md)
