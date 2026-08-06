"""
ATLAS — Cyberpunk HUD Overlay Widget (GUI)
Provides a lightweight, semi-transparent desktop HUD display showing real-time command execution,
audio visualizer indicator, and autonomous control badges.
"""

import threading
import time
from typing import Any, Dict, List, Optional


class CyberpunkHUD:
    """
    Desktop HUD widget manager for visualizing ATLAS assistant status.
    """
    def __init__(self):
        self.active_badge = "OFFLINE"
        self.last_command = ""
        self.logs: List[str] = []
        self._is_visible = False

    def show(self):
        """Activates and displays HUD widget."""
        self._is_visible = True
        print("\n╔══════════════════════════════════════════════════════════╗")
        print("║                ⚡ ATLAS CYBERPUNK HUD ACTIVE             ║")
        print("╚══════════════════════════════════════════════════════════╝\n")

    def hide(self):
        """Hides HUD widget."""
        self._is_visible = False

    def set_badge(self, status: str):
        """Updates active status badge (e.g. 'LISTENING', 'THINKING', 'EXECUTING')."""
        self.active_badge = status
        if self._is_visible:
            print(f"[HUD BADGE]: ░▒▓ {status} ▓▒░")

    def add_log(self, text: str):
        """Appends log entry to HUD execution stream."""
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {text}"
        self.logs.append(entry)
        if len(self.logs) > 20:
            self.logs.pop(0)
        if self._is_visible:
            print(f"[HUD STREAM]: {entry}")

    def render_state(self) -> Dict[str, Any]:
        """Returns JSON state representation of HUD for frontend GUI binding."""
        return {
            "visible": self._is_visible,
            "badge": self.active_badge,
            "logs": self.logs[-5:],
        }
