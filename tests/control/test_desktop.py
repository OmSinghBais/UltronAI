"""
Unit tests for control/desktop.py
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from PIL import Image

from control.desktop import click, delete_path, open_app, screenshot, type_text


class TestDesktopControl(unittest.TestCase):

    @patch("subprocess.Popen")
    @patch("os.startfile", create=True)
    def test_open_app_success(self, mock_startfile, mock_popen):
        res = open_app("Calculator")
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "open_app")

    def test_open_app_empty_name(self):
        res = open_app("")
        self.assertEqual(res["status"], "error")
        self.assertIn("empty", res["error"])

    @patch("subprocess.Popen", side_effect=Exception("Failed to launch"))
    @patch("os.startfile", side_effect=Exception("Failed to launch"), create=True)
    def test_open_app_exception(self, mock_startfile, mock_popen):
        res = open_app("NonExistentApp")
        self.assertEqual(res["status"], "error")
        self.assertIn("failed", res["error"].lower())

    @patch("control.desktop.pyautogui")
    def test_type_text_success(self, mock_pyautogui):
        res = type_text("Hello World", interval=0.1)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "type_text")
        self.assertEqual(res["data"]["length"], 11)
        mock_pyautogui.write.assert_called_once_with("Hello World", interval=0.1)

    def test_type_text_none(self):
        res = type_text(None)  # type: ignore
        self.assertEqual(res["status"], "error")
        self.assertIn("None", res["error"])

    @patch("control.desktop.pyautogui", None)
    def test_type_text_no_pyautogui(self):
        res = type_text("test")
        self.assertEqual(res["status"], "error")
        self.assertIn("not installed", res["error"])

    @patch("control.desktop.pyautogui")
    def test_click_with_coords(self, mock_pyautogui):
        res = click(x=100, y=200, button="right", clicks=2)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "click")
        self.assertEqual(
            res["data"], {"x": 100, "y": 200, "button": "right", "clicks": 2}
        )
        mock_pyautogui.click.assert_called_once_with(
            x=100, y=200, button="right", clicks=2
        )

    @patch("control.desktop.pyautogui")
    def test_click_without_coords(self, mock_pyautogui):
        res = click()
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "click")
        mock_pyautogui.click.assert_called_once_with(button="left", clicks=1)

    def test_click_invalid_button(self):
        res = click(button="invalid_button")
        self.assertEqual(res["status"], "error")
        self.assertIn("Invalid mouse button", res["error"])

    @patch("control.desktop.pyautogui")
    def test_screenshot_in_memory(self, mock_pyautogui):
        mock_img = Image.new("RGB", (100, 100), color="red")
        mock_pyautogui.screenshot.return_value = mock_img

        res = screenshot()
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "screenshot")
        self.assertIn("base64", res["data"])
        self.assertEqual(res["data"]["size"], (100, 100))

    @patch("control.desktop.pyautogui")
    def test_screenshot_save_to_file(self, mock_pyautogui):
        mock_img = Image.new("RGB", (100, 100), color="blue")
        mock_pyautogui.screenshot.return_value = mock_img

        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "test.png")
            res = screenshot(output_path=out_file)
            self.assertEqual(res["status"], "ok")
            self.assertEqual(res["data"]["output_path"], out_file)

    def test_delete_path_file_success(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_name = tmp.name

        self.assertTrue(os.path.exists(tmp_name))
        res = delete_path(tmp_name)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "delete_path")
        self.assertEqual(res["data"]["type"], "file")
        self.assertFalse(os.path.exists(tmp_name))

    def test_delete_path_dir_success(self):
        tmp_dir = tempfile.mkdtemp()
        dummy_file = os.path.join(tmp_dir, "dummy.txt")
        with open(dummy_file, "w") as f:
            f.write("test")

        self.assertTrue(os.path.exists(tmp_dir))
        res = delete_path(tmp_dir)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "delete_path")
        self.assertEqual(res["data"]["type"], "directory")
        self.assertFalse(os.path.exists(tmp_dir))

    def test_delete_path_nonexistent(self):
        res = delete_path("/path/that/does/not/exist/at/all/12345")
        self.assertEqual(res["status"], "error")
        self.assertIn("does not exist", res["error"])

    def test_delete_path_empty(self):
        res = delete_path("")
        self.assertEqual(res["status"], "error")
        self.assertIn("empty", res["error"])


if __name__ == "__main__":
    unittest.main()
