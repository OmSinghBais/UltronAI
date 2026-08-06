import httpx
from typing import Tuple
from config.settings import settings


class Router:
    """
    Reasoning router for ATLAS powered primarily by local Ollama (Llama 3.2).
    Also supports optional Gemini REST API fallback/online queries if configured.
    """
    def __init__(self):
        self.api_key = settings.gemini_api_key if (settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here") else None

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
        Routes prompt to Ollama 3.2 (llama3.2) by default, or Gemini via REST if configured and online.
        Returns tuple of (response_text, route_used).
        """
        # Default to local Ollama 3.2
        if not self.api_key or not await self.is_online():
            return await self._ollama_generate(prompt), "ollama"

        # Optional Gemini REST call if API key configured and online
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    url,
                    json={"contents": [{"parts": [{"text": prompt}]}]}
                )
                if r.status_code == 200:
                    data = r.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip(), "gemini"
        except Exception:
            pass  # Fall back to local Ollama

        return await self._ollama_generate(prompt), "ollama"

    async def _ollama_generate(self, prompt: str) -> str:
        """Sends generation request to local Ollama server (Llama 3.2)."""
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
            return f"[Offline Fallback Active] Local Ollama ({settings.ollama_model}) at {settings.ollama_host} unreachable: {e}"
