"""
ATLAS — Desktop Control Module
Provides pyautogui/pynput/subprocess wrappers for controlling the desktop.
Functions:
- open_app(app_name: str) -> dict
- type_text(text: str, interval: float = 0.0) -> dict
- click(x: int | None = None, y: int | None = None, button: str = "left", clicks: int = 1) -> dict
- screenshot(output_path: str | None = None) -> dict
- delete_path(path: str) -> dict
"""

import base64
import os
import platform
import re
import shutil
import subprocess
from io import BytesIO
from typing import Any, Dict, Optional

try:
    import pyautogui
except ImportError:
    pyautogui = None


def open_app(app_name: str) -> Dict[str, Any]:
    """
    Opens an application by name on macOS, Windows, or Linux.
    Cleans prompt noise ('in laptop', 'on my laptop', 'app') and launches via OS shell.
    """
    if not app_name or not app_name.strip():
        return {"status": "error", "error": "Application name cannot be empty"}

    action_name = "open_app"
    raw_name = app_name.strip()
    
    # Strip common command filler words
    cleaned_name = re.sub(
        r'\b(in|on|my|the|laptop|pc|desktop|app|application|please|can|you)\b',
        '',
        raw_name,
        flags=re.IGNORECASE
    ).strip()
    
    if not cleaned_name:
        cleaned_name = raw_name

    system = platform.system()

    # Windows application alias mapping
    win_alias = {
        "notepad": "notepad",
        "calculator": "calc",
        "calc": "calc",
        "paint": "mspaint",
        "chrome": "chrome",
        "edge": "msedge",
        "browser": "msedge",
        "terminal": "cmd",
        "cmd": "cmd",
        "command prompt": "cmd",
        "explorer": "explorer",
        "file manager": "explorer",
        "wordpad": "wordpad",
        "settings": "ms-settings:"
    }

    target_app = win_alias.get(cleaned_name.lower(), cleaned_name)

    try:
        if system == "Darwin":
            cmd = ["open", "-a", target_app]
            subprocess.Popen(cmd)
        elif system == "Windows":
            # Use os.system / start command for robust Windows shell execution
            os.system(f'start "" "{target_app}"')
        else:
            cmd = ["xdg-open", target_app]
            subprocess.Popen(cmd)

        return {
            "status": "ok",
            "action": action_name,
            "data": {"app_name": target_app, "raw_prompt": raw_name, "system": system},
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to open application '{target_app}': {str(e)}",
        }


def type_text(text: str, interval: float = 0.0) -> Dict[str, Any]:
    """
    Types text into the active window.
    """
    if text is None:
        return {"status": "error", "error": "Text cannot be None"}

    action_name = "type_text"
    try:
        if pyautogui is None:
            return {"status": "error", "error": "pyautogui module is not installed"}

        pyautogui.write(text, interval=interval)
        return {
            "status": "ok",
            "action": action_name,
            "data": {"length": len(text), "interval": interval},
        }
    except Exception as e:
        return {"status": "error", "error": f"Failed to type text: {str(e)}"}


def click(
    x: Optional[int] = None,
    y: Optional[int] = None,
    button: str = "left",
    clicks: int = 1,
) -> Dict[str, Any]:
    """
    Clicks mouse at (x, y) coordinates or current position.
    """
    action_name = "click"
    try:
        if pyautogui is None:
            return {"status": "error", "error": "pyautogui module is not installed"}

        valid_buttons = ["left", "right", "middle"]
        if button not in valid_buttons:
            return {
                "status": "error",
                "error": f"Invalid mouse button '{button}'. Must be one of {valid_buttons}",
            }

        if x is not None and y is not None:
            pyautogui.click(x=x, y=y, button=button, clicks=clicks)
        else:
            pyautogui.click(button=button, clicks=clicks)

        return {
            "status": "ok",
            "action": action_name,
            "data": {"x": x, "y": y, "button": button, "clicks": clicks},
        }
    except Exception as e:
        return {"status": "error", "error": f"Failed to perform click: {str(e)}"}


def screenshot(output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Captures a screenshot of the current display.
    """
    action_name = "screenshot"
    try:
        if pyautogui is None:
            return {"status": "error", "error": "pyautogui module is not installed"}

        img = pyautogui.screenshot()

        data_res: Dict[str, Any] = {}
        if output_path:
            out_dir = os.path.dirname(os.path.abspath(output_path))
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            img.save(output_path)
            data_res["output_path"] = output_path

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        b64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        data_res["base64"] = b64_str
        data_res["size"] = img.size

        return {"status": "ok", "action": action_name, "data": data_res}
    except Exception as e:
        return {"status": "error", "error": f"Failed to take screenshot: {str(e)}"}


def delete_path(path: str) -> Dict[str, Any]:
    """
    Deletes a file or directory at the specified path.
    """
    if not path or not path.strip():
        return {"status": "error", "error": "Path cannot be empty"}

    action_name = "delete_path"
    abs_path = os.path.abspath(path.strip())

    if not os.path.exists(abs_path):
        return {"status": "error", "error": f"Path does not exist: {abs_path}"}

    try:
        if os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
            target_type = "directory"
        else:
            os.remove(abs_path)
            target_type = "file"

        return {
            "status": "ok",
            "action": action_name,
            "data": {"path": abs_path, "type": target_type},
        }
    except Exception as e:
        return {"status": "error", "error": f"Failed to delete '{abs_path}': {str(e)}"}
