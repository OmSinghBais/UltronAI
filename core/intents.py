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
