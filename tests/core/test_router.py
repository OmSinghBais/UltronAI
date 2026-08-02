import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.router import Router


@pytest.mark.asyncio
async def test_falls_back_to_ollama_when_no_key():
    """Verify router falls back to Ollama when no API key is configured or offline."""
    router = Router()
    router.api_key_configured = False
    with patch.object(router, "is_online", AsyncMock(return_value=False)):
        with patch.object(router, "_ollama_generate", AsyncMock(return_value="local offline answer")):
            text, route = await router.route("What is the capital of France?")

    assert route == "ollama"
    assert text == "local offline answer"


@pytest.mark.asyncio
async def test_routes_to_gemini_when_online():
    """Verify router routes to Gemini when online and configured."""
    router = Router()
    router.api_key_configured = True
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
async def test_gemini_exception_reports_error():
    """Verify router reports descriptive error under Gemini route when API fails."""
    router = Router()
    router.api_key_configured = True
    mock_gemini = MagicMock()
    mock_gemini.generate_content.side_effect = Exception("Quota exceeded")
    router.gemini = mock_gemini

    with patch.object(router, "is_online", AsyncMock(return_value=True)):
        with patch("google.generativeai.GenerativeModel", side_effect=Exception("Quota exceeded")):
            text, route = await router.route("What is quantum computing?")

    assert route == "gemini"
    assert "[Gemini API" in text
