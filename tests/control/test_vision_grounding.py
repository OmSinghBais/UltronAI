import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from control.vision_grounding import SpatialVisionGrounder


class TestSpatialVisionGrounder(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_router = MagicMock()
        self.grounder = SpatialVisionGrounder(router=self.mock_router)

    async def test_find_element_coordinates_success(self):
        mock_img = MagicMock()
        mock_img.size = (1920, 1080)
        self.mock_router.route_vision = AsyncMock(return_value=('{"x": 400, "y": 600}', 'gemini-vision'))

        coords = await self.grounder.find_element_coordinates("blue submit button", screenshot=mock_img)
        self.assertEqual(coords, (400, 600))

    async def test_find_element_coordinates_parse_error(self):
        mock_img = MagicMock()
        mock_img.size = (1920, 1080)
        self.mock_router.route_vision = AsyncMock(return_value=('No element found', 'gemini-vision'))

        coords = await self.grounder.find_element_coordinates("missing button", screenshot=mock_img)
        self.assertIsNone(coords)

    @patch("control.vision_grounding.click")
    async def test_click_element_by_description_success(self, mock_click):
        mock_click.return_value = {"status": "ok", "action": "click", "data": {"x": 500, "y": 300}}
        with patch.object(self.grounder, "find_element_coordinates", AsyncMock(return_value=(500, 300))):
            res = await self.grounder.click_element_by_description("login button")
            self.assertEqual(res["status"], "ok")
            self.assertEqual(res["data"]["description"], "login button")
            mock_click.assert_called_once_with(x=500, y=300)

    async def test_inspect_screen_no_errors(self):
        with patch.object(self.grounder, "capture_screenshot", return_value=MagicMock()):
            self.mock_router.route_vision = AsyncMock(return_value=('NO_ERRORS', 'gemini-vision'))
            res = await self.grounder.inspect_screen_for_errors()
            self.assertEqual(res["status"], "ok")
            self.assertFalse(res["has_error"])

    async def test_inspect_screen_with_error(self):
        with patch.object(self.grounder, "capture_screenshot", return_value=MagicMock()):
            self.mock_router.route_vision = AsyncMock(
                return_value=('SyntaxError: Unexpected token on line 12. Fix: Add closing brace.', 'gemini-vision')
            )
            res = await self.grounder.inspect_screen_for_errors()
            self.assertEqual(res["status"], "ok")
            self.assertTrue(res["has_error"])
            self.assertIn("SyntaxError", res["summary"])


if __name__ == "__main__":
    unittest.main()
