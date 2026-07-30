# ATLAS Progress

## Core Track (owned by Core Lead)
### Phase 1 — Scaffolding, Config, Audit Log
Status: Demo-ready
- [2026-07-30] Established project scaffolding, `ATLAS_MASTER_PROMPT.md` specification, Pydantic settings loading, intent schemas, append-only JSONL audit logger, Windows setup guide, unit tests (`tests/core/test_config_and_audit.py`), and verification script (`demo_phase1.py`). All tests passing.

### Phase 2 — Voice Loop (Wake Word → STT → TTS)
Status: Demo-ready
- [2026-07-30] Implemented `core/wake_word.py` (openwakeword wrapper), `core/stt.py` (faster-whisper Hindi/English transcriber), `core/tts.py` (Piper TTS speech synthesis), unit tests (`tests/core/test_voice_loop.py`), and `demo_phase2.py` voice pipeline echo test.

### Phase 3 — Router (Gemini + Ollama with Fallback)
Status: Demo-ready
- [2026-07-30] Implemented `core/router.py` with online connectivity check (`is_online()`), online Gemini reasoning (`gemini-1.5-flash`), and local Ollama (`qwen2.5:3b`) offline fallback engine. Created unit tests `tests/core/test_router.py` (all tests passing) and `demo_phase3.py`.

### Phase 4 — Core Orchestrator & Confirmation Gate Integration
Status: Demo-ready
- [2026-07-30] Implemented `core/orchestrator.py` tying wake word detection, STT, intent classification, AI routing, safety confirmation gating (`_confirm()`), desktop control dispatching, TTS audio feedback, and audit logging into an asyncio loop. Created unit tests `tests/core/test_orchestrator.py` (all tests passing) and `demo_phase4.py`.

---

## Control Track (owned by Person B)
### Phase A — Desktop Control & Tests
Status: Complete
- [2026-07-30] Implemented `control/desktop.py` wrappers (`open_app`, `type_text`, `click`, `screenshot`, `delete_path`) with standardized response schema. Created test suite in `tests/control/test_desktop.py` (15/15 unit tests passing).

### Phase B — Browser Automation & Tests
Status: Complete
- [2026-07-30] Implemented `control/browser.py` Playwright wrappers (`navigate`, `search`, `fill_form`, `read_page`) with standardized dict response schema. Created test suite in `tests/control/test_browser.py` (all 26 control unit tests passing).

### Phase C — Confirmation Decorator & Face Gate
Status: Complete
- [2026-07-30] Implemented `control/confirmation.py` (`@requires_confirmation` decorator wrapper for sensitive actions), `control/face_gate.py` (local face enrollment/verification encrypted at rest via `cryptography.fernet`), and test suite in `tests/control/test_confirmation.py` (all 36 control unit tests passing).

---

## Phone Track (owned by Person C)
### Phase A — Android WebSocket Server & Tap/Type Commands
Status: Complete
- [2026-07-30] Created `atlas-phone-companion` Android Studio project with `AccessibilityControlService`, `CompanionWebSocketServer` (`ws://<phone-ip>:8765`), and setup UI in `MainActivity`. Implemented `tap`, `type`, `open_app`, and `read_screen` handler actions via Accessibility APIs. Implemented `PhoneController` Python WebSocket client in `phone/bridge_server.py`.

### Phase B — Screen Reader & Element Tree Walking
Status: Not started

### Phase C — App Launcher, Reconnection & Python Client Tests
Status: Not started

---

## Integration Phase (all three tracks merge)
Status: blocked until Control and Phone tracks report Phase C complete
