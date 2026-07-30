import json
import time
from pathlib import Path
from typing import Union, Optional, Dict, Any
from core.intents import Intent


class AuditLogger:
    """
    Append-only JSONL Audit Logger for ATLAS commands and actions.
    Every command, routing decision, and execution result is recorded with a timestamp.
    """
    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        intent: Intent,
        route_used: str,
        result: str,
        blocked: bool = False,
        latency_ms: Optional[float] = None
    ) -> Dict[str, Any]:
        entry = {
            "ts": time.time(),
            "raw_text": intent.raw_text,
            "intent_type": intent.type.value,
            "route_used": route_used,
            "blocked": blocked,
            "result": result,
            "latency_ms": latency_ms,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry
