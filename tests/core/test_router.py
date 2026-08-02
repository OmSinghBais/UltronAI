import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.router import Router


@pytest.mark.asyncio
async def test_falls_back_to_ollama_when_no_keys():
    """Verify router falls back to Ollama when no API keys are configured or offline."""
    router = Router()
    router.api_keys = []
    with patch.object(router, "is_online", AsyncMock(return_value=False)):
        with patch.object(router, "_ollama_generate", AsyncMock(return_value="local offline answer")):
            text, route = await router.route("What is the capital of France?")

    assert route == "ollama"
    assert text == "local offline answer"


@pytest.mark.asyncio
async def test_routes_to_gemini_when_online():
    """Verify router routes to Gemini when online and keys are configured."""
    router = Router()
    router.api_keys = ["mock-key-1", "mock-key-2"]
    mock_resp = MagicMock()
    mock_resp.text = "Paris is the capital of France."

    with patch.object(router, "is_online", AsyncMock(return_value=True)):
        with patch("google.generativeai.GenerativeModel") as mock_model_cls:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_resp
            mock_model_cls.return_value = mock_model

            text, route = await router.route("What is the capital of France?")

    assert "gemini" in route
    assert text == "Paris is the capital of France."


@pytest.mark.asyncio
async def test_multi_key_rotation_on_exception():
    """Verify router tries secondary key when primary key fails."""
    router = Router()
    router.api_keys = ["key-1", "key-2"]

    with patch.object(router, "is_online", AsyncMock(return_value=True)):
        with patch("google.generativeai.GenerativeModel") as mock_model_cls:
            mock_model_1 = MagicMock()
            mock_model_1.generate_content.side_effect = Exception("Quota limit key 1")

            mock_model_2 = MagicMock()
            mock_resp_2 = MagicMock()
            mock_resp_2.text = "Success on key 2"
            mock_model_2.generate_content.return_value = mock_resp_2

            mock_model_cls.side_effect = [mock_model_1] * len(Router.PREFERRED_MODELS) + [mock_model_2]

            text, route = await router.route("Hello world")

    assert "gemini" in route
    assert text == "Success on key 2"
