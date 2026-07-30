"""
ATLAS — Phone Control Bridge Client Module
Python-side WebSocket client (`PhoneController`) that connects to the Android Companion app.
"""

import asyncio
import json
from typing import Any, Dict, List, Literal, Optional

try:
    import websockets
    from websockets.exceptions import ConnectionClosed, WebSocketException
except ImportError:
    websockets = None
    ConnectionClosed = Exception      # type: ignore
    WebSocketException = Exception    # type: ignore

from config.settings import settings

# Valid scroll directions supported by the Android AccessibilityService
ScrollDirection = Literal["down", "up", "left", "right"]


class PhoneController:
    """
    WebSocket client that relays commands to the ATLAS Android Companion app.

    Connection lifecycle
    --------------------
    The controller uses **lazy auto-reconnect**: every public command method
    calls `_ensure_connected()` before sending, so callers never need to
    manually re-call `connect()` after a transient drop.

    Usage
    -----
    >>> pc = PhoneController()
    >>> await pc.connect()          # explicit first connect (optional)
    >>> await pc.tap(500, 1200)
    >>> await pc.scroll("up")
    >>> await pc.disconnect()
    """

    def __init__(
        self,
        phone_ip: str = settings.phone_ip,
        port: int = settings.phone_port,
        connect_timeout: float = 10.0,
        max_reconnect_attempts: int = 3,
    ):
        self.uri = f"ws://{phone_ip}:{port}"
        self.ws: Optional[Any] = None
        self._connect_timeout = connect_timeout
        self._max_reconnect_attempts = max_reconnect_attempts

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Open (or re-open) the WebSocket connection to the phone."""
        if websockets is None:
            raise ImportError("websockets module is not installed. Run: pip install websockets")
        self.ws = await asyncio.wait_for(
            websockets.connect(self.uri), timeout=self._connect_timeout
        )

    async def disconnect(self) -> None:
        """Gracefully close the WebSocket connection."""
        if self.ws:
            await self.ws.close()
            self.ws = None

    async def _ensure_connected(self) -> bool:
        """
        Auto-reconnect guard — called before every send.
        Returns True if connection is ready, False if all attempts failed.
        """
        # Check if already connected and open
        is_open = (
            self.ws is not None
            and not getattr(self.ws, "closed", True)
        )
        if is_open:
            return True

        # Attempt reconnect up to max_reconnect_attempts
        for attempt in range(1, self._max_reconnect_attempts + 1):
            try:
                await self.connect()
                return True
            except Exception:
                if attempt < self._max_reconnect_attempts:
                    await asyncio.sleep(0.5 * attempt)   # back-off: 0.5s, 1s, 1.5s …
        return False

    async def _send(self, payload: dict) -> Dict[str, Any]:
        """
        Internal helper: ensure connected, send payload, receive response.
        Returns a standardised error dict if the connection cannot be established
        or the send/recv raises.
        """
        if not await self._ensure_connected():
            return {
                "status": "error",
                "error": f"Cannot connect to phone at {self.uri} after {self._max_reconnect_attempts} attempts.",
            }
        try:
            await self.ws.send(json.dumps(payload))
            response = await self.ws.recv()
            return json.loads(response)
        except (ConnectionClosed, WebSocketException, OSError) as exc:
            self.ws = None   # mark as closed so next call triggers reconnect
            return {"status": "error", "error": f"Connection lost: {exc}"}

    # ------------------------------------------------------------------
    # Public command methods
    # ------------------------------------------------------------------

    async def tap(self, x: int, y: int) -> Dict[str, Any]:
        """
        Tap the screen at pixel coordinates (x, y).

        Response: ``{"status": "ok", "action": "tap"}``
        """
        return await self._send({"action": "tap", "x": x, "y": y})

    async def type_text(self, text: str) -> Dict[str, Any]:
        """
        Type text into the currently focused input field.

        Response: ``{"status": "ok", "action": "type"}``
        """
        return await self._send({"action": "type", "text": text})

    async def open_app(self, package: str) -> Dict[str, Any]:
        """
        Launch an installed app by its package name (e.g. ``com.whatsapp``).

        Response: ``{"status": "ok", "action": "open_app"}``
        """
        return await self._send({"action": "open_app", "package": package})

    async def read_screen(self) -> Dict[str, Any]:
        """
        Return the current screen's accessibility node tree.

        Response: ``{"status": "ok", "elements": [...]}``
        """
        return await self._send({"action": "read_screen"})

    async def scroll(
        self,
        direction: ScrollDirection = "down",
        x: int = 540,
        y: int = 960,
    ) -> Dict[str, Any]:
        """
        Scroll the screen in the given direction.

        Parameters
        ----------
        direction : "down" | "up" | "left" | "right"
            Direction to scroll.
        x, y : int
            Screen coordinates of the scroll gesture origin (default: centre).

        Response: ``{"status": "ok", "action": "scroll", "direction": "<dir>"}``
        """
        if direction not in ("down", "up", "left", "right"):
            return {
                "status": "error",
                "error": f"Invalid scroll direction '{direction}'. Must be down|up|left|right.",
            }
        return await self._send({"action": "scroll", "direction": direction, "x": x, "y": y})
