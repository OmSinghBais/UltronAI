"""
Unit tests for control/browser.py
"""

import unittest
from unittest.mock import MagicMock, patch

from control.browser import fill_form, navigate, read_page, search


class TestBrowserControl(unittest.TestCase):

    @patch("control.browser.sync_playwright")
    def test_navigate_success(self, mock_playwright):
        mock_p = MagicMock()
        mock_playwright.return_value.__enter__.return_value = mock_p
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_p.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.title.return_value = "Example Domain"
        mock_page.url = "https://example.com"
        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto.return_value = mock_response

        res = navigate("example.com")
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "navigate")
        self.assertEqual(res["data"]["title"], "Example Domain")
        self.assertEqual(res["data"]["url"], "https://example.com")
        self.assertEqual(res["data"]["status_code"], 200)

    def test_navigate_empty_url(self):
        res = navigate("")
        self.assertEqual(res["status"], "error")
        self.assertIn("URL cannot be empty", res["error"])

    @patch("control.browser.sync_playwright", None)
    def test_navigate_missing_playwright(self):
        res = navigate("example.com")
        self.assertEqual(res["status"], "error")
        self.assertIn("not installed", res["error"])

    @patch("control.browser.sync_playwright")
    def test_navigate_exception(self, mock_playwright):
        mock_p = MagicMock()
        mock_playwright.return_value.__enter__.return_value = mock_p
        mock_p.chromium.launch.side_effect = Exception("Browser crashed")

        res = navigate("example.com")
        self.assertEqual(res["status"], "error")
        self.assertIn("Failed to navigate", res["error"])

    @patch("control.browser.navigate")
    def test_search_google_success(self, mock_navigate):
        mock_navigate.return_value = {
            "status": "ok",
            "action": "navigate",
            "data": {
                "url": "https://www.google.com/search?q=test",
                "title": "Google Search",
                "status_code": 200,
            },
        }

        res = search("test query", engine="google")
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "search")
        self.assertEqual(res["data"]["query"], "test query")
        self.assertEqual(res["data"]["engine"], "google")

    def test_search_invalid_engine(self):
        res = search("test", engine="unsupported_engine")
        self.assertEqual(res["status"], "error")
        self.assertIn("Unsupported search engine", res["error"])

    def test_search_empty_query(self):
        res = search("")
        self.assertEqual(res["status"], "error")
        self.assertIn("Search query cannot be empty", res["error"])

    @patch("control.browser.sync_playwright")
    def test_fill_form_success(self, mock_playwright):
        mock_p = MagicMock()
        mock_playwright.return_value.__enter__.return_value = mock_p
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_p.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.title.return_value = "Login Page"
        mock_page.url = "https://example.com/login"

        res = fill_form(
            "https://example.com/login", "#username", "testuser", submit=True
        )
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "fill_form")
        self.assertEqual(res["data"]["selector"], "#username")
        self.assertEqual(res["data"]["filled_value"], "testuser")
        self.assertTrue(res["data"]["submitted"])
        mock_page.fill.assert_called_once_with("#username", "testuser")
        mock_page.press.assert_called_once_with("#username", "Enter")

    def test_fill_form_empty_selector(self):
        res = fill_form("https://example.com", "", "value")
        self.assertEqual(res["status"], "error")
        self.assertIn("Selector cannot be empty", res["error"])

    @patch("control.browser.sync_playwright")
    def test_read_page_success(self, mock_playwright):
        mock_p = MagicMock()
        mock_playwright.return_value.__enter__.return_value = mock_p
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_p.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.title.return_value = "Article Title"
        mock_page.url = "https://example.com/article"
        mock_page.inner_text.return_value = (
            "This is the body content of the article."
        )

        res = read_page("https://example.com/article")
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "read_page")
        self.assertEqual(res["data"]["title"], "Article Title")
        self.assertEqual(
            res["data"]["content"], "This is the body content of the article."
        )
        self.assertEqual(res["data"]["content_length"], 40)

    def test_read_page_empty_url(self):
        res = read_page("")
        self.assertEqual(res["status"], "error")
        self.assertIn("URL cannot be empty", res["error"])


if __name__ == "__main__":
    unittest.main()
