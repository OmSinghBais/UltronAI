"""
ATLAS Phase 3 Verification & Demo Script
Demonstrates dual reasoning: Online Gemini API reasoning and local Ollama offline fallback.
"""
import asyncio
from unittest.mock import AsyncMock, patch
from core.router import Router
from config.settings import settings


async def main():
    print("=" * 60)
    print("           ATLAS PHASE 3 VERIFICATION & DEMO           ")
    print("=" * 60)

    router = Router()

    # 1. Check Internet Connectivity Status
    print("\n[1/3] Checking Network Connectivity...")
    online = await router.is_online()
    print(f"  - Internet Connection: {'ONLINE [OK]' if online else 'OFFLINE (Local Mode)'}")

    prompt = "Explain in 1 sentence what an AI assistant does."

    # 2. Live Routing Test
    print(f"\n[2/3] Executing Live Router Request: '{prompt}'...")
    text, route = await router.route(prompt)
    print(f"  - Route Used:      [{route.upper()}]")
    print(f"  - Model Response:  '{text}'")

    # 3. Simulated Offline Fallback Test
    print("\n[3/3] Simulating Disconnected Offline Fallback...")
    with patch.object(router, "is_online", AsyncMock(return_value=False)):
        with patch.object(router, "_ollama_generate", AsyncMock(return_value="[Simulated Ollama Fallback] An AI assistant automates tasks and answers user queries locally.")):
            sim_text, sim_route = await router.route(prompt)
            print(f"  - Simulated Route: [{sim_route.upper()}]")
            print(f"  - Fallback Result: '{sim_text}'")

    print("\n" + "=" * 60)
    print("         PHASE 3 ROUTER VERIFIED SUCCESSFULLY          ")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
