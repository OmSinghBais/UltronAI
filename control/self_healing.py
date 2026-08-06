"""
ATLAS — Self-Healing Automation & Custom Voice Macro Engine
Provides automatic vision-assisted retries for failed desktop/browser actions,
and handles custom voice macro creation and execution.
"""

from typing import Any, Callable, Dict, List, Optional
from control.vision_grounding import SpatialVisionGrounder
from core.history_db import HistoryDB


class SelfHealingExecutor:
    """
    Executes actions with self-healing retry logic using Vision Grounding upon failure.
    """
    def __init__(self, grounder: Optional[SpatialVisionGrounder] = None):
        self.grounder = grounder or SpatialVisionGrounder()

    async def execute_with_self_healing(self, action_fn: Callable[..., Any], element_description: str, *args, **kwargs) -> Dict[str, Any]:
        """
        Executes action_fn. If it returns status=='error', falls back to vision grounding.
        """
        try:
            res = action_fn(*args, **kwargs)
            if isinstance(res, dict) and res.get("status") == "ok":
                return res
        except Exception:
            pass

        # Fallback: Visual grounding retry
        print(f"[SELF-HEALING]: Action failed. Retrying via visual grounding for '{element_description}'...")
        return await self.grounder.click_element_by_description(element_description)


class MacroEngine:
    """
    Stores and executes custom multi-command voice macros ("Start Work Mode").
    """
    def __init__(self, history_db: Optional[HistoryDB] = None):
        self.history_db = history_db or HistoryDB()
        self.macros: Dict[str, List[str]] = {}

    def register_macro(self, macro_name: str, commands: List[str]):
        """Registers a new voice macro."""
        name_clean = macro_name.lower().strip()
        self.macros[name_clean] = commands
        print(f"[MACRO REGISTERED]: '{name_clean}' -> {len(commands)} commands")

    def get_macro(self, macro_name: str) -> Optional[List[str]]:
        """Retrieves commands for a registered macro."""
        return self.macros.get(macro_name.lower().strip())
