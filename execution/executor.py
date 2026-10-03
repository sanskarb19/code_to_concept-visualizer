"""Parent-side executor: spawns tracer_runner.py in a subprocess."""
import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path

RUNNER = Path(__file__).resolve().parent / "tracer_runner.py"


def execute_code(source: str, timeout: float = 5.0) -> dict:
    """Execute user code in a subprocess and return a trace dict.

    SECURITY: A subprocess alone is NOT a full sandbox. Only run trusted code.
    """
    if not source.strip():
        return {
            "source_code": source, "events": [], "error": None,
            "stdout": "", "stderr": "", "timed_out": False,
        }

    src_fd, src_path = tempfile.mkstemp(suffix=".py", prefix="usercode_")
    out_fd, out_path = tempfile.mkstemp(suffix=".json", prefix="trace_")
    os.close(out_fd)
    try:
        with os.fdopen(src_fd, "w", encoding="utf-8") as f:
            f.write(source)

        try:
            proc = subprocess.Popen(
                [sys.executable, "-u", str(RUNNER), src_path, out_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except Exception as e:
            return {
                "source_code": source, "events": [],
                "error": {"type": "LaunchError", "message": str(e), "line": None},
                "stdout": "", "stderr": "", "timed_out": False,
            }

        timed_out = False
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            stdout, stderr = proc.communicate()

        if timed_out:
            return {
                "source_code": source, "events": [],
                "error": {
                    "type": "TimeoutError",
                    "message": f"Execution exceeded {timeout:.1f}s and was terminated.",
                    "line": None,
                },
                "stdout": "", "stderr": stderr or "", "timed_out": True,
            }

        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            with open(out_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["stderr"] = stderr or ""
            data.setdefault("timed_out", False)
            return data

        return {
            "source_code": source, "events": [],
            "error": {
                "type": "RunnerError",
                "message": (stderr or stdout or "Tracer runner produced no trace.").strip(),
                "line": None,
            },
            "stdout": stdout or "", "stderr": stderr or "", "timed_out": False,
        }
    finally:
        for p in (src_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass