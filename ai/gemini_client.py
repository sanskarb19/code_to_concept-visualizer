"""Small optional client for the current Google GenAI Python SDK."""

import os

from ai.prompts import SYSTEM_PROMPT, build_step_prompt

try:
    from google import genai
except ImportError:  # Keep execution and visualization usable without the SDK.
    genai = None


class GeminiExplainer:
    def __init__(self):
        self._client = None
        self._available = False
        self._error = None
        self.model = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash").strip()
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()

        if genai is None:
            self._error = "The Google GenAI SDK is not installed."
        elif not api_key:
            self._error = "GEMINI_API_KEY is not configured."
        else:
            try:
                self._client = genai.Client(api_key=api_key)
                self._available = True
            except Exception as exc:
                self._error = f"Gemini could not be initialized: {exc}"

    @property
    def available(self) -> bool:
        return self._available

    def status(self) -> str:
        if self.available:
            return f"Connected · {self.model}"
        return f"Unavailable · {self._error or 'Gemini is not configured.'}"

    def explain_step(self, context: dict) -> str:
        if not self.available:
            raise RuntimeError(self._error or "Gemini is not configured.")

        try:
            interaction = self._client.interactions.create(
                model=self.model,
                input=build_step_prompt(context),
                system_instruction=SYSTEM_PROMPT,
                generation_config={"temperature": 0.35, "thinking_level": "low"},
                # Explanations are independent; do not persist source or state
                # snapshots in Google's server-side interaction history.
                store=False,
                timeout=45,
            )
        except Exception as exc:
            message = str(exc)
            if "401" in message or "UNAUTHENTICATED" in message:
                self._available = False
                self._error = (
                    "Google rejected the configured Gemini credentials. "
                    "Update GEMINI_API_KEY in Replit Secrets or your local .env file."
                )
                raise RuntimeError(self._error) from None
            if "404" in message or "NOT_FOUND" in message:
                self._available = False
                self._error = (
                    f"Google could not find Gemini model {self.model!r}. "
                    "Update GEMINI_MODEL to a model available to your account."
                )
                raise RuntimeError(self._error) from None
            raise
        text = getattr(interaction, "output_text", None)
        if not text or not text.strip():
            raise RuntimeError("Gemini returned an empty explanation.")
        return text.strip()