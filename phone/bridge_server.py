import asyncio
import json
import logging
from typing import Optional, List, Dict, Any
import websockets

from config.settings import settings

logger = logging.getLogger(__name__)

class PhoneController:
    """
    WebSocket client on laptop connecting to the Phone Companion App's WebSocket Server.
    """
    def __init__(self, phone_ip: str = settings.phone_ip, port: int = settings.phone_port):
        self.uri = f"ws://{phone_ip}:{port}"
        self.ws: Optional[websockets.WebSocketClientProtocol] = None

    async def connect(self):
        """Connect to the phone WebSocket server."""
        logger.info(f"Connecting to phone WebSocket server at {self.uri}")
        self.ws = await websockets.connect(self.uri)
        logger.info("Connected to phone companion WebSocket server.")

    async def disconnect(self):
        """Disconnect from the phone WebSocket server."""
        if self.ws:
            await self.ws.close()
            self.ws = None
            logger.info("Disconnected from phone companion WebSocket server.")

    async def _ensure_connection(self):
        """Ensure WebSocket connection is active."""
        if self.ws is None:
            await self.connect()

    async def tap(self, x: int, y: int) -> Dict[str, Any]:
        """Send tap command to phone at screen coordinates (x, y)."""
        await self._ensure_connection()
        command = {"action": "tap", "x": x, "y": y}
        await self.ws.send(json.dumps(command))
        response = json.loads(await self.ws.recv())
        return response

    async def type_text(self, text: str) -> Dict[str, Any]:
        """Send type command to phone to enter text into focused field."""
        await self._ensure_connection()
        command = {"action": "type", "text": text}
        await self.ws.send(json.dumps(command))
        response = json.loads(await self.ws.recv())
        return response

    async def open_app(self, package: str) -> Dict[str, Any]:
        """Send open_app command to launch application by package name."""
        await self._ensure_connection()
        command = {"action": "open_app", "package": package}
        await self.ws.send(json.dumps(command))
        response = json.loads(await self.ws.recv())
        return response

    async def read_screen(self) -> List[Dict[str, Any]]:
        """Send read_screen command and return list of UI screen elements."""
        await self._ensure_connection()
        command = {"action": "read_screen"}
        await self.ws.send(json.dumps(command))
        response = json.loads(await self.ws.recv())
        return response.get("elements", [])
