"""
ATLAS — Confirmation Module
Provides the @requires_confirmation decorator for sensitive control operations.
Confirmation REQUIRED for:
1. Logging into or out of any account
2. Any action involving money (purchases, transfers, payments)
3. Deleting files or data
4. Sending a message, email, or making a call on my behalf
5. Entering or transmitting any password, OTP, or payment credential
"""

from functools import wraps
from typing import Any, Callable, Dict, Optional, Union


def requires_confirmation(
    category: str, prompt: Optional[str] = None
) -> Callable:
    """
    Decorator that gates sensitive control functions behind a confirmation callback.

    Parameters:
    - category: Category of sensitive action (e.g., 'delete_file', 'payment', 'login', 'messaging', 'credentials').
    - prompt: Optional custom message describing the action requiring confirmation.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            *args: Any,
            confirm_fn: Optional[Callable[[str], bool]] = None,
            **kwargs: Any,
        ) -> Dict[str, Any]:
            action_name = getattr(func, "__name__", "unknown_action")
            action_prompt = (
                prompt
                or f"Confirmation required for action '{action_name}' (Category: {category}). Proceed?"
            )

            if confirm_fn is not None:
                try:
                    is_confirmed = confirm_fn(action_prompt)
                except Exception as e:
                    return {
                        "status": "error",
                        "error": f"Confirmation prompt callback failed: {str(e)}",
                    }
            else:
                # If no confirm_fn provided, default to blocked for safety
                return {
                    "status": "cancelled",
                    "reason": f"No confirmation callback provided for sensitive action '{action_name}'",
                }

            if not is_confirmed:
                return {"status": "cancelled", "reason": "not confirmed"}

            return func(*args, **kwargs)

        return wrapper

    return decorator
