"""
ATLAS — Credentials Management Module
Handles secure OS Keychain access via keyring for sensitive API keys and tokens.
"""

import logging
from typing import Optional

try:
    import keyring
except ImportError:
    keyring = None

SERVICE_NAME = "atlas_ultron_ai"


def set_credential(key_name: str, secret_value: str) -> bool:
    """Stores a secret in OS Keychain under the ATLAS service."""
    if keyring is None:
        logging.warning("keyring module not available. Install keyring for OS keychain support.")
        return False
    try:
        keyring.set_password(SERVICE_NAME, key_name, secret_value)
        return True
    except Exception as e:
        logging.error(f"Failed to set credential '{key_name}' in keychain: {e}")
        return False


def get_credential(key_name: str) -> Optional[str]:
    """Retrieves a secret from OS Keychain."""
    if keyring is None:
        return None
    try:
        return keyring.get_password(SERVICE_NAME, key_name)
    except Exception as e:
        logging.error(f"Failed to get credential '{key_name}' from keychain: {e}")
        return None


def delete_credential(key_name: str) -> bool:
    """Deletes a secret from OS Keychain."""
    if keyring is None:
        return False
    try:
        keyring.delete_password(SERVICE_NAME, key_name)
        return True
    except Exception as e:
        logging.error(f"Failed to delete credential '{key_name}' from keychain: {e}")
        return False
