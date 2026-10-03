# Python Code Visualizer

An interactive Pygame-based learning environment where students **write their own
Python code** and **see it execute line-by-line**, with an optional Gemini AI
explanation for the current step.

## Architecture

The **tracer is the source of truth**. Gemini only *explains* the trace – it never
executes code and never invents behavior.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env       # then paste your GEMINI_API_KEY inside
python main.py