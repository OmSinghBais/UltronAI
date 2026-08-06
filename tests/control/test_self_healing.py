import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from control.self_healing import SelfHealingExecutor, MacroEngine


class TestSelfHealingAndMacros(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_grounder = MagicMock()
        self.executor = SelfHealingExecutor(grounder=self.mock_grounder)
        self.macro_engine = MacroEngine()

    async def test_self_healing_primary_success(self):
        primary_fn = MagicMock(return_value={"status": "ok", "action": "click"})
        res = await self.executor.execute_with_self_healing(primary_fn, "submit button")
        self.assertEqual(res["status"], "ok")
        primary_fn.assert_called_once()
        self.mock_grounder.click_element_by_description.assert_not_called()

    async def test_self_healing_fallback_to_vision(self):
        primary_fn = MagicMock(return_value={"status": "error", "error": "Element not clickable"})
        self.mock_grounder.click_element_by_description = AsyncMock(
            return_value={"status": "ok", "action": "click", "data": {"description": "submit button"}}
        )

        res = await self.executor.execute_with_self_healing(primary_fn, "submit button")
        self.assertEqual(res["status"], "ok")
        self.mock_grounder.click_element_by_description.assert_called_once_with("submit button")

    def test_macro_registration_and_retrieval(self):
        self.macro_engine.register_macro("start work mode", ["open vs code", "open chrome", "silence phone"])
        cmds = self.macro_engine.get_macro("START WORK MODE")
        self.assertIsNotNone(cmds)
        self.assertEqual(len(cmds), 3)
        self.assertEqual(cmds[0], "open vs code")


if __name__ == "__main__":
    unittest.main()
