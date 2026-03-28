"""
decision_engine.py
Keyword-based rule logic to determine risk level from extracted symptoms.
Uses frozensets for O(1) lookup performance.
"""

HIGH_RISK_KEYWORDS = frozenset(
    {
        "chest pain",
        "chest tightness",
        "heart attack",
        "stroke",
        "seizure",
        "unconscious",
        "unresponsive",
        "difficulty breathing",
        "shortness of breath",
        "severe bleeding",
        "blood in urine",
        "blood in stool",
        "vomiting blood",
        "coughing blood",
        "paralysis",
        "sudden numbness",
        "severe head injury",
        "anaphylaxis",
        "allergic reaction",
        "severe allergic",
        "suicidal",
        "overdose",
        "poisoning",
    }
)

MEDIUM_RISK_KEYWORDS = frozenset(
    {
        "fever",
        "high temperature",
        "persistent cough",
        "abdominal pain",
        "stomach pain",
        "vomiting",
        "diarrhea",
        "dizziness",
        "fainting",
        "severe headache",
        "migraine",
        "back pain",
        "joint pain",
        "swelling",
        "rash",
        "skin rash",
        "infection",
        "urinary tract",
        "uti",
        "dehydration",
        "extreme fatigue",
        "blurred vision",
        "ear pain",
        "sore throat",
        "difficulty swallowing",
    }
)

LOW_RISK_KEYWORDS = frozenset(
    {
        "headache",
        "runny nose",
        "stuffy nose",
        "sneezing",
        "mild cough",
        "mild fever",
        "cold",
        "flu",
        "fatigue",
        "tiredness",
        "sore muscles",
        "minor cut",
        "bruise",
        "indigestion",
        "heartburn",
        "bloating",
        "mild nausea",
        "constipation",
        "dry skin",
        "itching",
        "insomnia",
    }
)


def _normalize_symptoms(symptoms: list[str]) -> frozenset[str]:
    return frozenset(s.lower().strip() for s in symptoms)


def _contains_keyword(symptoms_set: frozenset[str], keywords: frozenset[str]) -> bool:
    return bool(symptoms_set & keywords)


def classify_risk_level(symptoms: list[str]) -> str:
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

    symptoms_set = _normalize_symptoms(symptoms)

    if _contains_keyword(symptoms_set, HIGH_RISK_KEYWORDS):
        return "HIGH"

    if _contains_keyword(symptoms_set, MEDIUM_RISK_KEYWORDS):
        return "MEDIUM"

    return "LOW"
