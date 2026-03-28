"""
utils/validators.py
Input sanitization and validation helpers.
"""

import re
from typing import Optional


# Maximum allowed characters for user input
MAX_INPUT_LENGTH = 2000
MIN_INPUT_LENGTH = 3


def sanitize_input(text: str) -> str:
    """
    Strip leading/trailing whitespace and collapse internal whitespace.
    Removes control characters that could cause prompt injection issues.

    Args:
        text: raw user input string

    Returns:
        Cleaned string
    """
    # Remove null bytes and other control chars (keep newlines for readability)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Collapse multiple spaces/tabs into a single space
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def validate_input_length(text: str) -> Optional[str]:
    """
    Validate that input is within acceptable length bounds.

    Returns:
        Error message string if invalid, None if valid.
    """
    if len(text) < MIN_INPUT_LENGTH:
        return f"Input is too short (minimum {MIN_INPUT_LENGTH} characters)."
    if len(text) > MAX_INPUT_LENGTH:
        return f"Input is too long (maximum {MAX_INPUT_LENGTH} characters)."
    return None


def is_meaningful_input(text: str) -> bool:
    """
    Rudimentary check that input contains at least one word of 3+ characters.
    Prevents single-character or symbol-only submissions from reaching Gemini.
    """
    words = text.split()
    return any(len(w) >= 3 for w in words)
