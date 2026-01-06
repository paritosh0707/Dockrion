"""
Deep Serialization Utilities

Converts arbitrary Python objects to JSON-serializable structures.
Used by adapters to ensure agent output can be serialized to JSON.
"""

import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Union

# Type alias for JSON-serializable types
JsonSerializable = Union[None, bool, int, float, str, List[Any], Dict[str, Any]]


def deep_serialize(obj: Any, max_depth: int = 50, _depth: int = 0) -> JsonSerializable:
    """
    Recursively convert Python objects to JSON-serializable types.

    Handles:
    - Primitives (None, bool, int, float, str)
    - Collections (list, tuple, set, dict)
    - Pydantic models (v1 and v2)
    - Dataclasses
    - datetime objects
    - UUID, Decimal, Enum, Path
    - Custom classes (via __dict__ or str fallback)

    Args:
        obj: Any Python object to serialize
        max_depth: Maximum recursion depth (prevents infinite loops)
        _depth: Current recursion depth (internal)

    Returns:
        JSON-serializable Python object (dict, list, or primitive)

    Examples:
        >>> from langchain_core.messages import HumanMessage
        >>> msg = HumanMessage(content="Hello")
        >>> deep_serialize(msg)
        {'content': 'Hello', 'type': 'human', ...}

        >>> from dataclasses import dataclass
        >>> @dataclass
        ... class Point:
        ...     x: int
        ...     y: int
        >>> deep_serialize(Point(1, 2))
        {'x': 1, 'y': 2}
    """
    # Prevent infinite recursion
    if _depth > max_depth:
        return f"<max depth {max_depth} exceeded>"

    # Already JSON-serializable primitives
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj

    # Handle bytes
    if isinstance(obj, bytes):
        try:
            return obj.decode("utf-8")
        except UnicodeDecodeError:
            return f"<bytes: {len(obj)} bytes>"

    # Handle lists and tuples
    if isinstance(obj, (list, tuple)):
        return [deep_serialize(item, max_depth, _depth + 1) for item in obj]

    # Handle sets and frozensets
    if isinstance(obj, (set, frozenset)):
        return [deep_serialize(item, max_depth, _depth + 1) for item in sorted(obj, key=str)]

    # Handle dicts
    if isinstance(obj, dict):
        return {str(k): deep_serialize(v, max_depth, _depth + 1) for k, v in obj.items()}

    # === Special Types ===

    # Pydantic v2 models (check first, more common)
    if hasattr(obj, "model_dump") and callable(obj.model_dump):
        try:
            return deep_serialize(obj.model_dump(), max_depth, _depth + 1)
        except Exception:
            pass  # Fall through to other methods

    # Pydantic v1 models
    if hasattr(obj, "dict") and callable(obj.dict) and hasattr(obj, "__fields__"):
        try:
            return deep_serialize(obj.dict(), max_depth, _depth + 1)
        except Exception:
            pass

    # Dataclasses
    if hasattr(obj, "__dataclass_fields__"):
        try:
            from dataclasses import asdict

            return deep_serialize(asdict(obj), max_depth, _depth + 1)
        except Exception:
            pass

    # datetime types
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, time):
        return obj.isoformat()
    if isinstance(obj, timedelta):
        return obj.total_seconds()

    # UUID
    if isinstance(obj, uuid.UUID):
        return str(obj)

    # Decimal
    if isinstance(obj, Decimal):
        return float(obj)

    # Enum
    if isinstance(obj, Enum):
        return obj.value

    # Path
    if isinstance(obj, Path):
        return str(obj)

    # === Generic Fallbacks ===

    # Objects with __dict__ (most custom classes)
    if hasattr(obj, "__dict__"):
        # Filter out private/dunder attributes
        obj_dict = {k: v for k, v in vars(obj).items() if not k.startswith("_")}
        if obj_dict:
            return deep_serialize(obj_dict, max_depth, _depth + 1)

    # Objects with __slots__
    if hasattr(obj, "__slots__"):
        obj_dict = {
            slot: getattr(obj, slot, None) for slot in obj.__slots__ if not slot.startswith("_")
        }
        if obj_dict:
            return deep_serialize(obj_dict, max_depth, _depth + 1)

    # Callable (functions, methods)
    if callable(obj):
        return f"<callable: {getattr(obj, '__name__', str(obj))}>"

    # Last resort: string representation
    try:
        return str(obj)
    except Exception:
        return f"<unserializable: {type(obj).__name__}>"


def serialize_for_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience wrapper for serializing agent output.

    Args:
        data: Agent output dictionary (may contain non-serializable objects)

    Returns:
        JSON-serializable dictionary
    """
    result = deep_serialize(data)
    # Result should always be a dict when input is a dict
    if isinstance(result, dict):
        return result
    # Fallback: wrap in dict if somehow not a dict
    return {"result": result}
