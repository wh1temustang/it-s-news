"""A small JSON Schema validator for storyboards.

Supports the subset the schemas in this package use: type, properties,
required, additionalProperties: false, items, minItems, maxItems, minLength,
maxLength, enum, minimum, maximum and format: "uri". Unknown keywords
(description, default, x-*) are ignored.

The messages are written for the agent that produced the storyboard: each
names the field, what is wrong and, where it helps, what to do about it.
"""
from __future__ import annotations

from typing import Any

_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
}


def _is_type(value: Any, name: str) -> bool:
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, _TYPES[name])


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def validate(value: Any, schema: dict, path: str = "$") -> list[str]:
    """Return a list of problems; empty when `value` matches `schema`."""
    expected = schema.get("type")
    if expected and not _is_type(value, expected):
        return [f"{path}: expected {expected}, got {_type_name(value)}"]

    errors: list[str] = []
    if "enum" in schema and value not in schema["enum"]:
        allowed = ", ".join(str(v) for v in schema["enum"])
        errors.append(f"{path}: {value!r} is not allowed. Use one of: {allowed}")

    if isinstance(value, str):
        if len(value.strip()) < schema.get("minLength", 0):
            errors.append(f"{path}: must not be empty")
        limit = schema.get("maxLength")
        if limit is not None and len(value) > limit:
            errors.append(
                f"{path}: {len(value)} characters, the limit is {limit}. Shorten it."
            )
        if schema.get("format") == "uri" and not value.startswith(("https://", "http://")):
            errors.append(f"{path}: must be an http(s) URL")

    if _is_type(value, "number"):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} is below the minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} is above the maximum {schema['maximum']}")

    if isinstance(value, list):
        n = len(value)
        if n < schema.get("minItems", 0):
            errors.append(
                f"{path}: has {_plural(n, 'item')}, needs at least {schema['minItems']}"
            )
        if "maxItems" in schema and n > schema["maxItems"]:
            errors.append(
                f"{path}: has {_plural(n, 'item')}, the limit is {schema['maxItems']}. "
                "Keep the ones that matter most."
            )
        if "items" in schema:
            for i, item in enumerate(value):
                errors += validate(item, schema["items"], f"{path}[{i}]")

    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required field {key!r}")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    allowed = ", ".join(props) or "none"
                    errors.append(f"{path}: unknown field {key!r}. Allowed: {allowed}")
        for key, sub in props.items():
            if key in value:
                errors += validate(value[key], sub, f"{path}.{key}")

    return errors
