SYSTEM_PROMPT = """You are a patient Python programming tutor.
Explain the provided execution step to a beginner.
Do not invent program behavior - use only the provided source code and execution state.
Explain what changed and why.
If the trace information is insufficient, explicitly say so.
Do not rewrite the entire program unless requested.
Keep explanations short (3-5 sentences) and beginner-friendly."""


def build_step_prompt(ctx: dict) -> str:
    src = ctx.get("source", "")
    line_no = ctx.get("line_number")
    line_text = ctx.get("line_text", "")
    locs = ctx.get("locals", {})
    fn = ctx.get("function", "<module>")
    event = ctx.get("event", "line")
    concept = ctx.get("concept", "Variables & Assignment")
    prev = ctx.get("prev_locals", {})

    loc_lines = "\n".join(f"  {k} = {v}" for k, v in locs.items()) or "  (none)"
    prev_lines = "\n".join(f"  {k} = {v}" for k, v in prev.items()) or "  (none)"

    return f"""Execution step context:

Source program:
{src}
Currently executing line #{line_no}:  {line_text}
Function/frame: {fn}
Event type: {event}
Selected concept: {concept}

Variables before this step:
{prev_lines}

Variables after this step:
{loc_lines}

Please explain in 3-5 beginner-friendly sentences:
1. What this line does.
2. Why it is executing now.
3. Which variables changed (if any), and to what.
4. A small conceptual tie-in."""


def build_error_prompt(ctx: dict) -> str:
    return f"""A beginner ran this Python program and got an error.

Source:
{ctx.get('source', '')}
Error type: {ctx.get('error_type')}
Error message: {ctx.get('error_message')}
Failing line: {ctx.get('error_line')}
Variables right before the failure:
{ctx.get('var_lines', '  (unknown)')}

Explain the error to a beginner in 2-4 sentences:
1. What this error means in plain English.
2. Why it happened (based on the failing line and state).
3. How to fix it."""
