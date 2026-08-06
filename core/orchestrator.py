import asyncio
import time
from typing import Optional, Callable, Dict, Any, Union
from pathlib import Path

from core.wake_word import WakeWordDetector
from core.stt import SpeechToText
from core.tts import TextToSpeech
from core.router import Router
from core.audit_log import AuditLogger
from core.history_db import HistoryDB
from core.intents import Intent, IntentType

from control.desktop import open_app, type_text, delete_path, screenshot, click
from control.browser import navigate, search, fill_form, read_page
from phone.bridge_server import PhoneController


class Orchestrator:
    """
    ATLAS Core Orchestrator.
    Ties together wake word detection, STT, intent classification, AI routing,
    confirmation safety gating, control action dispatching, TTS audio feedback, audit logging, and HistoryDB.
    """
    def __init__(
        self,
        wake_word: Optional[WakeWordDetector] = None,
        stt: Optional[SpeechToText] = None,
        tts: Optional[TextToSpeech] = None,
        router: Optional[Router] = None,
        audit: Optional[AuditLogger] = None,
        phone: Optional[PhoneController] = None,
        history_db: Optional[HistoryDB] = None,
    ):
        self.wake_word = wake_word or WakeWordDetector()
        self.stt = stt or SpeechToText()
        self.tts = tts or TextToSpeech()
        self.router = router or Router()
        self.audit = audit or AuditLogger("./storage/audit.jsonl")
        self.history_db = history_db or HistoryDB("./storage/history.db")
        self.phone: Optional[PhoneController] = phone  # Injected; None until connect() called

    def classify_intent(self, text: str, lang: str = "en") -> Intent:
        """
        Classifies input text into Intent schema with confirmation flags based on security policy.
        Sensitive keywords requiring confirmation:
        - login, logout
        - money, buy, purchase, pay, transfer
        - delete, erase, remove file
        - send message, send email, make a call
        - password, otp, credential
        """
        text_lower = text.lower()
        sensitive_keywords = [
            "login", "log in", "logout", "log out",
            "buy", "purchase", "pay", "transfer", "money",
            "delete", "erase", "remove file",
            "send email", "send message", "make a call", "send msg",
            "password", "otp", "credential"
        ]
        is_sensitive = any(k in text_lower for k in sensitive_keywords)

        if is_sensitive:
            intent_type = IntentType.SENSITIVE_ACTION
        elif any(k in text_lower for k in ["tap phone", "type on phone", "open app on phone", "read screen", "phone tap"]):
            intent_type = IntentType.PHONE_ACTION
        elif any(k in text_lower for k in ["open", "type", "click", "launch", "screenshot"]):
            intent_type = IntentType.DESKTOP_ACTION
        elif any(k in text_lower for k in ["browse", "search", "navigate", "go to"]):
            intent_type = IntentType.BROWSER_ACTION
        else:
            intent_type = IntentType.QUERY

        return Intent(
            type=intent_type,
            raw_text=text,
            language=lang,
            parameters={},
            requires_confirmation=is_sensitive
        )

    async def confirm(self, prompt_text: str, confirm_fn: Optional[Callable[[str], Any]] = None) -> bool:
        """
        Confirmation gate helper for sensitive actions.
        Prompts user via TTS, then evaluates confirmation via callback or STT.
        """
        self.tts.speak(f"{prompt_text} Please confirm with yes.")
        if confirm_fn is not None:
            res = confirm_fn(prompt_text)
            if asyncio.iscoroutine(res):
                res = await res
            return bool(res)
        return False

    async def _log_and_store(
        self,
        intent: Intent,
        route_used: str,
        result: str,
        blocked: bool,
        latency_ms: float
    ):
        self.audit.log(
            intent=intent,
            route_used=route_used,
            result=result,
            blocked=blocked,
            latency_ms=latency_ms
        )
        try:
            await self.history_db.add_record(
                raw_text=intent.raw_text,
                intent_type=intent.type.value,
                route_used=route_used,
                response=result,
                blocked=blocked,
                latency_ms=latency_ms
            )
        except Exception:
            pass  # Non-blocking history record creation

    async def confirm(self, prompt: str, confirm_fn: Optional[Callable] = None) -> bool:
        """
        Confirmation gate helper. Executes confirm_fn callback or defaults to True if None.
        """
        if confirm_fn is None:
            return True
        try:
            if asyncio.iscoroutinefunction(confirm_fn):
                return await confirm_fn(prompt)
            return bool(confirm_fn(prompt))
        except Exception:
            return False

    async def process_command(self, text: str, lang: str = "en", confirm_fn: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Processes a single command transcript end-to-end.
        """
        start_time = time.time()
        intent = self.classify_intent(text, lang)

        if intent.requires_confirmation:
            confirmed = await self.confirm(f"This will execute: {text}.", confirm_fn=confirm_fn)
            if not confirmed:
                self.tts.speak("Action cancelled.")
                await self._log_and_store(
                    intent=intent,
                    route_used="confirmation_gate",
                    result="cancelled",
                    blocked=True,
                    latency_ms=(time.time() - start_time) * 1000
                )
                return {"status": "cancelled", "reason": "not confirmed"}

        if intent.type == IntentType.QUERY:
            response, route = await self.router.route(text)
            self.tts.speak(response)
            await self._log_and_store(
                intent=intent,
                route_used=route,
                result=response,
                blocked=False,
                latency_ms=(time.time() - start_time) * 1000
            )
            return {"status": "ok", "route": route, "response": response}

        elif intent.type == IntentType.DESKTOP_ACTION:
            result = self._dispatch_desktop_action(text)
            self.tts.speak(f"Executed: {result.get('action', 'desktop action')}")
            await self._log_and_store(
                intent=intent,
                route_used="desktop_control",
                result=str(result),
                blocked=False,
                latency_ms=(time.time() - start_time) * 1000
            )
            return result

        elif intent.type == IntentType.SENSITIVE_ACTION:
            result = self._dispatch_sensitive_action(text)
            self.tts.speak(f"Executed sensitive action: {result.get('action', text)}")
            await self._log_and_store(
                intent=intent,
                route_used="sensitive_control",
                result=str(result),
                blocked=False,
                latency_ms=(time.time() - start_time) * 1000
            )
            return result

        elif intent.type == IntentType.PHONE_ACTION:
            result = await self._dispatch_phone_action(text)
            self.tts.speak(f"Phone action executed.")
            await self._log_and_store(
                intent=intent,
                route_used="phone_control",
                result=str(result),
                blocked=False,
                latency_ms=(time.time() - start_time) * 1000
            )
            return result

        else:
            response, route = await self.router.route(text)
            self.tts.speak(response)
            await self._log_and_store(
                intent=intent,
                route_used=route,
                result=response,
                blocked=False,
                latency_ms=(time.time() - start_time) * 1000
            )
            return {"status": "ok", "route": route, "response": response}

    def _dispatch_desktop_action(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        if "open" in text_lower:
            app_name = text_lower.split("open")[-1].strip()
            return open_app(app_name)
        elif "type" in text_lower:
            content = text_lower.split("type")[-1].strip()
            return type_text(content)
        elif "screenshot" in text_lower:
            return screenshot()
        return {"status": "ok", "action": text}

    def _dispatch_sensitive_action(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        if "delete" in text_lower:
            target_path = text_lower.split("delete")[-1].strip()
            return delete_path(target_path)
        return {"status": "ok", "action": f"executed sensitive: {text}"}

    async def _dispatch_phone_action(self, text: str) -> Dict[str, Any]:
        """
        Dispatches PHONE_ACTION intents to the PhoneController WebSocket bridge.
        Requires self.phone to be an already-connected PhoneController instance.
        """
        if self.phone is None:
            return {
                "status": "error",
                "error": "PhoneController not connected. Call orchestrator.phone = PhoneController() and await phone.connect() first."
            }
        text_lower = text.lower()
        try:
            if "tap phone" in text_lower or "phone tap" in text_lower:
                return await self.phone.tap(x=500, y=1000)
            elif "type on phone" in text_lower:
                content = text_lower.split("type on phone")[-1].strip()
                return await self.phone.type_text(content)
            elif "open app on phone" in text_lower:
                package = text_lower.split("open app on phone")[-1].strip()
                return await self.phone.open_app(package)
            elif "read screen" in text_lower:
                return await self.phone.read_screen()
            else:
                return {"status": "error", "error": f"Unknown phone action: {text}"}
        except Exception as e:
            return {"status": "error", "error": f"Phone action failed: {str(e)}"}
