import unittest
from unittest.mock import AsyncMock, MagicMock
from phone.ecosystem import PhoneEcosystemManager


class TestPhoneEcosystemManager(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_phone = MagicMock()
        self.manager = PhoneEcosystemManager(phone_controller=self.mock_phone)

    async def test_sync_clipboard_success(self):
        self.mock_phone.type_text = AsyncMock(return_value={"status": "ok", "action": "type"})
        res = await self.manager.sync_clipboard_to_phone("Copied text content")
        self.assertEqual(res["status"], "ok")
        self.assertIn("Synced text", res["response"])
        self.mock_phone.type_text.assert_called_once_with("Copied text content")

    async def test_sync_clipboard_empty_error(self):
        res = await self.manager.sync_clipboard_to_phone("")
        self.assertEqual(res["status"], "error")
        self.assertIn("empty", res["error"])

    def test_parse_incoming_notification(self):
        payload = {
            "action": "notification",
            "app": "WhatsApp",
            "sender": "Alice",
            "body": "Meeting at 3 PM"
        }
        res = self.manager.parse_incoming_notification(payload)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["sender"], "Alice")
        self.assertEqual(res["app"], "WhatsApp")
        self.assertIn("Notification from Alice on WhatsApp", res["voice_summary"])


if __name__ == "__main__":
    unittest.main()
