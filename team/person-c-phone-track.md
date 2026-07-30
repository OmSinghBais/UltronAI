# ATLAS — Phone Track (Person C)

You're building the phone control layer of **ATLAS**, a local voice-driven personal assistant. You don't need the full project history — this file plus `ATLAS_MASTER_PROMPT.md` is everything you need.

---

## Step 0: Read Spec First
Read [ATLAS_MASTER_PROMPT.md](file:///c:/Users/ASUS/Documents/SECOND%20SEMISTER/INTERNSHIP/ultron/ATLAS_MASTER_PROMPT.md) in full before doing anything else, specifically Section 5 on the **Phone Control Architecture (Accessibility Service + Local WebSocket Server)**.

---

## Your Scope (and ONLY your scope — do not touch `core/` or `control/`)
- `atlas-phone-companion/` — a SEPARATE Android Studio (Kotlin) project:
  - `AccessibilityControlService.kt` — handles tap/type/scroll/read commands via Android's Accessibility API
  - `WebSocketServer.kt` — runs a local WebSocket server on the phone (`ws://<phone-ip>:<phone-port>`); the laptop connects to it
  - `ScreenReader.kt` — walks the current screen's node tree, extracts text + element bounds
  - `MainActivity.kt` — permission setup UI only, not used at runtime
- `phone/bridge_server.py` — the Python-side WebSocket **CLIENT** (`PhoneController` class on laptop that connects to the phone's WebSocket server)
- `tests/phone/` — unit tests for the Python client (mock the WebSocket server); Android-side testing is manual for now

---

## Frozen Message Schema (Do not change without flagging the team in `PROGRESS.md`)

### Laptop → Phone Commands (JSON over WebSocket):
- **Tap**: `{"action": "tap", "x": 500, "y": 1200}`
- **Type**: `{"action": "type", "text": "Hello world"}`
- **Open App**: `{"action": "open_app", "package": "com.whatsapp"}`
- **Read Screen**: `{"action": "read_screen"}`

### Phone → Laptop Responses (JSON over WebSocket):
- **Success**: `{"status": "ok", "action": "tap"}`
- **Screen Tree Result**: `{"status": "ok", "elements": [{"text": "Chat", "bounds": [0, 100, 200, 300]}]}`
- **Error**: `{"status": "error", "reason": "Node not focusable"}`

---

## Active Repository Schemas (`config/settings.py` & `core/intents.py`)

#### Settings Configuration Excerpt (`config/settings.py`):
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    phone_ip: str = Field(default="192.168.1.100", validation_alias="PHONE_IP")
    phone_port: int = Field(default=8765, validation_alias="PHONE_PORT")
    adb_device_id: Optional[str] = Field(default=None, validation_alias="ADB_DEVICE_ID")

settings = Settings()
```

#### Phone Controller Python Client Target Interface (`phone/bridge_server.py`):
```python
import asyncio
import json
import websockets
from config.settings import settings

class PhoneController:
    def __init__(self, phone_ip: str = settings.phone_ip, port: int = settings.phone_port):
        self.uri = f"ws://{phone_ip}:{port}"
        self.ws = None

    async def connect(self):
        self.ws = await websockets.connect(self.uri)

    async def tap(self, x: int, y: int) -> dict:
        await self.ws.send(json.dumps({"action": "tap", "x": x, "y": y}))
        return json.loads(await self.ws.recv())

    async def type_text(self, text: str) -> dict:
        await self.ws.send(json.dumps({"action": "type", "text": text}))
        return json.loads(await self.ws.recv())

    async def open_app(self, package: str) -> dict:
        await self.ws.send(json.dumps({"action": "open_app", "package": package}))
        return json.loads(await self.ws.recv())

    async def read_screen(self) -> list:
        await self.ws.send(json.dumps({"action": "read_screen"}))
        res = json.loads(await self.ws.recv())
        return res.get("elements", [])
```

---

## Setup Note For Your Own Machine
1. Android Accessibility Service + "draw over other apps" permissions require a **MANUAL tap on the phone** — cannot be scripted or automated via ADB. Note this requirement and do not attempt to automate around it.
2. ADB is used **ONCE** to sideload the companion app onto the phone during setup; after that, ADB is out of the runtime control path entirely.

---

## Suggested Phases
- **Phase A**: Android WebSocket server (`WebSocketServer.kt`) + tap/type Accessibility Service commands working end to end
- **Phase B**: `ScreenReader.kt` (read_screen via node-tree walking)
- **Phase C**: `open_app` + connection reliability (auto-reconnect handling) + Python unit tests in `tests/phone/test_bridge_client.py`

---

## How You Report Progress
Update the **Phone Track** section of `PROGRESS.md` at the end of every session. This is the ONE shared status file for all three of us — don't create a separate log file.

---

## Working Style
- **Audit-first**: Before writing code for each phase, list what you're about to build in 3-5 bullets and why, wait for your user's go-ahead, then implement. One phase per session.
