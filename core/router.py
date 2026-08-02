import google.generativeai as genai
import httpx
from typing import Tuple, List
from config.settings import settings


class Router:
    """
    Dual-engine reasoning router for ATLAS with dynamic model discovery & multi-key rotation.
    Automatically queries Google AI Studio API for available models on each key,
    ensuring 100% compatibility with latest Gemini & Gemma models (gemini-3.6-flash, gemini-3.5-flash, gemma-4-31b-it, etc.).
    Falls back to local Ollama when offline or when no Gemini API keys are configured.
    """
    FALLBACK_MODELS: List[str] = [
        "gemma-4-31b-it",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.0-flash"
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

    def _get_active_models_for_key(self, api_key: str) -> List[str]:
        """Dynamically fetches models supporting generateContent for the key."""
        try:
            genai.configure(api_key=api_key)
            discovered = []
            for m in genai.list_models():
                if "generateContent" in getattr(m, "supported_generation_methods", []):
                    # Strip 'models/' prefix if present
                    name = m.name.replace("models/", "")
                    discovered.append(name)

            # Prioritize flagship & fast models
            priority_order = [
                "gemini-3.6-flash",
                "gemini-3.5-flash",
                "gemma-4-31b-it",
                "gemini-3.5-flash-lite",
                "gemini-3.1-flash-lite",
                "gemini-2.5-flash",
                "gemini-2.0-flash"
            ]

            ordered = [m for m in priority_order if m in discovered]
            for m in discovered:
                if m not in ordered:
                    ordered.append(m)

            return ordered if ordered else self.FALLBACK_MODELS
        except Exception:
            return self.FALLBACK_MODELS

    async def route(self, prompt: str) -> Tuple[str, str]:
        """
        Routes prompt to Gemini using dynamic model discovery and multi-key rotation pool if online.
        Returns tuple of (response_text, route_used).
        """
        if self.api_keys and await self.is_online():
            errors = []
            # Rotate through configured keys
            for idx, key in enumerate(self.api_keys, 1):
                try:
                    genai.configure(api_key=key)
                    candidate_models = self._get_active_models_for_key(key)

                    for model_name in candidate_models:
                        try:
                            model = genai.GenerativeModel(model_name)
                            resp = model.generate_content(prompt)
                            if resp and hasattr(resp, "text") and resp.text:
                                return resp.text.strip(), f"gemini (key-{idx}/{model_name})"
                        except Exception as e:
                            errors.append(f"Key-{idx} [{model_name}]: {e}")

                except Exception as e:
                    errors.append(f"Key-{idx} config: {e}")

            # If all keys/models fail
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
