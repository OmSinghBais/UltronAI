"""
ATLAS — SQLite Command History Database
Provides asynchronous, queryable SQLite storage for conversation history, metrics, and logs using aiosqlite.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiosqlite


class HistoryDB:
    """
    Asynchronous SQLite database interface for ATLAS interaction history.
    """
    def __init__(self, db_path: str = "./storage/history.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def init_db(self) -> None:
        """Initializes tables and indexes if they do not exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    raw_text TEXT NOT NULL,
                    intent_type TEXT NOT NULL,
                    route_used TEXT NOT NULL,
                    response TEXT,
                    blocked BOOLEAN DEFAULT 0,
                    latency_ms REAL,
                    metadata TEXT
                );
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON history(timestamp);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_intent_type ON history(intent_type);")
            await db.commit()

    async def add_record(
        self,
        raw_text: str,
        intent_type: str,
        route_used: str,
        response: str,
        blocked: bool = False,
        latency_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Inserts a new record into history."""
        await self.init_db()
        meta_str = json.dumps(metadata) if metadata else "{}"
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO history (raw_text, intent_type, route_used, response, blocked, latency_ms, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (raw_text, intent_type, route_used, response, 1 if blocked else 0, latency_ms, meta_str),
            )
            await db.commit()
            return cursor.lastrowid or 0

    async def get_recent_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent history records."""
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                result = []
                for row in rows:
                    item = dict(row)
                    item["blocked"] = bool(item["blocked"])
                    try:
                        item["metadata"] = json.loads(item["metadata"])
                    except Exception:
                        pass
                    result.append(item)
                return result
