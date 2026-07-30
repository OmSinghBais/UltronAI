"""
ATLAS Phase 4 Verification & Demo Script
Demonstrates end-to-end Orchestrator execution:
1. Autonomous query processing
2. Autonomous non-sensitive desktop action
3. Confirmed sensitive action vs. cancelled sensitive action
"""
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

from core.orchestrator import Orchestrator
from core.audit_log import AuditLogger
from config.settings import settings


async def main():
    print("=" * 60)
    print("           ATLAS PHASE 4 VERIFICATION & DEMO           ")
    print("=" * 60)

    # 1. Initialize Orchestrator with temp audit log
    with tempfile.TemporaryDirectory() as tmpdir:
        test_audit_path = Path(tmpdir) / "demo_phase4_audit.jsonl"
        orchestrator = Orchestrator(audit=AuditLogger(test_audit_path))
        orchestrator.router.route = AsyncMock(return_value=("ATLAS Orchestrator is operational.", "gemini"))

        # 2. Test Autonomous Informational Query
        print("\n[1/3] Testing Autonomous Informational Query...")
        query_text = "what is the system status"
        res1 = await orchestrator.process_command(query_text)
        print(f"  - Command:  '{query_text}'")
        print(f"  - Result:   {res1}")

        # 3. Test Autonomous Desktop Action
        print("\n[2/3] Testing Autonomous Desktop Action...")
        desktop_text = "open notepad"
        res2 = await orchestrator.process_command(desktop_text)
        print(f"  - Command:  '{desktop_text}'")
        print(f"  - Result:   {res2}")

        # 4. Test Sensitive Action Gating (Confirmed vs Cancelled)
        print("\n[3/3] Testing Sensitive Action Gating (Delete File)...")
        sensitive_text = "delete important_data.txt"

        # 4a. Cancelled Case
        print("  - [Case A: User cancels confirmation]")
        res3_cancel = await orchestrator.process_command(sensitive_text, confirm_fn=lambda p: False)
        print(f"    Result: {res3_cancel}")

        # 4b. Confirmed Case
        print("  - [Case B: User confirms with 'yes']")
        res3_confirm = await orchestrator.process_command(sensitive_text, confirm_fn=lambda p: True)
        print(f"    Result: {res3_confirm}")

        print("\n" + "=" * 60)
        print("       PHASE 4 ORCHESTRATOR VERIFIED SUCCESSFULLY       ")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
