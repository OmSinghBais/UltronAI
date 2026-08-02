import google.generativeai as genai
import httpx
from typing import Tuple, List
from config.settings import settings


class Router:
    """
    Dual-engine reasoning router for ATLAS.
    Routes queries to Google Gemini API when an API key is configured,
    trying available model identifiers (gemma-4-31b-it, gemini-2.0-flash, etc.).
    Falls back to local Ollama when offline or when no Gemini API key is configured.
    """
    PREFERRED_MODELS: List[str] = [
        "gemma-4-31b-it",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash-latest",
        "gemini-2.5-flash"
    ]

    def __init__(self):
        self.gemini = None
        self.api_key_configured = False
        if settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here":
            try:
                genai.configure(api_key=settings.gemini_api_key)
                self.gemini = genai.GenerativeModel("gemma-4-31b-it")
                self.api_key_configured = True
            except Exception:
                self.gemini = None

    async def is_online(self) -> bool:
        """Checks internet connectivity by attempting a fast GET ping."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get("https://www.google.com")
                return r.status_code == 200
        except Exception:
            return False

    async def route(self, prompt: str) -> Tuple[str, str]:
        """
        Routes prompt to Gemini if configured and online.
        Returns tuple of (response_text, route_used).
        """
        if self.api_key_configured and await self.is_online():
            errors = []
            # Try preferred models in sequence
            for model_name in self.PREFERRED_MODELS:
                try:
                    model = genai.GenerativeModel(model_name)
                    resp = model.generate_content(prompt)
                    if resp and hasattr(resp, "text") and resp.text:
                        return resp.text.strip(), f"gemini ({model_name})"
                except Exception as e:
                    errors.append(f"{model_name}: {e}")

            # If API key is present but Google Gemini returns error (e.g. rate limit 429 or 403)
            error_details = errors[0] if errors else "API call failed"
            if "429" in error_details or "Quota" in error_details:
                return (
                    "[Gemini API Quota Exceeded] Free tier rate limit reached on your key. Please retry in 30 seconds or generate a key at https://aistudio.google.com/",
                    "gemini"
                )
            elif "403" in error_details or "denied" in error_details.lower():
                return (
                    "[Gemini API Key Error] Key was rejected by Google AI Studio. Please use a valid key starting with 'AIzaSy...' from https://aistudio.google.com/",
                    "gemini"
                )
            else:
                return (
                    f"[Gemini API Error] {error_details[:150]}",
                    "gemini"
                )

        return await self._ollama_generate(prompt), "ollama"

    async def _ollama_generate(self, prompt: str) -> str:
        """Sends generation request to local Ollama server."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(
                    f"{settings.ollama_host}/api/generate",
                    json={
                        "model": settings.ollama_model,
                        "prompt": prompt,
                        "stream": False
                    },
                )
                if r.status_code == 200:
                    return r.json().get("response", "").strip()
                return f"[Ollama Service Error] Server returned HTTP {r.status_code}"
        except Exception as e:
            return f"[Offline Fallback Active] Local Ollama at {settings.ollama_host} unreachable: {e}"
