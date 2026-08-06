import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from core.agent_planner import GoalPlanner, ProactiveHeartbeat


class TestAgentPlanner(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_router = MagicMock()
        self.planner = GoalPlanner(router=self.mock_router)

    async def test_decompose_goal_success(self):
        self.mock_router.route = AsyncMock(
            return_value=("1. Open Chrome\n2. Search Python news\n3. Summarize page", "ollama")
        )
        steps = await self.planner.decompose_goal("Research python news")
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0], "Open Chrome")
        self.assertEqual(steps[1], "Search Python news")
        self.assertEqual(steps[2], "Summarize page")

    async def test_proactive_heartbeat_loop(self):
        heartbeat = ProactiveHeartbeat(interval_seconds=0.05)
        mock_callback = AsyncMock()

        heartbeat.start(check_callback=mock_callback)
        await asyncio.sleep(0.12)
        heartbeat.stop()

        self.assertGreaterEqual(heartbeat.checks_run, 2)
        self.assertGreaterEqual(mock_callback.call_count, 2)


if __name__ == "__main__":
    unittest.main()
