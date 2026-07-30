import json
import tempfile
from pathlib import Path
import pytest
from config.settings import Settings
from core.intents import Intent, IntentType
from core.audit_log import AuditLogger


def test_settings_default_fallback():
    """Verify Settings loads with default values when environment variables are unset."""
    settings = Settings()
    assert settings.ollama_model == "qwen2.5:3b"
    assert settings.ollama_host == "http://localhost:11434"
    assert settings.confirmation_timeout_s == 15
    assert settings.phone_port == 8765


def test_audit_logger_write_and_read():
    """Verify AuditLogger writes entries in JSONL format and can be parsed correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_audit.jsonl"
        logger = AuditLogger(log_path)

        intent = Intent(
            type=IntentType.QUERY,
            raw_text="what time is it",
            language="en",
            requires_confirmation=False
        )

        entry = logger.log(
            intent=intent,
            route_used="gemini",
            result="The time is 12:45 PM",
            blocked=False,
            latency_ms=120.5
        )

        assert log_path.exists()

        with log_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data["raw_text"] == "what time is it"
            assert data["intent_type"] == "query"
            assert data["route_used"] == "gemini"
            assert data["result"] == "The time is 12:45 PM"
            assert data["blocked"] is False
            assert data["latency_ms"] == 120.5
            assert "ts" in data
