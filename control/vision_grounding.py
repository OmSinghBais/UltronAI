"""
ATLAS — Spatial Vision Grounding Module
Enables natural language UI element targeting ("click the red Submit button") via Vision LLM bounding box prediction,
and proactive screen error inspection.
"""

import json
import re
from io import BytesIO
from typing import Any, Dict, Optional, Tuple

try:
    from PIL import Image, ImageGrab
except ImportError:
    Image = None
    ImageGrab = None

from control.desktop import click
from core.router import Router


class SpatialVisionGrounder:
    """
    Translates visual element descriptions into pixel coordinates (x, y) using Vision LLMs.
    """
    def __init__(self, router: Optional[Router] = None):
        self.router = router or Router()

    def capture_screenshot(self) -> Optional[Any]:
        """Captures current screen as a PIL Image."""
        if ImageGrab is None:
            return None
        try:
            return ImageGrab.grab()
        except Exception:
            return None

    async def find_element_coordinates(self, description: str, screenshot: Optional[Any] = None) -> Optional[Tuple[int, int]]:
        """
        Queries Vision LLM with a screenshot to find the (x, y) coordinates of an element.
        Expects Vision LLM to return JSON in format: {"x": <int>, "y": <int>}
        """
        img = screenshot or self.capture_screenshot()
        if img is None:
            return None

        width, height = img.size
        prompt = (
            f"Analyze this screen screenshot ({width}x{height} pixels). "
            f"Find the target UI element: '{description}'. "
            f"Return ONLY a JSON object with the approximate pixel coordinates of the center of that element: "
            f'{{"x": <integer between 0 and {width}>, "y": <integer between 0 and {height}>}}. '
            f"Do not include any explanation or markdown code block."
        )

        resp_text, _ = await self.router.route_vision(prompt, img)
        
        # Parse JSON from response
        try:
            match = re.search(r'\{.*\}', resp_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                x = int(data.get("x", -1))
                y = int(data.get("y", -1))
                if 0 <= x <= width and 0 <= y <= height:
                    return (x, y)
        except Exception:
            pass
        return None

    async def click_element_by_description(self, description: str) -> Dict[str, Any]:
        """
        Finds a UI element on screen by its description and clicks it.
        """
        coords = await self.find_element_coordinates(description)
        if coords is None:
            return {
                "status": "error",
                "error": f"Could not visually locate element '{description}' on screen."
            }
        
        x, y = coords
        result = click(x=x, y=y)
        result["data"]["description"] = description
        return result

    async def inspect_screen_for_errors(self) -> Dict[str, Any]:
        """
        Inspects current active screen for visible error stack traces or warning popups.
        """
        img = self.capture_screenshot()
        if img is None:
            return {"status": "error", "error": "Screen capture failed"}

        prompt = (
            "Scan this screen image. Is there an active error, exception stack trace, or warning modal visible? "
            "If YES, summarize the error in 1 sentence and provide a 1-sentence fix. "
            "If NO, reply exactly 'NO_ERRORS'."
        )
        resp_text, route = await self.router.route_vision(prompt, img)
        if "NO_ERRORS" in resp_text:
            return {"status": "ok", "has_error": False, "summary": "No visual errors detected on screen."}

        return {
            "status": "ok",
            "has_error": True,
            "summary": resp_text.strip(),
            "route": route
        }
