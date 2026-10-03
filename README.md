# Python Code Visualizer

A local browser-based Python learning tool. Write Python in the editor, run it
through the existing subprocess tracer, then inspect the captured events,
variables, call frames, output, and errors one step at a time.

The trace is the source of truth. Gemini is an optional explanation service and
does not execute or determine the result of a program.

## Run locally

```bash
pip install -r requirements.txt
python main.py
```

Open <http://localhost:8000>. The browser editor uses Monaco when its CDN is
reachable and falls back to a keyboard-editable editor if it is not.

## Optional Gemini explanations

Set `GEMINI_API_KEY` to enable explanations. On Replit, add it through Replit
Secrets; when running locally, copy `.env.example` to `.env` and set it there.
The key is read by the Python backend and is never sent to the browser. The
visualizer, editor, and execution controls work without it. A rejected key is
reported as unavailable without interrupting execution.

## API

- `GET /api/health` — application and Gemini availability
- `GET /api/concepts` — supported visualization concepts
- `GET /api/examples?concept=...` — starter code for a concept
- `POST /api/execute` — run source in a separate Python process and return trace data
- `POST /api/explain` — explain one captured trace step with Gemini

## Execution note

User code runs in a subprocess with a time limit, but a subprocess is **not** a
complete security sandbox. This project is for local educational use; do not
use it to run untrusted programs on a shared or public service.