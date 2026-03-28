"""
gemini_service.py
Handles all interactions with the Google Gemini API.
Responsible for: prompt construction, API call, raw response return.
"""

import os
import logging
import json

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Gemini client setup ───────────────────────────────────────────────────────
_model = None

def _get_model():
    global _model
    if _model is not None:
        return _model
    
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        logger.info("GEMINI_API_KEY is present.")
    else:
        logger.warning("GEMINI_API_KEY is missing!")
        return None
        
    genai.configure(api_key=api_key)
    _model = genai.GenerativeModel("gemini-pro")
    return _model

# ── Prompt template ───────────────────────────────────────────────────────────
_PROMPT_TEMPLATE = """
You are a medical-triage AI assistant (Version 1 baseline).

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
    Send user input to Gemini and return the raw parsed JSON dict.

    Returns:
        dict with keys: symptoms (list[str]), condition (str), risk_level (str), error (str|None)
    """
    logger.info("Received input for Gemini: %s", user_input)
    prompt = _PROMPT_TEMPLATE.format(user_input=user_input.strip())

    model = _get_model()
    if not model:
        logger.error("GEMINI_API_KEY is not set.")
        return {
            "symptoms": [],
            "condition": "Unknown",
            "risk_level": "LOW",
            "error": "Missing GEMINI_API_KEY configuration"
        }

    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        logger.info("Raw Gemini response: %s", raw_text)

        # Strip accidental markdown fences if model ignores instructions
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        parsed = json.loads(raw_text)
        condition = parsed.get("condition", "Unknown")
        if not condition:
            condition = "Unknown"

        return {
            "symptoms": parsed.get("symptoms", []),
            "condition": condition,
            "risk_level": parsed.get("risk_level", "LOW"),
            "error": None,
        }

    except Exception as exc:
        error_msg = str(exc)
        logger.error("Gemini API call or parsing failed: %s", error_msg, exc_info=True)
        
        user_facing_error = "Gemini processing failed"
        if "API key not valid" in error_msg or "API_KEY_INVALID" in error_msg:
            user_facing_error = "Invalid Gemini API Key configured in Environment."

        return {
            "symptoms": [],
            "condition": "Unknown",
            "risk_level": "LOW",
            "error": user_facing_error
        }
