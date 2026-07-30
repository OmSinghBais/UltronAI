import tempfile
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from core.orchestrator import Orchestrator
from core.intents import IntentType
from core.audit_log import AuditLogger
from phone.bridge_server import PhoneController


@pytest.fixture
def temp_audit_logger():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield AuditLogger(Path(tmpdir) / "test_audit.jsonl")


@pytest.fixture
def mock_orchestrator(temp_audit_logger):
    orchestrator = Orchestrator(audit=temp_audit_logger)
    orchestrator.tts = MagicMock()
    orchestrator.router = MagicMock()
    orchestrator.router.route = AsyncMock(return_value=("Mock router answer", "gemini"))
    return orchestrator


def test_intent_classification(mock_orchestrator):
    """Verify non-sensitive vs sensitive intent classification."""
    intent_query = mock_orchestrator.classify_intent("what is the weather today")
    assert intent_query.type == IntentType.QUERY
    assert intent_query.requires_confirmation is False

    intent_open = mock_orchestrator.classify_intent("open notepad")
    assert intent_open.type == IntentType.DESKTOP_ACTION
    assert intent_open.requires_confirmation is False

    intent_delete = mock_orchestrator.classify_intent("delete storage/temp.txt")
    assert intent_delete.type == IntentType.SENSITIVE_ACTION
    assert intent_delete.requires_confirmation is True


@pytest.mark.asyncio
async def test_query_command_execution(mock_orchestrator):
    """Verify informational queries execute autonomously without confirmation."""
    res = await mock_orchestrator.process_command("what is python")

    assert res["status"] == "ok"
    assert res["route"] == "gemini"
    assert res["response"] == "Mock router answer"
    mock_orchestrator.tts.speak.assert_called_with("Mock router answer")


@pytest.mark.asyncio
async def test_sensitive_action_confirmed(mock_orchestrator):
    """Verify sensitive action proceeds when confirm_fn returns True."""
    with patch("core.orchestrator.delete_path", return_value={"status": "ok", "action": "deleted storage/temp.txt"}):
        res = await mock_orchestrator.process_command(
            "delete storage/temp.txt",
            confirm_fn=lambda prompt: True
        )

    assert res["status"] == "ok"
    assert "deleted storage/temp.txt" in res["action"]


@pytest.mark.asyncio
async def test_sensitive_action_cancelled(mock_orchestrator):
    """Verify sensitive action aborts and logs blocked entry when confirm_fn returns False."""
    res = await mock_orchestrator.process_command(
        "delete storage/temp.txt",
        confirm_fn=lambda prompt: False
    )

    assert res["status"] == "cancelled"
    assert res["reason"] == "not confirmed"
    mock_orchestrator.tts.speak.assert_called_with("Action cancelled.")


def test_phone_intent_classification(mock_orchestrator):
    """Verify phone commands are classified as PHONE_ACTION intent."""
    intent = mock_orchestrator.classify_intent("tap phone on the home button")
    assert intent.type == IntentType.PHONE_ACTION
    assert intent.requires_confirmation is False

    intent_read = mock_orchestrator.classify_intent("read screen now")
    assert intent_read.type == IntentType.PHONE_ACTION


@pytest.mark.asyncio
async def test_phone_action_no_controller(mock_orchestrator):
    """Verify graceful error when phone controller not injected."""
    mock_orchestrator.phone = None
    res = await mock_orchestrator.process_command("tap phone")
    assert res["status"] == "error"
    assert "PhoneController not connected" in res["error"]


@pytest.mark.asyncio
async def test_phone_action_dispatched(mock_orchestrator):
    """Verify phone action routes to the PhoneController when connected."""
    mock_phone = MagicMock(spec=PhoneController)
    mock_phone.read_screen = AsyncMock(return_value={"status": "ok", "content": "Home screen text"})
    mock_orchestrator.phone = mock_phone

    res = await mock_orchestrator.process_command("read screen now")
    assert res["status"] == "ok"
    mock_phone.read_screen.assert_awaited_once()
