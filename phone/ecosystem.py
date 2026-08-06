"""
ATLAS — Phone Ecosystem & Handoff Module
Provides cross-device clipboard synchronization and incoming notification listener/parser.
"""

import json
from typing import Any, Dict, Optional
from phone.bridge_server import PhoneController


class PhoneEcosystemManager:
    """
    Manages high-level phone ecosystem integrations: clipboard handoff & notification processing.
    """
    def __init__(self, phone_controller: Optional[PhoneController] = None):
        self.phone = phone_controller or PhoneController()

    async def sync_clipboard_to_phone(self, text: str) -> Dict[str, Any]:
        """
        Sends local text to the phone's currently focused input field via WebSocket.
        """
        if not text:
            return {"status": "error", "error": "Clipboard text cannot be empty"}
        
        res = await self.phone.type_text(text)
        if res.get("status") == "ok":
            res["response"] = f"Synced text ({len(text)} chars) to phone clipboard."
        return res

    def parse_incoming_notification(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses an incoming notification message payload received from the phone companion app.
        Payload format: {"action": "notification", "app": "WhatsApp", "sender": "John", "body": "Hey there!"}
        """
        app = payload.get("app", "Phone")
        sender = payload.get("sender", "Unknown")
        body = payload.get("body", "")

        summary_text = f"Notification from {sender} on {app}: {body}"
        return {
            "status": "ok",
            "app": app,
            "sender": sender,
            "body": body,
            "voice_summary": summary_text
        }
