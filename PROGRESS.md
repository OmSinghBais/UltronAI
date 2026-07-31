# ATLAS Progress

> **Last Updated:** 2026-07-31  
> **Overall Status:** Phase 7 (Hardening) — In Progress  
> **Test Count:** 68/68 passing · 2.97s

---

## Summary Table

| Track | Owner | Status |
|---|---|---|
| Core (Phases 1–4) | Core Lead | ✅ Complete |
| Control (Phases A–C) | Person B | ✅ Complete |
| Phone (Phases A–D + extras) | Person C | ✅ Complete |
| Integration (all tracks wired) | All | ✅ Complete |
| Phase 7 — Hardening & Demo | All | ⚠️ In Progress |

---

## Core Track (owned by Core Lead)

### Phase 1 — Scaffolding, Config, Audit Log
**Status: ✅ Complete**
- [2026-07-30] Established project scaffolding, `ATLAS_MASTER_PROMPT.md` specification, Pydantic settings loading, intent schemas, append-only JSONL audit logger, setup guide, unit tests (`tests/core/test_config_and_audit.py`), and verification script (`demo_phase1.py`). All tests passing.

### Phase 2 — Voice Loop (Wake Word → STT → TTS)
**Status: ✅ Complete**
- [2026-07-30] Implemented `core/wake_word.py` (openwakeword wrapper), `core/stt.py` (faster-whisper Hindi/English transcriber), `core/tts.py` (Piper TTS with numpy fallback), unit tests (`tests/core/test_voice_loop.py`), and `demo_phase2.py`.
- [2026-07-31] Refactored `core/stt.py` to expose `WhisperModel` at module level for mockability. Fixed `test_voice_loop.py` — replaced blocking HuggingFace model download with `unittest.mock` patches; all 4 voice tests run instantly offline.

### Phase 3 — Router (Gemini + Ollama with Fallback)
**Status: ✅ Complete**
- [2026-07-30] Implemented `core/router.py` with `is_online()` connectivity check, Gemini online reasoning (`gemini-1.5-flash`), and local Ollama (`qwen2.5:3b`) offline fallback. Unit tests `tests/core/test_router.py` (3/3 passing) and `demo_phase3.py`.
- ⚠️ **Known: `google-generativeai` SDK is deprecated** — emits `FutureWarning` on every run. Migration to `google-genai` is next planned task.

### Phase 4 — Core Orchestrator & Confirmation Gate
**Status: ✅ Complete**
- [2026-07-30] Implemented `core/orchestrator.py` tying wake word, STT, intent classification, AI routing, safety confirmation gate, desktop/browser/phone dispatch, TTS, and audit logging into a single asyncio loop. Unit tests `tests/core/test_orchestrator.py` (9/9 passing) and `demo_phase4.py`.
- [2026-07-31] Extended orchestrator with `PHONE_ACTION` intent dispatch → `PhoneController`. Added `phone: Optional[PhoneController]` constructor parameter and `_dispatch_phone_action()` async method.

---

## Control Track (owned by Person B)

### Phase A — Desktop Control & Tests
**Status: ✅ Complete**
- [2026-07-30] Implemented `control/desktop.py` (`open_app`, `type_text`, `click`, `screenshot`, `delete_path`). Test suite `tests/control/test_desktop.py` — **15/15 passing**.

### Phase B — Browser Automation & Tests
**Status: ✅ Complete**
- [2026-07-30] Implemented `control/browser.py` Playwright wrappers (`navigate`, `search`, `fill_form`, `read_page`). Test suite `tests/control/test_browser.py` — **11/11 passing**.

### Phase C — Confirmation Decorator & Face Gate
**Status: ✅ Complete**
- [2026-07-30] Implemented `control/confirmation.py` (`@requires_confirmation` decorator) and `control/face_gate.py` (Fernet-encrypted local face enrollment/verification). Test suite `tests/control/test_confirmation.py` — **10/10 passing**.
- Total control tests: **36/36 passing**.

---

## Phone Track (owned by Person C)

### Toolchain Setup — CLI-Only (no Android Studio)
**Status: ✅ Complete**
- [2026-07-31] OpenJDK 17, Android SDK `cmdline-tools/latest`, `platform-tools`, `platforms;android-34`, `build-tools;34.0.0`, Gradle 8.5 wrapper, `adb`. Builds headless via `./gradlew assembleDebug`.
- `atlas-phone-companion/local.properties` — `sdk.dir=$HOME/Library/Android/sdk` for macOS CLI builds.

### Phase A — Android WebSocket Server & Tap/Type
**Status: ✅ Complete**
- [2026-07-31] Kotlin project scaffolded: `AccessibilityControlService.kt`, `CompanionWebSocketServer.kt`, `ScreenReader.kt`, `MainActivity.kt`, `AndroidManifest.xml`. Commands: `tap`, `type`, `open_app`, `read_screen` via Accessibility APIs. APK built: `app-debug.apk` (5.4MB).

### Phase B — Screen Reader & Node Tree Walking
**Status: ✅ Complete**
- [2026-07-31] `ScreenReader.kt` walks active window node tree — extracts text, class names, bounding boxes, clickability.

### Phase C — App Launcher, Auto-Reconnect & Python Client Tests
**Status: ✅ Complete**
- [2026-07-31] `phone/bridge_server.py` — `PhoneController` with `tap`, `type_text`, `open_app`, `read_screen`, `scroll`.
- Auto-reconnect: `_ensure_connected()` with exponential back-off (0.5s/1s/1.5s). `_send()` shared helper used by all commands.
- `scroll(direction, x, y)` — `down/up/left/right` via `GestureDescription` swipe (400px, 300ms).
- Tests `tests/phone/test_bridge_client.py` — **15/15 passing** (covers reconnect paths, all scroll directions, invalid direction, `ConnectionClosed` auto-reset).

### Phase D — Physical Device Sideload & Live Verification
**Status: ✅ Complete**
- [2026-07-31] Sideloaded `app-debug.apk` onto physical Android device via `adb install -r`.
- Manually enabled Accessibility Service + Draw-over-apps on device (cannot be scripted).
- ADB port-forward tunnel: `adb forward tcp:8765 tcp:8765` — routes traffic through USB, bypasses Wi-Fi routing issues.
- Fixed Kotlin redeclaration build error — removed stale duplicate `WebSocketServer.kt`.
- **Live device smoke test — all passed:**
  ```
  ✅ connect()      → ws://127.0.0.1:8765 (ADB tunnel)
  ✅ read_screen()  → 9 real UI elements returned from device
  ✅ scroll("down") → {'status': 'ok', 'action': 'scroll', 'direction': 'down'}
  ✅ tap(540, 960)  → {'status': 'ok', 'action': 'tap'}
  ```
- Sideload guide: `docs/phone-sideload-guide.md`

---

## Integration Phase
**Status: ✅ Complete**
- [2026-07-31] All three tracks wired in `core/orchestrator.py`:
  - Desktop → `control/desktop.py`
  - Browser → `control/browser.py`
  - Phone → `phone/bridge_server.PhoneController` (WebSocket via ADB tunnel)
  - Sensitive actions → `control/confirmation.py` confirmation gate
  - All intents → `core/audit_log.py` JSONL append
- **68/68 tests passing in 2.97s. Zero network calls during test runs.**

---

## Phase 7 — Hardening & Demo (In Progress)

### ⚠️ Open Items

| # | Task | Priority | Notes |
|---|---|---|---|
| 1 | Migrate `google-generativeai` → `google-genai` in `core/router.py` | 🔴 High | Emits `FutureWarning` on every run; SDK is EOL |
| 2 | `demo_phase7.py` — full end-to-end voice loop with latency logging | 🔴 High | Spec: wake word → STT → router → action → TTS → audit < 3s |
| 3 | On-screen control indicator (floating overlay) | 🟡 Medium | Safety rail from `ATLAS_MASTER_PROMPT.md` — not yet built |
| 4 | ADB port-forward auto-setup on orchestrator startup | 🟡 Medium | Currently manual each session |
| 5 | `keyring` integration for credential storage | 🟡 Medium | Spec: credentials in OS keychain, not `.env` |
| 6 | SQLite command history (`aiosqlite`) | 🟢 Low | Spec mentions SQLite; only JSONL audit log exists |
| 7 | Integration tests with latency measurement | 🟢 Low | Phase 7 spec requirement |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          ATLAS — ULTRON AI                               │
│                                                                          │
│  Mic → WakeWord → STT → Orchestrator ──── Router ──→ Gemini / Ollama    │
│                              │                                           │
│                    ┌─────────┼──────────┐                               │
│                    ▼         ▼          ▼                                │
│              Desktop      Browser    Phone ──→ PhoneController           │
│              Control      Control    Control   (ws://127.0.0.1:8765      │
│                    └─────────┴──────────┘    via ADB port-forward)      │
│                              │                                           │
│                    ConfirmationGate (sensitive actions)                  │
│                    AuditLogger (append-only JSONL)                       │
│                    TTS → Speaker                                         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## ADB Quick Reference (each dev session)

```bash
# 1. Forward phone port through USB (run once per session)
adb forward tcp:8765 tcp:8765

# 2. Verify phone service is up
adb logcat -s AtlasWSServer

# 3. Rebuild + reinstall after Kotlin changes
cd atlas-phone-companion
ANDROID_HOME="$HOME/Library/Android/sdk" ./gradlew assembleDebug && cd ..
adb install -r atlas-phone-companion/app/build/outputs/apk/debug/app-debug.apk
# Toggle Accessibility OFF → ON on phone after reinstall

# 4. Run all tests
.venv313/bin/pytest tests/ -q
```
