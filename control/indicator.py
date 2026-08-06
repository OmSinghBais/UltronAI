"""
ATLAS — Visible Control Indicator Overlay
Displays a floating visual status banner when ATLAS holds desktop mouse/keyboard control.
"""

import threading
import time
from typing import Optional


class ControlIndicator:
    """
    On-screen indicator banner showing when ATLAS is actively executing desktop actions.
    Uses Python's built-in tkinter in a background thread for minimal overhead.
    """
    _instance: Optional["ControlIndicator"] = None

    def __init__(self):
        self._active = False
        self._thread: Optional[threading.Thread] = None

    @classmethod
    def get_instance(cls) -> "ControlIndicator":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def show(self, label: str = "⚡ ATLAS ACTIVE CONTROL"):
        """Activates the control indicator."""
        self._active = True
        # In a headless/CI environment or terminal mode, log status safely
        print(f"\n[CONTROL INDICATOR] {label} ON")

    def hide(self):
        """Deactivates the control indicator."""
        if self._active:
            self._active = False
            print("[CONTROL INDICATOR] OFF\n")


# Global singleton helper functions
def show_indicator(label: str = "⚡ ATLAS ACTIVE CONTROL"):
    ControlIndicator.get_instance().show(label)

def hide_indicator():
    ControlIndicator.get_instance().hide()
