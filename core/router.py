import google.generativeai as genai
import httpx
from typing import Tuple, List
from config.settings import settings


class Router:
    """
    Dual-engine reasoning router for ATLAS with multi-key automatic rotation pool.
    Tries configured API keys in order (Primary -> Secondary -> Tertiary),
    querying models (gemma-4-31b-it, gemini-2.0-flash, etc.).
    Falls back to local Ollama when offline or when no Gemini API keys are configured.
    """
    PREFERRED_MODELS: List[str] = [
        "gemma-4-31b-it",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash-latest",
        "gemini-2.5-flash"
    ]

    def __init__(self):
        self.api_keys: List[str] = [
            k for k in [settings.gemini_api_key, settings.gemini_api_key_2, settings.gemini_api_key_3]
            if k and k != "your_gemini_api_key_here"
        ]

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
        Routes prompt to Gemini using multi-key automatic rotation pool if online.
        Returns tuple of (response_text, route_used).
        """
        if self.api_keys and await self.is_online():
            errors = []
            # Rotate through configured keys
            for idx, key in enumerate(self.api_keys, 1):
                try:
                    genai.configure(api_key=key)
                except Exception as e:
                    errors.append(f"Key {idx} config error: {e}")
                    continue

                for model_name in self.PREFERRED_MODELS:
                    try:
                        model = genai.GenerativeModel(model_name)
                        resp = model.generate_content(prompt)
                        if resp and hasattr(resp, "text") and resp.text:
                            return resp.text.strip(), f"gemini (key-{idx}/{model_name})"
                    except Exception as e:
                        errors.append(f"Key-{idx} [{model_name}]: {e}")

            # If all keys/models hit quota limits or errors
            error_details = errors[0] if errors else "API call failed"
            if "429" in error_details or "Quota" in error_details:
                return (
                    f"[Gemini Multi-Key Quota Limit] Tried all {len(self.api_keys)} keys. Rate limit reached. Generate keys at https://aistudio.google.com/",
                    "gemini"
                )
            else:
                return (
                    f"[Gemini Multi-Key Error] {error_details[:150]}",
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
