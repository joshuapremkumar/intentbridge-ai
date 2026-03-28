"""
decision_engine.py
Keyword-based rule logic to determine risk level from extracted symptoms.
Deliberately simple — Version 1 baseline. No ML, no Gemini dependency.
"""

from typing import List

# ── Keyword dictionaries ──────────────────────────────────────────────────────

HIGH_RISK_KEYWORDS = {
    "chest pain", "chest tightness", "heart attack", "stroke", "seizure",
    "unconscious", "unresponsive", "difficulty breathing", "shortness of breath",
    "severe bleeding", "blood in urine", "blood in stool", "vomiting blood",
    "coughing blood", "paralysis", "sudden numbness", "severe head injury",
    "anaphylaxis", "allergic reaction", "severe allergic",
    "suicidal", "overdose", "poisoning",
}

MEDIUM_RISK_KEYWORDS = {
    "fever", "high temperature", "persistent cough", "abdominal pain",
    "stomach pain", "vomiting", "diarrhea", "dizziness", "fainting",
    "severe headache", "migraine", "back pain", "joint pain", "swelling",
    "rash", "skin rash", "infection", "urinary tract", "uti",
    "dehydration", "extreme fatigue", "blurred vision", "ear pain",
    "sore throat", "difficulty swallowing",
}

LOW_RISK_KEYWORDS = {
    "headache", "runny nose", "stuffy nose", "sneezing", "mild cough",
    "mild fever", "cold", "flu", "fatigue", "tiredness", "sore muscles",
    "minor cut", "bruise", "indigestion", "heartburn", "bloating",
    "mild nausea", "constipation", "dry skin", "itching", "insomnia",
}


def classify_risk_level(symptoms: List[str]) -> str:
    """
    Determine risk level (LOW / MEDIUM / HIGH) from a list of symptom strings.

    Logic (priority order):
    1. Any HIGH keyword match → HIGH
    2. Any MEDIUM keyword match → MEDIUM
    3. Anything else → LOW

    Args:
        symptoms: list of symptom strings from Gemini extraction

    Returns:
        str: "LOW", "MEDIUM", or "HIGH"
    """
    if not symptoms:
        return "LOW"

    normalized = [s.lower().strip() for s in symptoms]

    for symptom in normalized:
        for keyword in HIGH_RISK_KEYWORDS:
            if keyword in symptom:  # symptom contains the keyword phrase
                return "HIGH"

    for symptom in normalized:
        for keyword in MEDIUM_RISK_KEYWORDS:
            if keyword in symptom:  # symptom contains the keyword phrase
                return "MEDIUM"

    return "LOW"
