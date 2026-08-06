"""
ATLAS — Deep Learning User Style Mimicry Engine
Extracts writing habits (capitalization, punctuation, brevity, slang, emojis) from past user interactions
and conditions local Llama 3.2 to generate chat auto-replies in the exact personal style of the user.
"""

import json
from pathlib import Path
from typing import List, Optional, Tuple
from core.history_db import HistoryDB
from core.router import Router


class UserStyleMimicEngine:
    """
    DL-prompt-engineered style mimicry engine for generating personalized auto-replies.
    """
    def __init__(self, history_db: Optional[HistoryDB] = None, router: Optional[Router] = None, samples_file: str = "./storage/user_style.json"):
        self.history_db = history_db or HistoryDB()
        self.router = router or Router()
        self.samples_file = Path(samples_file)
        self.samples_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.samples_file.exists():
            self.samples_file.write_text("[]", encoding="utf-8")

    def add_style_sample(self, sample_text: str) -> None:
        """Saves a custom text sample written by the user."""
        if not sample_text or not sample_text.strip():
            return
        samples = self.get_custom_samples()
        if sample_text.strip() not in samples:
            samples.append(sample_text.strip())
            self.samples_file.write_text(json.dumps(samples, indent=2), encoding="utf-8")

    def get_custom_samples(self) -> List[str]:
        """Retrieves custom user writing samples."""
        try:
            return json.loads(self.samples_file.read_text(encoding="utf-8"))
        except Exception:
            return []

    async def collect_training_samples(self, limit: int = 20) -> List[str]:
        """Combines custom style samples and past raw_text commands from HistoryDB."""
        samples = self.get_custom_samples()
        try:
            records = await self.history_db.get_recent_history(limit=limit * 2)
            for r in records:
                txt = r.get("raw_text", "").strip()
                if txt and len(txt) > 2 and txt not in samples:
                    samples.append(txt)
                if len(samples) >= limit:
                    break
        except Exception:
            pass
        return samples[:limit]

    async def generate_user_style_reply(self, incoming_msg: str, context: str = "") -> Tuple[str, str]:
        """
        Generates an auto-reply to incoming_msg matching the user's exact writing style.
        Returns tuple of (reply_text, route_used).
        """
        samples = await self.collect_training_samples(limit=15)
        samples_formatted = "\n".join([f'- "{s}"' for s in samples]) if samples else '- "yep sounds good"\n- "sure np"\n- "cool let me know"'

        prompt = (
            f"SYSTEM ROLE: You are acting as the user. You must generate a direct chat reply to an incoming message. "
            f"Strictly match the user's exact capitalization (e.g. lowercase vs uppercase), punctuation, brevity, slang, and tone.\n\n"
            f"FEW-SHOT EXAMPLES OF THE USER'S ACTUAL TYPING STYLE:\n{samples_formatted}\n\n"
            f"INCOMING MESSAGE TO REPLY TO: '{incoming_msg}'\n"
            f"{'CONTEXT: ' + context if context else ''}\n\n"
            f"OUTPUT RULE: Output ONLY the exact chat message text to send. No quotes, no intro, no explanations."
        )

        reply_text, route_used = await self.router.route(prompt)
        # Clean response
        clean_reply = reply_text.strip().strip('"\'')
        return clean_reply, route_used
