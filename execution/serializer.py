"""Safe JSON serialization of arbitrary Python values.

Never blindly json.dumps objects from the traced program.
"""
MAX_DEPTH = 4
MAX_ITEMS = 100
MAX_STRING = 240


def serialize(value, depth=0, seen=None):
    if seen is None:
        seen = set()
    if depth > MAX_DEPTH:
        return {"__type__": "elided", "value": "..."}

    if value is None:
        return {"__type__": "none", "value": None}
    if isinstance(value, bool):
        return {"__type__": "bool", "value": value}
    if isinstance(value, int):
        if abs(value) > 10**15:
            return {"__type__": "int", "value": str(value)[:40] + "..."}
        return {"__type__": "int", "value": value}
    if isinstance(value, float):
        if value != value:
            return {"__type__": "float", "value": "nan"}
        if value == float("inf"):
            return {"__type__": "float", "value": "inf"}
        if value == float("-inf"):
            return {"__type__": "float", "value": "-inf"}
        return {"__type__": "float", "value": value}
    if isinstance(value, str):
        if len(value) > MAX_STRING:
            return {"__type__": "str", "value": value[:MAX_STRING] + "..."}
        return {"__type__": "str", "value": value}
    if isinstance(value, (bytes, bytearray)):
        return {"__type__": "bytes", "value": f"<{len(value)} bytes>"}

    oid = id(value)
    if oid in seen:
        return {"__type__": "cycle", "value": "<recursive>"}
    seen = seen | {oid}

    if isinstance(value, list):
        return {"__type__": "list",
                "value": [serialize(v, depth + 1, seen) for v in value[:MAX_ITEMS]]}
    if isinstance(value, tuple):
        return {"__type__": "tuple",
                "value": [serialize(v, depth + 1, seen) for v in value[:MAX_ITEMS]]}
    if isinstance(value, (set, frozenset)):
        return {"__type__": "set",
                "value": [serialize(v, depth + 1, seen) for v in list(value)[:MAX_ITEMS]]}
    if isinstance(value, dict):
        out = {}
        for i, (k, v) in enumerate(value.items()):
            if i >= MAX_ITEMS:
                out["..."] = {"__type__": "elided", "value": "..."}
                break
            key = k if isinstance(k, str) else repr(k)
            out[key[:60]] = serialize(v, depth + 1, seen)
        return {"__type__": "dict", "value": out}

    try:
        r = repr(value)
    except Exception:
        r = f"<{type(value).__name__}>"
    if len(r) > MAX_STRING:
        r = r[:MAX_STRING] + "..."
    return {"__type__": "object", "value": r,
            "class": type(value).__name__}


def display(value):
    """Render a serialized value as a short human-readable string."""
    if not isinstance(value, dict) or "__type__" not in value:
        return str(value)
    t = value["__type__"]
    v = value.get("value")
    if t == "none":
        return "None"
    if t == "bool":
        return "True" if v else "False"
    if t == "int":
        return str(v)
    if t == "float":
        return str(v)
    if t == "str":
        return f'"{v}"'
    if t == "bytes":
        return v
    if t == "list":
        return "[" + ", ".join(display(x) for x in v[:8]) + (", …" if len(v) > 8 else "") + "]"
    if t == "tuple":
        return "(" + ", ".join(display(x) for x in v[:8]) + (", …" if len(v) > 8 else "") + ")"
    if t == "set":
        return "{" + ", ".join(display(x) for x in v[:8]) + (", …" if len(v) > 8 else "") + "}"
    if t == "dict":
        items = list(v.items())[:5]
        return "{" + ", ".join(f"{k}: {display(val)}" for k, val in items) + (
            ", …" if len(v) > 5 else "") + "}"
    if t == "object":
        return v
    if t == "cycle":
        return v
    if t == "elided":
        return "..."
    return str(v)