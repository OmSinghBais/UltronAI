import tempfile
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from core.style_engine import UserStyleMimicEngine


class TestUserStyleMimicEngine(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.samples_file = Path(self.tmp_dir.name) / "user_style.json"
        self.mock_router = MagicMock()
        self.mock_db = MagicMock()
        self.engine = UserStyleMimicEngine(
            history_db=self.mock_db,
            router=self.mock_router,
            samples_file=str(self.samples_file)
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_add_and_get_style_samples(self):
        self.engine.add_style_sample("yep on it")
        self.engine.add_style_sample("cool thx")
        samples = self.engine.get_custom_samples()
        self.assertEqual(len(samples), 2)
        self.assertIn("yep on it", samples)
        self.assertIn("cool thx", samples)

    async def test_generate_user_style_reply(self):
        self.engine.add_style_sample("sure sounds good")
        self.mock_router.route = AsyncMock(return_value=('"sounds good bro"', "ollama"))

        reply, route = await self.engine.generate_user_style_reply("Are we still meeting at 5?")
        self.assertEqual(reply, "sounds good bro")
        self.assertEqual(route, "ollama")
        self.mock_router.route.assert_called_once()


if __name__ == "__main__":
    unittest.main()
