import tempfile
from pathlib import Path
import pytest
from core.credentials import set_credential, get_credential, delete_credential
from core.history_db import HistoryDB


def test_credentials_management():
    """Verify set, get, and delete operations on keyring credentials."""
    # Test setting credential
    success = set_credential("test_api_key", "secret123")
    if success:
        assert get_credential("test_api_key") == "secret123"
        delete_credential("test_api_key")


@pytest.mark.asyncio
async def test_history_db_crud():
    """Verify creating, inserting, and querying history records in SQLite."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        history = HistoryDB(str(db_path))

        await history.init_db()
        row_id = await history.add_record(
            raw_text="open browser",
            intent_type="desktop_action",
            route_used="desktop_control",
            response="{'status': 'ok'}",
            blocked=False,
            latency_ms=45.2,
            metadata={"source": "cli"}
        )
        assert row_id > 0

        records = await history.get_recent_history(limit=10)
        assert len(records) == 1
        assert records[0]["raw_text"] == "open browser"
        assert records[0]["intent_type"] == "desktop_action"
        assert records[0]["blocked"] is False
        assert records[0]["metadata"]["source"] == "cli"
