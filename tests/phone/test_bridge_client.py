"""
Unit tests for phone/bridge_server.py Python WebSocket client.
Covers: connect/disconnect, auto-reconnect, all command methods, scroll, error paths.
"""

import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from phone.bridge_server import PhoneController


class TestPhoneController(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.controller = PhoneController(
            phone_ip="192.168.1.100", port=8765
        )

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Auto-reconnect (_ensure_connected)
    # ------------------------------------------------------------------

    @patch("phone.bridge_server.websockets")
    async def test_ensure_connected_reconnects_when_ws_is_none(self, mock_ws_module):
        """_ensure_connected() opens connection when self.ws is None."""
        mock_ws_conn = AsyncMock()
        mock_ws_conn.closed = False
        mock_ws_module.connect = AsyncMock(return_value=mock_ws_conn)

        self.controller.ws = None
        result = await self.controller._ensure_connected()

        self.assertTrue(result)
        mock_ws_module.connect.assert_called_once()

    @patch("phone.bridge_server.websockets")
    async def test_ensure_connected_reconnects_when_ws_closed(self, mock_ws_module):
        """_ensure_connected() re-opens connection when existing ws is closed."""
        mock_stale = AsyncMock()
        mock_stale.closed = True         # simulate dropped connection
        self.controller.ws = mock_stale

        mock_fresh = AsyncMock()
        mock_fresh.closed = False
        mock_ws_module.connect = AsyncMock(return_value=mock_fresh)

        result = await self.controller._ensure_connected()
        self.assertTrue(result)
        mock_ws_module.connect.assert_called_once()

    @patch("phone.bridge_server.websockets")
    async def test_ensure_connected_skips_if_already_open(self, mock_ws_module):
        """_ensure_connected() does NOT reconnect when connection is healthy."""
        mock_ws = AsyncMock()
        mock_ws.closed = False
        self.controller.ws = mock_ws

        result = await self.controller._ensure_connected()
        self.assertTrue(result)
        mock_ws_module.connect.assert_not_called()

    @patch("phone.bridge_server.websockets")
    async def test_ensure_connected_returns_false_after_all_retries_fail(self, mock_ws_module):
        """_ensure_connected() returns False if all reconnect attempts raise."""
        mock_ws_module.connect = AsyncMock(side_effect=OSError("refused"))
        self.controller.ws = None
        self.controller._max_reconnect_attempts = 2

        result = await self.controller._ensure_connected()
        self.assertFalse(result)
        self.assertEqual(mock_ws_module.connect.call_count, 2)

    @patch("phone.bridge_server.websockets")
    async def test_command_returns_error_when_cannot_connect(self, mock_ws_module):
        """tap() returns error dict when _ensure_connected() ultimately fails."""
        mock_ws_module.connect = AsyncMock(side_effect=OSError("refused"))
        self.controller.ws = None
        self.controller._max_reconnect_attempts = 1

        res = await self.controller.tap(100, 200)
        self.assertEqual(res["status"], "error")
        self.assertIn("Cannot connect", res["error"])

    # ------------------------------------------------------------------
    # tap
    # ------------------------------------------------------------------

    async def test_tap_success(self):
        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.recv.return_value = json.dumps({"status": "ok", "action": "tap"})
        self.controller.ws = mock_ws

        res = await self.controller.tap(500, 1200)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "tap")
        mock_ws.send.assert_called_once_with(
            json.dumps({"action": "tap", "x": 500, "y": 1200})
        )

    # ------------------------------------------------------------------
    # type_text
    # ------------------------------------------------------------------

    async def test_type_text_success(self):
        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.recv.return_value = json.dumps({"status": "ok", "action": "type"})
        self.controller.ws = mock_ws

        res = await self.controller.type_text("Hello World")
        self.assertEqual(res["status"], "ok")
        mock_ws.send.assert_called_once_with(
            json.dumps({"action": "type", "text": "Hello World"})
        )

    # ------------------------------------------------------------------
    # open_app
    # ------------------------------------------------------------------

    async def test_open_app_success(self):
        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.recv.return_value = json.dumps({"status": "ok", "action": "open_app"})
        self.controller.ws = mock_ws

        res = await self.controller.open_app("com.whatsapp")
        self.assertEqual(res["status"], "ok")
        mock_ws.send.assert_called_once_with(
            json.dumps({"action": "open_app", "package": "com.whatsapp"})
        )

    # ------------------------------------------------------------------
    # read_screen
    # ------------------------------------------------------------------

    async def test_read_screen_success(self):
        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.recv.return_value = json.dumps({
            "status": "ok",
            "elements": [
                {"text": "Chat", "class": "android.widget.TextView",
                 "bounds": [0, 100, 200, 300], "clickable": True}
            ],
        })
        self.controller.ws = mock_ws

        res = await self.controller.read_screen()
        self.assertEqual(res["status"], "ok")
        self.assertEqual(len(res["elements"]), 1)
        self.assertEqual(res["elements"][0]["text"], "Chat")
        mock_ws.send.assert_called_once_with(
            json.dumps({"action": "read_screen"})
        )

    # ------------------------------------------------------------------
    # scroll
    # ------------------------------------------------------------------

    async def test_scroll_down_success(self):
        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.recv.return_value = json.dumps(
            {"status": "ok", "action": "scroll", "direction": "down"}
        )
        self.controller.ws = mock_ws

        res = await self.controller.scroll("down")
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["direction"], "down")
        mock_ws.send.assert_called_once_with(
            json.dumps({"action": "scroll", "direction": "down", "x": 540, "y": 960})
        )

    async def test_scroll_up_success(self):
        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.recv.return_value = json.dumps(
            {"status": "ok", "action": "scroll", "direction": "up"}
        )
        self.controller.ws = mock_ws

        res = await self.controller.scroll("up", x=300, y=700)
        self.assertEqual(res["status"], "ok")
        mock_ws.send.assert_called_once_with(
            json.dumps({"action": "scroll", "direction": "up", "x": 300, "y": 700})
        )

    async def test_scroll_invalid_direction_rejected_client_side(self):
        """Invalid direction is rejected by Python client before hitting the network."""
        mock_ws = AsyncMock()
        mock_ws.closed = False
        self.controller.ws = mock_ws

        res = await self.controller.scroll("diagonal")  # invalid
        self.assertEqual(res["status"], "error")
        self.assertIn("Invalid scroll direction", res["error"])
        mock_ws.send.assert_not_called()   # never sent to phone

    async def test_scroll_all_directions(self):
        """All four valid directions send the correct payload."""
        for direction in ("down", "up", "left", "right"):
            mock_ws = AsyncMock()
            mock_ws.closed = False
            mock_ws.recv.return_value = json.dumps(
                {"status": "ok", "action": "scroll", "direction": direction}
            )
            self.controller.ws = mock_ws

            res = await self.controller.scroll(direction)
            self.assertEqual(res["status"], "ok", f"Failed for direction={direction}")

    # ------------------------------------------------------------------
    # Connection-lost auto-reconnect during send
    # ------------------------------------------------------------------

    @patch("phone.bridge_server.websockets")
    async def test_send_auto_reconnects_on_connection_closed(self, mock_ws_module):
        """If ws.send() raises ConnectionClosed, _send marks ws=None and the
        caller gets a clean error dict (not a raw exception)."""
        from websockets.exceptions import ConnectionClosed as WsCC

        # Simulate a broken ws that raises on send
        broken_ws = AsyncMock()
        broken_ws.closed = False
        broken_ws.send = AsyncMock(side_effect=WsCC(None, None))
        self.controller.ws = broken_ws

        # Reconnect attempt also fails for this test
        mock_ws_module.connect = AsyncMock(side_effect=OSError("still down"))
        self.controller._max_reconnect_attempts = 1

        res = await self.controller.tap(100, 200)
        self.assertEqual(res["status"], "error")
        self.assertIsNone(self.controller.ws)   # ws reset so next call retries


if __name__ == "__main__":
    unittest.main()
