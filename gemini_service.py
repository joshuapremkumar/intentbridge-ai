"""
gemini_service.py
Handles all interactions with the Google Gemini API.
Responsible for: prompt construction, API call, raw response return.
"""

import json
import logging
import os
import re
import threading
from dataclasses import dataclass
from typing import Optional

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class GeminiResult:
    symptoms: list[str]
    condition: str
    risk_level: str
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "symptoms": self.symptoms,
            "condition": self.condition,
            "risk_level": self.risk_level,
            "error": self.error,
        }


_model_lock = threading.Lock()
_model: Optional[genai.GenerativeModel] = None


def _get_model() -> Optional[genai.GenerativeModel]:
    global _model
    if _model is not None:
        return _model

    with _model_lock:
        if _model is not None:
            return _model

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY is missing!")
            return None

        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-2.0-flash")
        logger.info("GEMINI_API_KEY is present.")
        return _model


def _escape_user_input(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


_PROMPT_TEMPLATE = """You are a medical-triage AI assistant (Version 1 baseline).

Analyze the user input below and respond ONLY with valid JSON — no markdown, no extra text.

Required JSON format:
{{
  "symptoms": ["symptom1", "symptom2"],
  "condition": "possible condition or empty string if unclear",
  "risk_level": "LOW | MEDIUM | HIGH"
}}

Rules:
- symptoms: array of concise keyword strings (e.g. ["headache", "fever", "fatigue"])
- condition: single string — your best guess at a possible condition, or "" if not determinable
- risk_level: exactly one of "LOW", "MEDIUM", or "HIGH"
- Do NOT wrap in markdown code fences
- Do NOT include any text outside the JSON object

User input:
\"\"\"{user_input}\"\"\"
"""


def call_gemini(user_input: str) -> dict:
    """
    Send user input to Gemini and return the parsed result dict.

    Returns:
        dict with keys: symptoms (list[str]), condition (str), risk_level (str), error (str|None)
    """
    logger.info("Received input for Gemini: %s", user_input)
    safe_input = _escape_user_input(user_input.strip())
    prompt = _PROMPT_TEMPLATE.format(user_input=safe_input)

    model = _get_model()
    if not model:
        logger.error("GEMINI_API_KEY is not set.")
        return GeminiResult(
            symptoms=[],
            condition="Unknown",
            risk_level="LOW",
            error="Missing GEMINI_API_KEY configuration",
        ).to_dict()

    try:
        response = model.generate_content(prompt, timeout=30.0)
        raw_text = response.text.strip()
        logger.info("Raw Gemini response: %s", raw_text)

        raw_text = _strip_markdown_fences(raw_text)

        parsed = json.loads(raw_text)
        condition = parsed.get("condition") or "Unknown"
        valid_risk = parsed.get("risk_level", "LOW")
        if valid_risk not in ("LOW", "MEDIUM", "HIGH"):
            valid_risk = "LOW"

        return GeminiResult(
            symptoms=parsed.get("symptoms", []),
            condition=condition,
            risk_level=valid_risk,
            error=None,
        ).to_dict()

    except json.JSONDecodeError as exc:
        logger.error("JSON parsing failed: %s", exc)
        return GeminiResult(
            symptoms=[],
            condition="Unknown",
            risk_level="LOW",
            error="Failed to parse Gemini response",
        ).to_dict()

    except Exception as exc:
        error_msg = str(exc)
        logger.error("Gemini API call failed: %s", error_msg, exc_info=True)

        if "API key not valid" in error_msg or "API_KEY_INVALID" in error_msg:
            user_facing_error = "Invalid Gemini API Key configured in Environment."
        else:
            user_facing_error = "Gemini processing failed"

        return GeminiResult(
            symptoms=[],
            condition="Unknown",
            risk_level="LOW",
            error=user_facing_error,
        ).to_dict()


def _strip_markdown_fences(text: str) -> str:
    match = re.match(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text
