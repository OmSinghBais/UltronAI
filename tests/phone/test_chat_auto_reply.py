import unittest
from unittest.mock import AsyncMock, MagicMock
from phone.chat_auto_reply import ChatAutoReplier


class TestChatAutoReplier(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_style = MagicMock()
        self.mock_phone = MagicMock()
        self.replier = ChatAutoReplier(style_engine=self.mock_style, phone_controller=self.mock_phone)

    async def test_reply_to_chat_notification_preview_only(self):
        self.mock_style.generate_user_style_reply = AsyncMock(return_value=("yeah sure 5pm works", "ollama"))

        payload = {"sender": "Bob", "body": "What time should we meet?", "app": "WhatsApp"}
        res = await self.replier.reply_to_chat_notification(payload, force_send=False)

        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["generated_reply"], "yeah sure 5pm works")
        self.assertFalse(res["sent"])
        self.mock_phone.type_text.assert_not_called()

    async def test_reply_to_chat_notification_force_send(self):
        self.mock_style.generate_user_style_reply = AsyncMock(return_value=("on my way!", "ollama"))
        self.mock_phone.type_text = AsyncMock(return_value={"status": "ok", "action": "type"})

        payload = {"sender": "Bob", "body": "Where are you?", "app": "SMS"}
        res = await self.replier.reply_to_chat_notification(payload, force_send=True)

        self.assertEqual(res["status"], "ok")
        self.assertTrue(res["sent"])
        self.mock_phone.type_text.assert_called_once_with("on my way!")


if __name__ == "__main__":
    unittest.main()
