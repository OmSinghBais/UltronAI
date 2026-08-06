import unittest
from gui.hud import CyberpunkHUD


class TestCyberpunkHUD(unittest.TestCase):

    def setUp(self):
        self.hud = CyberpunkHUD()

    def test_show_and_hide(self):
        self.hud.show()
        self.assertTrue(self.hud._is_visible)
        self.hud.hide()
        self.assertFalse(self.hud._is_visible)

    def test_set_badge_and_add_log(self):
        self.hud.show()
        self.hud.set_badge("THINKING")
        self.assertEqual(self.hud.active_badge, "THINKING")

        self.hud.add_log("Executing tap action")
        state = self.hud.render_state()
        self.assertEqual(state["badge"], "THINKING")
        self.assertEqual(len(state["logs"]), 1)
        self.assertIn("Executing tap action", state["logs"][0])


if __name__ == "__main__":
    unittest.main()
