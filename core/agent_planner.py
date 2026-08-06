"""
ATLAS — Proactive Background Agents & Goal Planner Engine
Decomposes complex multi-step user prompts into Directed Acyclic Graphs (DAGs) of executable sub-intents,
and handles periodic background status heartbeat tasks.
"""

import asyncio
from typing import Any, Dict, List, Optional
from core.router import Router


class GoalPlanner:
    """
    Multi-step goal decomposition engine for complex requests.
    """
    def __init__(self, router: Optional[Router] = None):
        self.router = router or Router()

    async def decompose_goal(self, main_goal: str) -> List[str]:
        """
        Decomposes a multi-step request into a sequence of atomic command strings.
        """
        prompt = (
            f"Decompose the following user goal into a simple sequential list of atomic sub-commands: '{main_goal}'. "
            f"Return ONLY sub-commands separated by newlines, with no bullet points, numbering, or introductory text."
        )
        resp, _ = await self.router.route(prompt)
        lines = [line.strip("- *0123456789. ").strip() for line in resp.split("\n") if line.strip()]
        return lines if lines else [main_goal]


class ProactiveHeartbeat:
    """
    Periodic background heartbeat agent for proactive system & task monitoring.
    """
    def __init__(self, interval_seconds: float = 60.0):
        self.interval_seconds = interval_seconds
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.checks_run = 0

    async def _heartbeat_loop(self, check_callback: Optional[Any] = None):
        while self.running:
            self.checks_run += 1
            if check_callback:
                try:
                    if asyncio.iscoroutinefunction(check_callback):
                        await check_callback(self.checks_run)
                    else:
                        check_callback(self.checks_run)
                except Exception:
                    pass
            await asyncio.sleep(self.interval_seconds)

    def start(self, check_callback: Optional[Any] = None):
        """Starts the background heartbeat loop."""
        if not self.running:
            self.running = True
            self._task = asyncio.create_task(self._heartbeat_loop(check_callback))

    def stop(self):
        """Stops the background heartbeat loop."""
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()
