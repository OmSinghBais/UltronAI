import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.router import Router


@pytest.mark.asyncio
async def test_falls_back_to_ollama_when_offline():
    """Verify router falls back to Ollama (llama3.2) when internet is offline."""
    router = Router()
    with patch.object(router, "is_online", AsyncMock(return_value=False)):
        with patch.object(router, "_ollama_generate", AsyncMock(return_value="local llama3.2 answer")):
            text, route = await router.route("What is the capital of France?")

    assert route == "ollama"
    assert text == "local llama3.2 answer"


@pytest.mark.asyncio
async def test_routes_to_gemini_when_online():
    """Verify router routes to Gemini when online and API key is set."""
    router = Router()
    router.api_key = "test_key"

    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 200
    mock_post_resp.json.return_value = {
        "candidates": [
            {"content": {"parts": [{"text": "Paris is the capital of France."}]}}
        ]
    }

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_post_resp)

    with patch.object(router, "is_online", AsyncMock(return_value=True)):
        with patch("httpx.AsyncClient", return_value=mock_client):
            text, route = await router.route("What is the capital of France?")

    assert route == "gemini"
    assert text == "Paris is the capital of France."


@pytest.mark.asyncio
async def test_falls_back_to_ollama_on_gemini_exception():
    """Verify router falls back to Ollama when Gemini API raises an exception or fails."""
    router = Router()
    router.api_key = "test_key"

    with patch.object(router, "is_online", AsyncMock(return_value=True)):
        with patch("httpx.AsyncClient", side_effect=Exception("Network error")):
            with patch.object(router, "_ollama_generate", AsyncMock(return_value="fallback llama3.2 response")):
                text, route = await router.route("What is quantum computing?")

    assert route == "ollama"
    assert text == "fallback llama3.2 response"
