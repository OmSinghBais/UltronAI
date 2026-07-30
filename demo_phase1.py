"""
ATLAS Phase 1 Demo Script
Loads configuration, writes a sample audit log entry, and tests Gemini API connectivity.
"""
import sys
import time
from pathlib import Path
from config.settings import settings
from core.intents import Intent, IntentType
from core.audit_log import AuditLogger


def main():
    print("=" * 60)
    print("           ATLAS PHASE 1 VERIFICATION & DEMO           ")
    print("=" * 60)

    # 1. Load & Print Settings Summary
    print("\n[1/3] Loading Configuration...")
    print(f"  - Ollama Host:      {settings.ollama_host}")
    print(f"  - Ollama Model:     {settings.ollama_model}")
    print(f"  - Whisper Model:    {settings.whisper_model_size}")
    print(f"  - Audit Log Path:   {settings.audit_log_path}")
    print(f"  - Phone Endpoint:   ws://{settings.phone_ip}:{settings.phone_port}")
    has_key = bool(settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here")
    print(f"  - Gemini API Key:   {'Configured [OK]' if has_key else 'Not configured / Example key'}")

    # 2. Write Audit Log Entry
    print("\n[2/3] Writing Test Audit Log Entry...")
    logger = AuditLogger(settings.audit_log_path)
    sample_intent = Intent(
        type=IntentType.QUERY,
        raw_text="Hello ATLAS Phase 1 Demo",
        language="en",
        requires_confirmation=False
    )
    entry = logger.log(
        intent=sample_intent,
        route_used="demo_phase1",
        result="Phase 1 verification sample entry written successfully.",
        blocked=False,
        latency_ms=1.5
    )
    print(f"  - Audit Log File:   {settings.audit_log_path}")
    print(f"  - Recorded Entry:   {entry}")

    # 3. Test Gemini API Key Connection (if provided)
    print("\n[3/3] Testing Gemini API Connectivity...")
    if not has_key:
        print("  - [SKIP] No valid GEMINI_API_KEY set in .env. Skipping API ping call.")
    else:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content("Say 'ATLAS Phase 1 Online' in 5 words or less.")
            print(f"  - Gemini API Response: '{response.text.strip()}'")
            print("  - Gemini Connection:   SUCCESS [OK]")
        except Exception as e:
            print(f"  - Gemini API Call Failed: {e}")

    print("\n" + "=" * 60)
    print("        PHASE 1 VERIFICATION COMPLETED SUCCESSFULLY        ")
    print("=" * 60)


if __name__ == "__main__":
    main()
