"""Runs in a subprocess. Executes the user's code with sys.settrace."""
import sys
import os
import io
import json
import types
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from execution.serializer import serialize

MAX_STEPS = 5000
USER_FILENAME = "<user_code>"


def _snapshot_locals(frame):
    out = {}
    for name, value in frame.f_locals.items():
        if name.startswith("__") and name.endswith("__"):
            continue
        if isinstance(value, types.ModuleType):
            continue
        try:
            out[name] = serialize(value)
        except Exception:
            out[name] = {"__type__": "object", "value": "<unserializable>"}
    return out


def main():
    if len(sys.argv) < 3:
        sys.stderr.write("usage: tracer_runner.py <source_path> <out_path>\n")
        sys.exit(1)

    source_path, out_path = sys.argv[1], sys.argv[2]
    with open(source_path, "r", encoding="utf-8") as f:
        source = f.read()

    events = []
    state = {"step": 0, "calls": []}
    real_stdout = sys.stdout
    real_stderr = sys.stderr
    captured = io.StringIO()
    sys.stdout = captured
    error_info = None

    def make_event(frame, event_type, extra=None):
        ev = {
            "step": state["step"],
            "event": event_type,
            "line_number": frame.f_lineno,
            "function": frame.f_code.co_name,
            "call_depth": len(state["calls"]),
            "locals": _snapshot_locals(frame),
            "stdout": captured.getvalue(),
        }
        if extra:
            ev.update(extra)
        return ev

    def local_tracer(frame, event_type, arg):
        if frame.f_code.co_filename != USER_FILENAME:
            return None

        if state["step"] >= MAX_STEPS:
            raise RuntimeError(
                f"Step limit of {MAX_STEPS} reached (possible infinite loop)."
            )

        if event_type == "line":
            events.append(make_event(frame, "line"))
            state["step"] += 1

        elif event_type == "call":
            state["calls"].append(frame.f_code.co_name)
            events.append(make_event(frame, "call"))
            state["step"] += 1

        elif event_type == "return":
            try:
                ret = serialize(arg)
            except Exception:
                ret = {"__type__": "object", "value": "<unserializable>"}
            if state["calls"]:
                state["calls"].pop()
            events.append(make_event(frame, "return", {"return_value": ret}))
            state["step"] += 1

        elif event_type == "exception":
            exc_type, exc_val, _ = arg
            events.append(make_event(frame, "exception", {
                "exception": {
                    "type": getattr(exc_type, "__name__", str(exc_type)),
                    "message": str(exc_val),
                }
            }))
            state["step"] += 1

        return local_tracer

    def global_tracer(frame, event_type, arg):
        if frame.f_code.co_filename != USER_FILENAME:
            return None
        return local_tracer

    sys.settrace(global_tracer)
    try:
        code = compile(source, USER_FILENAME, "exec")
        g = {"__name__": "__main__", "__file__": USER_FILENAME}
        exec(code, g)
    except SystemExit:
        pass
    except BaseException as e:
        user_line = None
        tb = e.__traceback__
        while tb:
            if tb.tb_frame.f_code.co_filename == USER_FILENAME:
                user_line = tb.tb_lineno
            tb = tb.tb_next
        error_info = {
            "type": type(e).__name__,
            "message": str(e),
            "line": user_line,
            "traceback": traceback.format_exc(),
        }
    finally:
        sys.settrace(None)
        sys.stdout = real_stdout
        sys.stderr = real_stderr

    payload = {
        "source_code": source,
        "events": events,
        "error": error_info,
        "stdout": captured.getvalue(),
        "stderr": "",
        "timed_out": False,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)


if __name__ == "__main__":
    main()