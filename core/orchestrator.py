import asyncio
import time
from typing import Optional, Callable, Dict, Any, Union
from pathlib import Path

from core.wake_word import WakeWordDetector
from core.stt import SpeechToText
from core.tts import TextToSpeech
from core.router import Router
from core.audit_log import AuditLogger
from core.intents import Intent, IntentType

from control.desktop import open_app, type_text, delete_path, screenshot, click
from control.browser import navigate, search, fill_form, read_page
from phone.bridge_server import PhoneController


class Orchestrator:
    """
    ATLAS Core Orchestrator.
    Ties together wake word detection, STT, intent classification, AI routing,
    confirmation safety gating, control action dispatching, TTS audio feedback, and audit logging.
    """
    def __init__(
        self,
        wake_word: Optional[WakeWordDetector] = None,
        stt: Optional[SpeechToText] = None,
        tts: Optional[TextToSpeech] = None,
        router: Optional[Router] = None,
        audit: Optional[AuditLogger] = None,
        phone: Optional[PhoneController] = None
    ):
        self.wake_word = wake_word or WakeWordDetector()
        self.stt = stt or SpeechToText()
        self.tts = tts or TextToSpeech()
        self.router = router or Router()
        self.audit = audit or AuditLogger("./storage/audit.jsonl")
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
                self.audit.log(
                    intent=intent,
                    route_used="confirmation_gate",
                    result="cancelled",
                    blocked=True,
                    latency_ms=(time.time() - start_time) * 1000
                )
                return {"status": "cancelled", "reason": "not confirmed"}

        # Check for Screen Seeing / Vision commands
        text_lower = text.lower()
        if any(v in text_lower for v in ["see screen", "what is on my screen", "what's on screen", "look at screen", "analyze screen", "look at laptop", "read desktop"]):
            try:
                from PIL import ImageGrab
                img = ImageGrab.grab()
                vision_prompt = f"The user asked: '{text}'. Analyze the active laptop screen screenshot and explain clearly what is visible, active apps, open documents, or requested information."
                resp_text, route_used = await self.router.route_vision(vision_prompt, img)
                self.tts.speak(resp_text)
                self.audit.log(intent=intent, route_used=route_used, result=resp_text, blocked=False, latency_ms=(time.time() - start_time) * 1000)
                return {"status": "ok", "action": "see_screen", "response": resp_text, "route": route_used}
            except Exception as e:
                err_msg = f"Screen capture vision analysis error: {e}"
                self.tts.speak(err_msg)
                return {"status": "error", "error": err_msg}

        # Check for Search & Summarize commands ("search python news", "open chrome and search...")
        if "search" in text_lower or "browse" in text_lower or "google" in text_lower:
            # First open browser if requested
            if "chrome" in text_lower or "open" in text_lower:
                open_app("chrome.exe")

            # Extract search query
            query = text_lower
            for prefix in ["open chrome and search", "search for", "search", "browse for", "google", "find"]:
                if prefix in query:
                    query = query.split(prefix)[-1].strip()

            if not query:
                query = text

            search_res = search(query, headless=True)
            if search_res.get("status") == "ok":
                page_data = read_page(search_res["data"]["url"], headless=True)
                content = page_data.get("data", {}).get("content", "")
                if content:
                    summary_prompt = f"User asked: '{text}'. Summarize the following search result page in 3 clear sentences for voice read-out:\n\n{content[:3000]}"
                    summary_text, route_used = await self.router.route(summary_prompt)
                    resp_str = f"I searched for '{query}'. Here is what I found: {summary_text}"
                else:
                    resp_str = f"I opened Chrome and searched for '{query}'."
            else:
                resp_str = f"I opened Chrome and searched for '{query}'."

            self.tts.speak(resp_str)
            self.audit.log(intent=intent, route_used="browser_automation", result=resp_str, blocked=False, latency_ms=(time.time() - start_time) * 1000)
            return {"status": "ok", "action": "search", "response": resp_str, "route": "browser_agent"}

        if intent.type == IntentType.QUERY:
            response, route = await self.router.route(text)
            self.tts.speak(response)
            self.audit.log(
                intent=intent,
                route_used=route,
                result=response,
                blocked=False,
                latency_ms=(time.time() - start_time) * 1000
            )
            return {"status": "ok", "route": route, "response": response}

        elif intent.type == IntentType.DESKTOP_ACTION:
            result = self._dispatch_desktop_action(text)
            app_name = result.get("data", {}).get("app_name", text)
            spoken_msg = f"Opened {app_name} on your laptop." if result.get("status") == "ok" else f"Could not open {app_name}."
            result["response"] = spoken_msg
            self.tts.speak(spoken_msg)
            self.audit.log(
                intent=intent,
                route_used="desktop_control",
                result=str(result),
                blocked=False,
                latency_ms=(time.time() - start_time) * 1000
            )
            return result

        elif intent.type == IntentType.SENSITIVE_ACTION:
            result = self._dispatch_sensitive_action(text)
            spoken_msg = f"Executed sensitive action: {text}"
            result["response"] = spoken_msg
            self.tts.speak(spoken_msg)
            self.audit.log(
                intent=intent,
                route_used="sensitive_control",
                result=str(result),
                blocked=False,
                latency_ms=(time.time() - start_time) * 1000
            )
            return result

        elif intent.type == IntentType.PHONE_ACTION:
            result = await self._dispatch_phone_action(text)
            spoken_msg = result.get("response", "Executed action on your phone.")
            result["response"] = spoken_msg
            self.tts.speak(spoken_msg)
            self.audit.log(
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
            self.audit.log(
                intent=intent,
                route_used=route,
                result=response,
                blocked=False,
                latency_ms=(time.time() - start_time) * 1000
            )
            return {"status": "ok", "route": route, "response": response}

    def _dispatch_desktop_action(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        if "open" in text_lower or "launch" in text_lower:
            # Extract target application
            target = text_lower
            for verb in ["open", "launch"]:
                if verb in target:
                    target = target.split(verb)[-1]
            return open_app(target.strip())
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
                res = await self.phone.tap(x=500, y=1000)
                res["response"] = "Tapped phone screen."
                return res
            elif "type on phone" in text_lower:
                content = text_lower.split("type on phone")[-1].strip()
                res = await self.phone.type_text(content)
                res["response"] = f"Typed '{content}' on phone."
                return res
            elif "open app on phone" in text_lower:
                package = text_lower.split("open app on phone")[-1].strip()
                res = await self.phone.open_app(package)
                res["response"] = f"Opened app {package} on phone."
                return res
            elif "read screen" in text_lower or "see phone screen" in text_lower:
                res = await self.phone.read_screen()
                nodes = res.get("elements", [])
                node_summary = f"Phone screen contains {len(nodes)} interactive elements."
                res["response"] = node_summary
                return res
            else:
                return {"status": "error", "error": f"Unknown phone action: {text}"}
        except Exception as e:
            return {"status": "error", "error": f"Phone action failed: {str(e)}"}
