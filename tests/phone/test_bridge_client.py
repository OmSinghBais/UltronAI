"""
Unit tests for phone/bridge_server.py Python WebSocket client
"""

import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from phone.bridge_server import PhoneController


class TestPhoneController(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.controller = PhoneController(
            phone_ip="192.168.1.100", port=8765
        )

    @patch("phone.bridge_server.websockets")
    async def test_connect_and_disconnect(self, mock_ws_module):
        mock_ws_conn = AsyncMock()
        mock_ws_module.connect = AsyncMock(return_value=mock_ws_conn)

        await self.controller.connect()
        self.assertIsNotNone(self.controller.ws)
        mock_ws_module.connect.assert_called_once_with("ws://192.168.1.100:8765")

        await self.controller.disconnect()
        self.assertIsNone(self.controller.ws)
        mock_ws_conn.close.assert_called_once()

    async def test_tap_not_connected(self):
        res = await self.controller.tap(500, 1000)
        self.assertEqual(res["status"], "error")
        self.assertIn("not connected", res["error"])

    async def test_tap_success(self):
        mock_ws = AsyncMock()
        mock_ws.recv.return_value = json.dumps(
            {"status": "ok", "action": "tap"}
        )
        self.controller.ws = mock_ws

        res = await self.controller.tap(500, 1200)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "tap")
        mock_ws.send.assert_called_once_with(
            json.dumps({"action": "tap", "x": 500, "y": 1200})
        )

    async def test_type_text_success(self):
        mock_ws = AsyncMock()
        mock_ws.recv.return_value = json.dumps(
            {"status": "ok", "action": "type"}
        )
        self.controller.ws = mock_ws

        res = await self.controller.type_text("Hello World")
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "type")
        mock_ws.send.assert_called_once_with(
            json.dumps({"action": "type", "text": "Hello World"})
        )

    async def test_open_app_success(self):
        mock_ws = AsyncMock()
        mock_ws.recv.return_value = json.dumps(
            {"status": "ok", "action": "open_app"}
        )
        self.controller.ws = mock_ws

        res = await self.controller.open_app("com.whatsapp")
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "open_app")
        mock_ws.send.assert_called_once_with(
            json.dumps({"action": "open_app", "package": "com.whatsapp"})
        )

    async def test_read_screen_success(self):
        mock_ws = AsyncMock()
        mock_ws.recv.return_value = json.dumps(
            {
                "status": "ok",
                "elements": [
                    {
                        "text": "Chat",
                        "class": "android.widget.TextView",
                        "bounds": [0, 100, 200, 300],
                        "clickable": True,
                    }
                ],
            }
        )
        self.controller.ws = mock_ws

        res = await self.controller.read_screen()
        self.assertEqual(res["status"], "ok")
        self.assertEqual(len(res["elements"]), 1)
        self.assertEqual(res["elements"][0]["text"], "Chat")
        mock_ws.send.assert_called_once_with(
            json.dumps({"action": "read_screen"})
        )


if __name__ == "__main__":
    unittest.main()
