"""
tests/test_decision_engine.py
Unit tests for decision_engine.classify_risk().
No external dependencies — purely tests keyword-based logic.
"""

import sys
import os

# Ensure project root is on path when running from tests/ or project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from decision_engine import classify_risk


class TestClassifyRiskHigh:
    def test_chest_pain_returns_high(self):
        assert classify_risk(["chest pain"]) == "HIGH"

    def test_difficulty_breathing_returns_high(self):
        assert classify_risk(["difficulty breathing", "dizziness"]) == "HIGH"

    def test_stroke_returns_high(self):
        assert classify_risk(["stroke symptoms", "headache"]) == "HIGH"

    def test_high_takes_priority_over_medium(self):
        assert classify_risk(["fever", "chest pain", "fatigue"]) == "HIGH"


class TestClassifyRiskMedium:
    def test_fever_returns_medium(self):
        assert classify_risk(["fever"]) == "MEDIUM"

    def test_vomiting_returns_medium(self):
        assert classify_risk(["vomiting", "diarrhea"]) == "MEDIUM"

    def test_abdominal_pain_returns_medium(self):
        assert classify_risk(["abdominal pain"]) == "MEDIUM"

    def test_rash_returns_medium(self):
        assert classify_risk(["rash", "itching"]) == "MEDIUM"


class TestClassifyRiskLow:
    def test_headache_only_returns_low(self):
        assert classify_risk(["headache"]) == "LOW"

    def test_runny_nose_returns_low(self):
        assert classify_risk(["runny nose", "sneezing"]) == "LOW"

    def test_empty_symptoms_returns_low(self):
        assert classify_risk([]) == "LOW"

    def test_unknown_symptoms_return_low(self):
        assert classify_risk(["some vague feeling"]) == "LOW"


class TestClassifyRiskEdgeCases:
    def test_single_space_symptom(self):
        result = classify_risk([" "])
        assert result in ("LOW", "MEDIUM", "HIGH")

    def test_mixed_case_symptoms(self):
        # Normalization converts to lowercase before matching
        assert classify_risk(["Chest Pain"]) == "HIGH"
        assert classify_risk(["FEVER"]) == "MEDIUM"
