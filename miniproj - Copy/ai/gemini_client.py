"""Gemini client with backward/forward compatibility."""
import os
import threading

_SDK = None
_new_genai = None
_new_types = None
_old_genai = None

try:
    from google import genai as _new_genai
    from google.genai import types as _new_types
    _SDK = "google-genai"
except ImportError:
    try:
        import google.generativeai as _old_genai
        _SDK = "google-generativeai"
    except ImportError:
        _SDK = None

from ai.prompts import SYSTEM_PROMPT, build_step_prompt, build_error_prompt

DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiExplainer:
    """Optional. Fails loudly but harmlessly if not configured."""

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.sdk = _SDK
        self._model_name = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL).strip()
        self._client = None
        self._model = None
        self._error = None
        self.available = False

        if _SDK is None:
            self._error = ("No Gemini SDK installed. Run one of:\n"
                           "  pip install google-genai         (recommended)\n"
                           "  pip install google-generativeai  (deprecated)")
            return
        if not api_key:
            self._error = "GEMINI_API_KEY not set. Set it in your environment to enable AI."
            return

        try:
            if _SDK == "google-genai":
                self._client = _new_genai.Client(api_key=api_key)
            else:
                _old_genai.configure(api_key=api_key)
                self._model = _old_genai.GenerativeModel(
                    model_name=self._model_name,
                    system_instruction=SYSTEM_PROMPT,
                )
            self.available = True
        except Exception as e:
            self._error = f"Failed to init Gemini ({_SDK}): {e}"

    def status(self):
        if self.available:
            return f"ready ({self.sdk}, {self._model_name})"
        return self._error

    def _generate(self, prompt: str) -> str:
        if self.sdk == "google-genai":
            resp = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
                config=_new_types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                ),
            )
        else:
            resp = self._model.generate_content(prompt)
        text = getattr(resp, "text", None)
        return text.strip() if text else str(resp).strip()

    def explain_step_async(self, ctx, on_done):
        if not self.available:
            on_done(f"AI explanation unavailable: {self._error}", False)
            return
        def worker():
            try:
                on_done(self._generate(build_step_prompt(ctx)), True)
            except Exception as e:
                on_done(f"AI request failed: {e}", False)
        threading.Thread(target=worker, daemon=True).start()

    def explain_error_async(self, ctx, on_done):
        if not self.available:
            on_done(f"AI explanation unavailable: {self._error}", False)
            return
        def worker():
            try:
                on_done(self._generate(build_error_prompt(ctx)), True)
            except Exception as e:
                on_done(f"AI request failed: {e}", False)
        threading.Thread(target=worker, daemon=True).start()
