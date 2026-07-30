"""
Unit tests for control/confirmation.py and control/face_gate.py
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from control.confirmation import requires_confirmation
from control.face_gate import enroll_face, generate_face_key, verify_face


# Dummy functions decorated with @requires_confirmation
@requires_confirmation(category="delete_file")
def mock_delete_file(file_path: str):
    return {"status": "ok", "action": "delete_file", "data": {"path": file_path}}


@requires_confirmation(category="payment", prompt="Confirm payment of $50?")
def mock_make_payment(amount: float):
    return {"status": "ok", "action": "payment", "data": {"amount": amount}}


class TestConfirmationDecorator(unittest.TestCase):

    def test_confirmation_approved(self):
        def mock_confirm(prompt: str) -> bool:
            return True

        res = mock_delete_file("/tmp/test.txt", confirm_fn=mock_confirm)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["data"]["path"], "/tmp/test.txt")

    def test_confirmation_denied(self):
        def mock_confirm(prompt: str) -> bool:
            return False

        res = mock_delete_file("/tmp/test.txt", confirm_fn=mock_confirm)
        self.assertEqual(res["status"], "cancelled")
        self.assertEqual(res["reason"], "not confirmed")

    def test_confirmation_missing_callback(self):
        res = mock_delete_file("/tmp/test.txt")
        self.assertEqual(res["status"], "cancelled")
        self.assertIn("No confirmation callback provided", res["reason"])

    def test_confirmation_callback_raises_exception(self):
        def mock_confirm(prompt: str) -> bool:
            raise RuntimeError("UI error")

        res = mock_delete_file("/tmp/test.txt", confirm_fn=mock_confirm)
        self.assertEqual(res["status"], "error")
        self.assertIn("callback failed", res["error"])

    def test_custom_prompt_passed_to_callback(self):
        received_prompt = None

        def mock_confirm(prompt: str) -> bool:
            nonlocal received_prompt
            received_prompt = prompt
            return True

        res = mock_make_payment(50.0, confirm_fn=mock_confirm)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(received_prompt, "Confirm payment of $50?")


class TestFaceGate(unittest.TestCase):

    def setUp(self):
        self.key = generate_face_key()
        self.embedding1 = [0.1, 0.2, 0.3, 0.4, 0.5]
        self.embedding1_similar = [0.11, 0.21, 0.31, 0.41, 0.51]
        self.embedding2_different = [0.9, 0.8, 0.7, 0.6, 0.5]

    def test_enroll_and_verify_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store_file = os.path.join(tmpdir, "face.enc")

            enroll_res = enroll_face(
                self.embedding1, self.key, storage_path=store_file
            )
            self.assertEqual(enroll_res["status"], "ok")
            self.assertEqual(enroll_res["action"], "enroll_face")
            self.assertTrue(os.path.exists(store_file))

            # Verify identical embedding
            verify_res = verify_face(
                self.embedding1, self.key, storage_path=store_file
            )
            self.assertEqual(verify_res["status"], "ok")
            self.assertTrue(verify_res["data"]["match"])
            self.assertEqual(verify_res["data"]["distance"], 0.0)

            # Verify similar embedding
            verify_similar = verify_face(
                self.embedding1_similar, self.key, storage_path=store_file
            )
            self.assertEqual(verify_similar["status"], "ok")
            self.assertTrue(verify_similar["data"]["match"])

    def test_verify_mismatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store_file = os.path.join(tmpdir, "face.enc")
            enroll_face(self.embedding1, self.key, storage_path=store_file)

            verify_res = verify_face(
                self.embedding2_different, self.key, storage_path=store_file
            )
            self.assertEqual(verify_res["status"], "ok")
            self.assertFalse(verify_res["data"]["match"])
            self.assertGreater(verify_res["data"]["distance"], 0.6)

    def test_verify_invalid_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store_file = os.path.join(tmpdir, "face.enc")
            enroll_face(self.embedding1, self.key, storage_path=store_file)

            wrong_key = generate_face_key()
            verify_res = verify_face(
                self.embedding1, wrong_key, storage_path=store_file
            )
            self.assertEqual(verify_res["status"], "error")
            self.assertIn("failed", verify_res["error"])

    def test_verify_file_not_found(self):
        verify_res = verify_face(
            self.embedding1,
            self.key,
            storage_path="/path/does/not/exist/face.enc",
        )
        self.assertEqual(verify_res["status"], "error")
        self.assertIn("not found", verify_res["error"])

    @patch("control.face_gate.Fernet", None)
    def test_missing_cryptography_module(self):
        res = enroll_face(self.embedding1, b"dummy_key")
        self.assertEqual(res["status"], "error")
        self.assertIn("not installed", res["error"])


if __name__ == "__main__":
    unittest.main()
