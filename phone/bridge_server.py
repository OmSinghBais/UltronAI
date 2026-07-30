"""
ATLAS — Phone Control Bridge Client Module
Python-side WebSocket client (`PhoneController`) that connects to the Android Companion app.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

try:
    import websockets
except ImportError:
    websockets = None

from config.settings import settings


class PhoneController:

    def __init__(
        self,
        phone_ip: str = settings.phone_ip,
        port: int = settings.phone_port,
    ):
        self.uri = f"ws://{phone_ip}:{port}"
        self.ws: Optional[Any] = None

    async def connect(self, timeout: float = 10.0) -> None:
        if websockets is None:
            raise ImportError("websockets module is not installed")
        self.ws = await asyncio.wait_for(
            websockets.connect(self.uri), timeout=timeout
        )

    async def disconnect(self) -> None:
        if self.ws:
            await self.ws.close()
            self.ws = None

    async def tap(self, x: int, y: int) -> Dict[str, Any]:
        if not self.ws:
            return {
                "status": "error",
                "error": "WebSocket client is not connected",
            }
        payload = {"action": "tap", "x": x, "y": y}
        await self.ws.send(json.dumps(payload))
        response = await self.ws.recv()
        return json.loads(response)

    async def type_text(self, text: str) -> Dict[str, Any]:
        if not self.ws:
            return {
                "status": "error",
                "error": "WebSocket client is not connected",
            }
        payload = {"action": "type", "text": text}
        await self.ws.send(json.dumps(payload))
        response = await self.ws.recv()
        return json.loads(response)

    async def open_app(self, package: str) -> Dict[str, Any]:
        if not self.ws:
            return {
                "status": "error",
                "error": "WebSocket client is not connected",
            }
        payload = {"action": "open_app", "package": package}
        await self.ws.send(json.dumps(payload))
        response = await self.ws.recv()
        return json.loads(response)

    async def read_screen(self) -> Dict[str, Any]:
        if not self.ws:
            return {
                "status": "error",
                "error": "WebSocket client is not connected",
            }
        payload = {"action": "read_screen"}
        await self.ws.send(json.dumps(payload))
        response = await self.ws.recv()
        return json.loads(response)
