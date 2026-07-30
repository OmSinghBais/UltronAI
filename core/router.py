import google.generativeai as genai
import httpx
from typing import Tuple
from config.settings import settings


class Router:
    """
    Dual-engine reasoning router for ATLAS.
    Routes queries to Google Gemini API when online, falling back seamlessly
    to local Ollama (e.g. qwen2.5:3b) when offline or upon API errors.
    """
    def __init__(self):
        self.gemini = None
        if settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here":
            try:
                genai.configure(api_key=settings.gemini_api_key)
                self.gemini = genai.GenerativeModel("gemini-1.5-flash")
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
        Routes prompt to Gemini if online and configured, or falls back to Ollama.
        Returns tuple of (response_text, route_used).
        """
        if self.gemini is not None and await self.is_online():
            try:
                resp = self.gemini.generate_content(prompt)
                if resp and hasattr(resp, "text") and resp.text:
                    return resp.text.strip(), "gemini"
            except Exception:
                pass  # Fall through to local model on any Gemini failure or exception

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
