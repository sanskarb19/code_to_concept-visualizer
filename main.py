import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

# Keep credentials in the server environment; never send them to the browser.
load_dotenv(ROOT / ".env")

from ai import GeminiExplainer  # noqa: E402
from examples import get_example  # noqa: E402
from execution.executor import execute_code  # noqa: E402
from visualization.registry import CONCEPTS  # noqa: E402

app = FastAPI(
    title="Python Code Visualizer",
    description="Run Python in a subprocess and inspect its captured execution trace.",
    version="1.0.0",
)
gemini = GeminiExplainer()
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class ExecuteRequest(BaseModel):
    code: str = Field(max_length=100_000)
    concept: str = Field(default="Variables & Assignment", max_length=80)


class ExplainRequest(BaseModel):
    source: str = Field(max_length=100_000)
    line_number: int | None = None
    line_text: str = Field(default="", max_length=2_000)
    event: str = Field(default="line", max_length=40)
    function: str = Field(default="<module>", max_length=200)
    concept: str = Field(default="Variables & Assignment", max_length=80)
    locals: dict[str, Any] = Field(default_factory=dict)
    prev_locals: dict[str, Any] = Field(default_factory=dict)


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
async def health():
    return {
        "success": True,
        "gemini": {"available": gemini.available, "status": gemini.status()},
    }


@app.get("/api/concepts")
async def concepts():
    return {"concepts": CONCEPTS}


@app.get("/api/examples")
async def example(concept: str = "Variables & Assignment"):
    if concept not in CONCEPTS:
        raise HTTPException(status_code=422, detail="Choose a concept from the list.")
    return {"code": get_example(concept)}


@app.post("/api/execute")
async def run_program(request: ExecuteRequest):
    if request.concept not in CONCEPTS:
        raise HTTPException(status_code=422, detail="Choose a concept from the list.")

    # Run the blocking subprocess call off the event loop so the web UI remains
    # responsive while the trace is being collected.
    result = await run_in_threadpool(execute_code, request.code, 5.0)
    result.setdefault("source_code", request.code)
    result.setdefault("events", [])
    result.setdefault("stdout", "")
    result.setdefault("stderr", "")
    result.setdefault("timed_out", False)
    result.setdefault("error", None)
    result["success"] = result["error"] is None
    return result


@app.post("/api/explain")
async def explain(request: ExplainRequest):
    if request.concept not in CONCEPTS:
        raise HTTPException(status_code=422, detail="Choose a concept from the list.")

    context = request.model_dump()
    try:
        explanation = await run_in_threadpool(gemini.explain_step, context)
        return {"success": True, "explanation": explanation}
    except Exception as exc:
        # Gemini is an optional explanation service; its failure must not affect
        # execution, trace playback, or server availability.
        return {
            "success": False,
            "explanation": "",
            "error": str(exc) or "Gemini could not generate an explanation.",
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "8000")),
        reload=False,
    )