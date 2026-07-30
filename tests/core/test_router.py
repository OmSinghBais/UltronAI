import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.router import Router


@pytest.mark.asyncio
async def test_falls_back_to_ollama_when_offline():
    """Verify router falls back to Ollama when internet is offline."""
    router = Router()
    with patch.object(router, "is_online", AsyncMock(return_value=False)):
        with patch.object(router, "_ollama_generate", AsyncMock(return_value="local offline answer")):
            text, route = await router.route("What is the capital of France?")

    assert route == "ollama"
    assert text == "local offline answer"


@pytest.mark.asyncio
async def test_routes_to_gemini_when_online():
    """Verify router routes to Gemini when online and configured."""
    router = Router()
    mock_gemini = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "Paris is the capital of France."
    mock_gemini.generate_content.return_value = mock_resp
    router.gemini = mock_gemini

    with patch.object(router, "is_online", AsyncMock(return_value=True)):
        text, route = await router.route("What is the capital of France?")

    assert route == "gemini"
    assert text == "Paris is the capital of France."


@pytest.mark.asyncio
async def test_falls_back_to_ollama_on_gemini_exception():
    """Verify router falls back to Ollama when Gemini API raises an exception (e.g. quota exceeded)."""
    router = Router()
    mock_gemini = MagicMock()
    mock_gemini.generate_content.side_effect = Exception("Quota exceeded / Network timeout")
    router.gemini = mock_gemini

    with patch.object(router, "is_online", AsyncMock(return_value=True)):
        with patch.object(router, "_ollama_generate", AsyncMock(return_value="fallback offline response")):
            text, route = await router.route("What is quantum computing?")

    assert route == "ollama"
    assert text == "fallback offline response"
