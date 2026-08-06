import base64
import io
import httpx
from typing import Tuple, List, Any
from config.settings import settings


class Router:
    """
    Dual-engine reasoning router for ATLAS with dynamic model discovery, multi-key rotation, and Ollama Llama 3.2 default.
    """
    FALLBACK_MODELS: List[str] = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
    ]

    def __init__(self):
        self.api_keys: List[str] = [
            k for k in [settings.gemini_api_key, getattr(settings, "gemini_api_key_2", ""), getattr(settings, "gemini_api_key_3", "")]
            if k and k != "your_gemini_api_key_here"
        ]
        self.api_key = self.api_keys[0] if self.api_keys else None

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
        Routes prompt to Gemini if online and API key is set, or defaults to Ollama Llama 3.2.
        Returns tuple of (response_text, route_used).
        """
        if self.api_keys and await self.is_online():
            for idx, key in enumerate(self.api_keys, 1):
                for model_name in self.FALLBACK_MODELS:
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
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
                                        return parts[0]["text"].strip(), f"gemini (key-{idx}/{model_name})"
                    except Exception:
                        continue

        return await self._ollama_generate(prompt), "ollama"

    async def route_vision(self, prompt: str, image_data: Any) -> Tuple[str, str]:
        """
        Routes prompt + image to Gemini Multimodal REST API for screen visual reasoning.
        """
        if self.api_keys and await self.is_online():
            # Convert PIL image to base64 jpeg
            try:
                buf = io.BytesIO()
                image_data.save(buf, format="JPEG")
                img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            except Exception:
                img_b64 = ""

            for idx, key in enumerate(self.api_keys, 1):
                for model_name in ["gemini-2.5-flash", "gemini-1.5-flash"]:
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                        payload = {
                            "contents": [
                                {
                                    "parts": [
                                        {"text": prompt},
                                        {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
                                    ]
                                }
                            ]
                        }
                        async with httpx.AsyncClient(timeout=20.0) as client:
                            r = await client.post(url, json=payload)
                            if r.status_code == 200:
                                data = r.json()
                                candidates = data.get("candidates", [])
                                if candidates:
                                    parts = candidates[0].get("content", {}).get("parts", [])
                                    if parts and "text" in parts[0]:
                                        return parts[0]["text"].strip(), f"gemini-vision (key-{idx}/{model_name})"
                    except Exception:
                        continue

        return "[Offline Mode] Vision analysis requires active internet connection for Gemini Multimodal API.", "offline"

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
