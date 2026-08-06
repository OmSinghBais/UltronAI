"""
ATLAS — Main System Entrypoint
Long-running Python process for the ATLAS voice-driven personal assistant.
Initializes Core Orchestrator, Dual Router (Llama 3.2), Phone Control Bridge, Desktop/Browser automation, and Safety Confirmation Gate.
"""

import asyncio
import os
import sys

from config.settings import settings
from core.audit_log import AuditLogger
from core.orchestrator import Orchestrator
from core.router import Router
from phone.bridge_server import PhoneController


BANNER = r"""
   ___  _____ _      ___   _____ 
  / _ \|_   _| |    / _ \ /  ___|
 / /_\ \ | | | |   / /_\ \\ `--. 
 |  _  | | | | |___|  _  | `--. \
 |_| |_| \_/ \_____|_| |_/\____/ 

  ATLAS — Voice & AI Assistant (Ollama Llama 3.2 Powered)
  Status: Online · Listening
------------------------------------------------------------
"""


async def main():
    print(BANNER)
    print(f"[*] Configuration Loaded:")
    print(f"    - LLM Engine: Ollama ({settings.ollama_model} @ {settings.ollama_host})")
    print(f"    - Phone Bridge: {settings.phone_ip}:{settings.phone_port}")
    print(f"    - Audit Trail: {settings.audit_log_path}")
    print()

    audit_logger = AuditLogger(settings.audit_log_path)
    router = Router()

    print("[*] Connecting to Phone Bridge (with ADB auto-tunneling)...")
    phone_controller = PhoneController()
    try:
        await phone_controller.connect()
        print("    [+] Connected to Phone Bridge!")
    except Exception as e:
        print(f"    [-] Phone Bridge not connected ({e}). Will auto-reconnect when phone commands are sent.")

    orchestrator = Orchestrator(
        router=router,
        audit_logger=audit_logger,
        phone=phone_controller
    )

    print("[+] ATLAS System Ready. Enter a command (or 'exit' to quit):\n")

    try:
        while True:
            try:
                user_input = await asyncio.to_thread(input, "Atlas > ")
                user_input = user_input.strip()
                if not user_input:
                    continue
                if user_input.lower() in ("exit", "quit"):
                    break

                res = await orchestrator.process_command(user_input)
                print(f"Response: {res.get('result', '')}\n")
            except (KeyboardInterrupt, EOFError):
                break
    finally:
        print("\n[*] Shutting down ATLAS...")
        await phone_controller.disconnect()
        print("[+] Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
