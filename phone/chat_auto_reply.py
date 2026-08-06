"""
ATLAS — Phone Chat Auto-Reply Module
Listens for incoming phone chat notifications (SMS, WhatsApp, etc.),
generates personalized auto-replies matching the user's exact writing style via UserStyleMimicEngine,
and sends them automatically or upon prompt over the PhoneController WebSocket.
"""

from typing import Any, Dict, Optional
from core.style_engine import UserStyleMimicEngine
from phone.bridge_server import PhoneController


class ChatAutoReplier:
    """
    Receives chat notifications and dispatches style-matched replies over PhoneController.
    """
    def __init__(self, style_engine: Optional[UserStyleMimicEngine] = None, phone_controller: Optional[PhoneController] = None):
        self.style_engine = style_engine or UserStyleMimicEngine()
        self.phone = phone_controller or PhoneController()
        self.auto_reply_enabled = False

    def enable_auto_reply(self, enabled: bool = True):
        """Enables or disables automatic chat auto-replies."""
        self.auto_reply_enabled = enabled
        status_str = "ENABLED" if enabled else "DISABLED"
        print(f"[CHAT AUTO-REPLY]: {status_str}")

    async def reply_to_chat_notification(self, notification_payload: Dict[str, Any], force_send: bool = False) -> Dict[str, Any]:
        """
        Generates a personalized user-style auto-reply to an incoming notification payload.
        If force_send is True or auto_reply_enabled is True, types and sends the reply on phone.
        """
        sender = notification_payload.get("sender", "Someone")
        incoming_body = notification_payload.get("body", "")
        app = notification_payload.get("app", "Chat")

        if not incoming_body:
            return {"status": "error", "error": "Notification body is empty"}

        context = f"Message received from {sender} via {app}"
        generated_reply, route = await self.style_engine.generate_user_style_reply(incoming_body, context=context)

        res = {
            "status": "ok",
            "app": app,
            "sender": sender,
            "incoming_body": incoming_body,
            "generated_reply": generated_reply,
            "route": route,
            "sent": False
        }

        if force_send or self.auto_reply_enabled:
            send_res = await self.phone.type_text(generated_reply)
            res["sent"] = (send_res.get("status") == "ok")
            res["send_result"] = send_res

        return res
