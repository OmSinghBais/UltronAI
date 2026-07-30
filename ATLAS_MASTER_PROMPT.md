# ATLAS — MASTER SPECIFICATION (Single Source of Truth)

> **Important**: This document merges the original Master Build Prompt and all follow-up updates (Fast-Control confirmation policy, Android Accessibility Service phone architecture). Antigravity MUST re-read this file at the start of every session to align with the active specification.

---

## PART 1 — VISION & CONTRACT

Build **ATLAS**, a voice-driven personal assistant that:
- Wakes offline on "Hey Atlas", understands Hindi + English (code-switched fine)
- Controls the laptop (keyboard, mouse, apps, browser, files) and an Android phone (nav, typing, screen read)
- Reason via Gemini API when online, falls back to a local Ollama model when offline
- Runs entirely on free tools/free-tier APIs, no Docker, single long-running Python process as the hub

### Non-negotiable Safety Rails & Execution Rules:
1. **Updated Confirmation Policy**:
   - **Full autonomous control (no confirmation, no delay)** for:
     - Typing, clicking, navigating, opening/closing apps, switching windows/tabs
     - Reading screen content, taking screenshots, reading clipboard
     - Browsing, searching, scrolling, filling non-sensitive form fields
     - All phone navigation, app opening, reading phone screen state
     - File operations that are non-destructive (create, read, move within workspace folder)
   - **Spoken/Typed Confirmation REQUIRED** for:
     - Logging into or out of any account
     - Any action involving money (purchases, transfers, payments)
     - Deleting files or data
     - Sending a message, email, or making a call on my behalf
     - Entering or transmitting any password, OTP, or payment credential
2. **No Credentials in Code/Config/Logs**:
   - Credentials stored in OS keychain via `keyring`. Human triggers each login.
3. **Audit Log Mandatory**:
   - Every action is appended to an immutable JSONL audit log — command in, action taken, result, latency, blocked state — timestamped.
4. **Visible Control Indicator**:
   - Visible on-screen indicator whenever ATLAS holds mouse/keyboard control.
5. **Offline Wake-Word**:
   - Wake-word detection is 100% offline; no audio leaves device until after wake word fires.

---

## PART 2 — SYSTEM ARCHITECTURE

### 2.1 Component Diagram
```
┌──────────────────────────────────────────────────────────────────────┐
│                         ATLAS CORE (laptop, one asyncio process)      │
│                                                                        │
│  ┌───────────┐   ┌──────────┐   ┌────────────┐   ┌─────────────┐    │
│  │ WakeWord  │──▶│   STT    │──▶│   Router    │──▶│     TTS      │   │
│  │ (offline) │   │ (Whisper)│   │ Gemini/     │   │   (Piper)    │   │
│  └───────────┘   └──────────┘   │ Ollama      │   └─────────────┘   │
│                                  └──────┬──────┘                     │
│                                         │ intent + args               │
│                                         ▼                             │
│                          ┌──────────────────────────┐                │
│                          │      Action Dispatcher     │               │
│                          │  (confirmation gate here)  │               │
│                          └──────┬───────────┬────────┘               │
│                                 │           │                        │
│                     ┌───────────┘           └────────────┐           │
│                     ▼                                     ▼          │
│           ┌──────────────────┐                  ┌──────────────────┐│
│           │  Desktop/Browser   │                  │  Phone Controller││
│           │  Control Module    │                  │(WebSocket Client)││
│           └──────────────────┘                  └────────┬─────────┘│
│                                                          │          │
│           ┌────────────────────────────────────────────┐ │          │
│           │              Audit Logger (JSONL)          │◀┘          │
│           └────────────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────────────┘
                                    │ WebSocket (LAN)
                                    ▼
                     ┌──────────────────────────────┐
                     │  Phone Companion (Android)   │
                     │ Accessibility Service + Srv  │
                     └──────────────────────────────┘
```

### 2.2 Sequence Flow — Normal Command ("what's on my calendar today")
```
User → WakeWord: "Hey Atlas"
WakeWord → Orchestrator: wake_detected event
Orchestrator → STT: start_recording()
User → STT: "what's on my calendar today"
STT → Router: transcript, lang="en"
Router → Router: classify intent (query) → route to Gemini (online) or Ollama (offline)
Router → LLM: prompt + context
LLM → Router: response text
Router → TTS: speak(response)
Orchestrator → AuditLog: log(command, route_used, response, latency_ms)
```

### 2.3 Sequence Flow — Sensitive Action ("send email to John")
```
User → WakeWord → STT → Router: intent classified as SENSITIVE_ACTION
Router → Orchestrator: requires_confirmation=True
Orchestrator → TTS: "This will send an email to John. Confirm?"
User → STT: "yes"
  if "yes": proceed to action execution
  if not "yes" / timeout: abort, TTS: "Action cancelled", AuditLog.log(BLOCKED)
Orchestrator → ControlModule: execute action
Orchestrator → AuditLog: log(full action chain, outcome)
Orchestrator → TTS: "Email sent to John"
```

---

## PART 3 — TECH STACK

| Layer | Tool | Why |
|---|---|---|
| Wake word | `openwakeword` | Offline, open source |
| STT | `faster-whisper` (small/medium) | Local, handles Hindi+English, fast on CPU |
| TTS | `piper-tts` | Local, low-latency, natural enough |
| Online reasoning | Gemini API (`google-generativeai`, free tier) | Strong reasoning when online |
| Offline reasoning | Ollama + `qwen2.5:3b` or `phi3:mini` | Fast local fallback |
| Desktop control | `pyautogui`, `pynput` | Keyboard/mouse cross-platform |
| Browser control | `playwright` | Reliable DOM-aware automation |
| Phone control | Android Companion App (Accessibility Service + WebSocket) | Fast, low latency, no ADB per command |
| Orchestrator | Python 3.11 `asyncio` | Single process, event-driven |
| Config | `pydantic-settings` | Typed config, validates `.env` |
| Storage | SQLite (`aiosqlite`) & JSONL | Command history, audit trails |
| Testing | `pytest`, `pytest-asyncio`, `unittest.mock` | Automated testing |

---

## PART 4 — REPO STRUCTURE
```
ultron/
├── ATLAS_MASTER_PROMPT.md
├── PROGRESS.md
├── BUGS.md
├── TESTING.md
├── SETUP.md
├── requirements.txt
├── .env.example
├── demo_phase1.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── core/
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── wake_word.py
│   ├── stt.py
│   ├── tts.py
│   ├── router.py
│   ├── intents.py
│   └── audit_log.py
├── control/
│   ├── __init__.py
│   ├── desktop.py
│   ├── browser.py
│   └── confirmation.py
├── phone/
│   ├── __init__.py
│   ├── bridge_server.py (WebSocket client connecting to phone)
│   └── companion_client.py
├── atlas-phone-companion/
│   └── (Android Kotlin project with AccessibilityService)
├── storage/
│   └── audit.jsonl
└── tests/
    ├── core/
    ├── control/
    └── phone/
```

---

## PART 5 — PHONE CONTROL ARCHITECTURE (ACCESSIBILITY SERVICE + WEBSOCKET)

### 5.1 Overview
- One-time setup: ADB sideloads `atlas-phone-companion` app onto phone. Human grants Accessibility Service + Draw Over Apps permissions once.
- Runtime control: The Android app runs a local WebSocket server (`ws://<phone-ip>:8765`). ATLAS on laptop connects once and keeps socket open.
- Commands: `tap`, `type`, `open_app`, `read_screen` (returns element tree with text and bounds).

### 5.2 Companion App Skeleton (`AccessibilityControlService.kt`)
```kotlin
class AccessibilityControlService : AccessibilityService() {
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    fun performTap(x: Int, y: Int) {
        val path = Path().apply { moveTo(x.toFloat(), y.toFloat()) }
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, 50))
            .build()
        dispatchGesture(gesture, null, null)
    }

    fun performTypeText(text: String) {
        val node = findFocusedEditableNode() ?: return
        val arguments = Bundle().apply {
            putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text)
        }
        node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments)
    }

    fun readScreenTree(): List<ScreenElement> {
        val root = rootInActiveWindow ?: return emptyList()
        return walkNodeTree(root)
    }
}
```

---

## PART 6 — PHASE-BY-PHASE PLAN (7 Phases)

### Phase 1 — Scaffolding + Config + Audit Log
Files: `ATLAS_MASTER_PROMPT.md`, `config/settings.py`, `core/audit_log.py`, `core/intents.py`, `PROGRESS.md`, `BUGS.md`, `TESTING.md`, `requirements.txt`, `.env.example`, `SETUP.md`, `demo_phase1.py`
Demo: script that loads settings, writes one audit log entry, confirms Gemini API key is valid with a trivial call.
Tests: config loads and validates; audit log writes and reads back valid JSONL.

### Phase 2 — Voice Loop (Wake Word → STT → TTS, no LLM yet)
Files: `core/wake_word.py`, `core/stt.py`, `core/tts.py`
Demo: say "Hey Atlas," speak a sentence in English/Hindi, transcribed and echoed back via TTS.
Tests: mock audio input → verify transcription pipeline; verify TTS output generation.

### Phase 3 — Router (Gemini + Ollama with fallback)
Files: `core/router.py`
Demo: ask a question while online → Gemini answers. Disable WiFi → Ollama answers, no crash.
Tests: mock online/offline states, verify fallback logic when Gemini fails or network drops.

### Phase 4 — Desktop Control + Confirmation Gate
Files: `control/desktop.py`, `control/confirmation.py`, `core/orchestrator.py` (fill in `_confirm`)
Demo: non-sensitive actions (open app, type text) execute autonomously. Sensitive actions (delete file, send email) trigger spoken confirmation.
Tests: confirmation decorator — mock confirm_fn True/False, verify action execution.

### Phase 5 — Face Gate / Advanced Safety (Optional Stretch)
Files: `control/face_gate.py`
Demo: Optional face verification for high-risk actions.

### Phase 6 — Phone Companion App + Fast WebSocket Bridge
Files: `atlas-phone-companion/`, `phone/bridge_server.py` (client)
Demo: Laptop connects to phone WebSocket server over WiFi, sends tap/type/read_screen commands with <500ms latency.
Tests: mock WebSocket communication round-trip.

### Phase 7 — Integration, Latency Pass, Hardening
Files: Full repository integration, remove stubs.
Demo: End-to-end flow from wake word to routing, execution, confirmation, TTS, and audit log under 3s.
Tests: Integration tests across intent types and latency measurement.
