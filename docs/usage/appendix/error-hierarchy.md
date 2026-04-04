# Error Hierarchy

[Home](../../README.md) > [Appendix](README.md)

All Dockrion errors extend `DockrionError` and follow a consistent pattern: each has a `message`, `code`, and `to_dict()` method.

## Base Class

```python
class DockrionError(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
    
    def to_dict(self) -> dict:
        return {"message": self.message, "code": self.code}
```

## Core Errors (`dockrion_common`)

| Error Class | Code | Typical Trigger |
|------------|------|-----------------|
| `DockrionError` | `INTERNAL_ERROR` | Base class, unexpected errors |
| `ValidationError` | `VALIDATION_ERROR` | Schema validation, input validation, bad format |
| `AuthError` | `AUTH_ERROR` | Missing/invalid credentials |
| `RateLimitError` | `RATE_LIMIT_EXCEEDED` | Rate limit hit (when enforcement is implemented) |
| `NotFoundError` | `NOT_FOUND` | Resource not found (e.g., run ID) |
| `ConflictError` | `CONFLICT` | Conflicting operations |
| `ServiceUnavailableError` | `SERVICE_UNAVAILABLE` | Dependent service unavailable |
| `DeploymentError` | `DEPLOYMENT_ERROR` | Build or deployment failure |
| `PolicyViolationError` | `POLICY_VIOLATION` | Safety policy triggered |

### Special Errors

**`MissingSecretError`** — extends `DockrionError`:

```python
class MissingSecretError(DockrionError):
    def __init__(self, missing: list):
        self.missing_secrets = missing
        # message: "Missing required secrets: ..."
    
    def to_dict(self):
        return {
            "message": self.message,
            "code": self.code,
            "missing_secrets": self.missing_secrets
        }
```

**`BuildConflictError`** — extends `DockrionError`:

```python
class BuildConflictError(DockrionError):
    def __init__(self, message: str, conflicts: list = None):
        self.conflicts = conflicts or []
    
    def to_dict(self):
        return {
            "message": self.message,
            "code": self.code,
            "conflicts": self.conflicts
        }
```

## Adapter Errors (`dockrion_adapters`)

All extend `AdapterError` which extends `DockrionError`:

| Error Class | Code | Extra Fields | Trigger |
|------------|------|-------------|---------|
| `AdapterError` | `ADAPTER_ERROR` | — | Base for adapter errors |
| `AdapterLoadError` | `ADAPTER_LOAD_ERROR` | — | Failed to load agent module |
| `ModuleNotFoundError` | `MODULE_NOT_FOUND` | `module_path` | Python module import failed |
| `CallableNotFoundError` | `CALLABLE_NOT_FOUND` | `module_path`, `callable_name` | Function/class not in module |
| `InvalidAgentError` | `INVALID_AGENT` | — | Agent doesn't match expected shape |
| `AdapterNotLoadedError` | `ADAPTER_NOT_LOADED` | — | `invoke()` called before `load()` |
| `AgentExecutionError` | `AGENT_EXECUTION_ERROR` | — | Error during agent execution |
| `AgentCrashedError` | `AGENT_CRASHED` | `original_error` | Unexpected crash wrapper |
| `InvalidOutputError` | `INVALID_OUTPUT` | `actual_type` | Agent returned non-dict |

## Event Backend Errors (`dockrion_events`)

| Error Class | Extra Fields | Trigger |
|------------|-------------|---------|
| `BackendError` | `backend` | Base for backend errors |
| `BackendConnectionError` | `backend` | Cannot connect to Redis |
| `BackendPublishError` | `backend` | Failed to publish event |
| `BackendSubscribeError` | `backend` | Failed to subscribe |

## SDK Errors

**`DependencyConflictError`** — from `dockrion_sdk.dependencies`:

```python
class DependencyConflictError(Exception):
    def __init__(self, package, user_constraint, dockrion_constraint, message, resolution_hints=None):
        ...
```

Raised when user dependencies conflict with Dockrion's requirements in an unresolvable way.

## HTTP Error Mapping

In the runtime, errors are converted to HTTP responses:

| Error Type | HTTP Status | Response Body |
|-----------|-------------|---------------|
| `AuthError` | 401 | `{"detail": {"message": "...", "code": "AUTH_ERROR"}}` |
| `RateLimitError` | 429 | `{"detail": {"message": "...", "code": "RATE_LIMIT_EXCEEDED"}}` |
| `ValidationError` | 400 | `ErrorResponse` with `"VALIDATION_ERROR"` |
| `PolicyViolationError` | 400 | `ErrorResponse` with `"POLICY_VIOLATION"` |
| `AgentExecutionError` | 500 | `ErrorResponse` with `"AGENT_EXECUTION_ERROR"` |
| `NotFoundError` | 404 | `ErrorResponse` with `"NOT_FOUND"` |

> **Source:** `packages/common-py/dockrion_common/errors.py`; `packages/adapters/dockrion_adapters/errors.py`; `packages/events/dockrion_events/backends/base.py`

---

**Previous:** [Adapters Reference](adapters-reference.md)
