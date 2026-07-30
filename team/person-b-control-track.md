# ATLAS — Control Track (Person B)

You're building the `control/` module of **ATLAS**, a local voice-driven personal assistant. You don't need the full project history — this file plus `ATLAS_MASTER_PROMPT.md` is everything you need.

---

## Step 0: Read Spec First
Read [ATLAS_MASTER_PROMPT.md](file:///c:/Users/ASUS/Documents/SECOND%20SEMISTER/INTERNSHIP/ultron/ATLAS_MASTER_PROMPT.md) in full before doing anything else. It is the single source of truth for the whole project. This file only tells you which slice is yours.

---

## Your Scope (and ONLY your scope — do not touch `core/` or `phone/`)
- `control/desktop.py` — `pyautogui`/`pynput` wrappers: `open_app`, `type_text`, `click`, `screenshot`, `delete_path`
- `control/browser.py` — Playwright wrappers: `navigate`, `search`, `fill_form`, `read_page`
- `control/confirmation.py` — the `@requires_confirmation` decorator wrapper
- `control/face_gate.py` — local face enrollment + verification (encrypted at rest using `cryptography.fernet`, never leaves device)
- `tests/control/` — unit tests for all of the above

---

## Frozen Interface & Data Schemas (Do not change without flagging the team in `PROGRESS.md`)

Every function you write in `control/` must return a Python dictionary with a `"status"` key:
- Successful result: `{"status": "ok", "action": "...", "data": ...}`
- Cancelled/Blocked result: `{"status": "cancelled", "reason": "not confirmed"}`
- Error result: `{"status": "error", "error": "description"}`

This is what `core/orchestrator.py` expects when invoking control functions.

### Active Repository Schemas (`core/intents.py` & `config/settings.py`)

#### Intent Schema (`core/intents.py`):
```python
from enum import Enum
from typing import Dict, Any
from pydantic import BaseModel, Field

class IntentType(str, Enum):
    QUERY = "query"                      # Informational, no side effects
    DESKTOP_ACTION = "desktop_action"     # Open app, type, click, navigation (non-sensitive)
    BROWSER_ACTION = "browser_action"     # Browse, search, read page (non-sensitive)
    PHONE_ACTION = "phone_action"         # Phone navigation, read screen (non-sensitive)
    SENSITIVE_ACTION = "sensitive_action" # Login/logout, payment, delete, send message/call, credentials

class Intent(BaseModel):
    type: IntentType
    raw_text: str
    language: str = Field(default="en")   # "en" | "hi"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = Field(default=False)
```

#### Settings Schema Excerpt (`config/settings.py`):
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    confirmation_timeout_s: int = Field(default=15, validation_alias="CONFIRMATION_TIMEOUT_S")
    # Face embedding storage path
    face_embedding_path: str = Field(default="./storage/face_embedding.enc")
    
settings = Settings()
```

---

## Confirmation Policy (Already Decided — Do Not Relitigate)

Full autonomous control (no confirmation, no delay) for:
- Typing, clicking, navigating, opening/closing apps, switching windows/tabs
- Reading screen content, taking screenshots, reading clipboard
- Browsing, searching, scrolling, filling non-sensitive form fields
- Non-destructive file operations (create, read, move within workspace folder)

**Confirmation REQUIRED** (via `@requires_confirmation` decorator) for ONLY these 5 categories:
1. Logging into or out of any account
2. Any action involving money (purchases, transfers, payments)
3. Deleting files or data
4. Sending a message, email, or making a call on my behalf
5. Entering or transmitting any password, OTP, or payment credential

---

## Suggested Phases (Mirror project's Phase structure)
- **Phase A**: `control/desktop.py` + tests in `tests/control/test_desktop.py`
- **Phase B**: `control/browser.py` + tests in `tests/control/test_browser.py`
- **Phase C**: `control/confirmation.py` + `control/face_gate.py` + tests in `tests/control/test_confirmation.py`

---

## How You Report Progress
Update the **Control Track** section of `PROGRESS.md` at the end of every session — what's done, what's blocked, what's next. This is the ONE shared status file for all three of us; don't create a separate log file.

---

## Working Style
- **Audit-first**: Before writing code for each phase, list what you're about to build in 3-5 bullets and why, wait for your user's go-ahead, then implement. One phase per session.
