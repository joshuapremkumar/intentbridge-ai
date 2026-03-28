"""
tests/test_decision_engine.py
Unit tests for decision_engine.classify_risk_level().
No external dependencies — purely tests keyword-based logic.
"""

from decision_engine import classify_risk_level


class TestClassifyRiskHigh:
    def test_chest_pain_returns_high(self) -> None:
        assert classify_risk_level(["chest pain"]) == "HIGH"

    def test_difficulty_breathing_returns_high(self) -> None:
        assert classify_risk_level(["difficulty breathing", "dizziness"]) == "HIGH"

    def test_stroke_returns_high(self) -> None:
        assert classify_risk_level(["stroke", "headache"]) == "HIGH"

    def test_high_takes_priority_over_medium(self) -> None:
        assert classify_risk_level(["fever", "chest pain", "fatigue"]) == "HIGH"


class TestClassifyRiskMedium:
    def test_fever_returns_medium(self) -> None:
        assert classify_risk_level(["fever"]) == "MEDIUM"

    def test_vomiting_returns_medium(self) -> None:
        assert classify_risk_level(["vomiting", "diarrhea"]) == "MEDIUM"

    def test_abdominal_pain_returns_medium(self) -> None:
        assert classify_risk_level(["abdominal pain"]) == "MEDIUM"

    def test_rash_returns_medium(self) -> None:
        assert classify_risk_level(["rash", "itching"]) == "MEDIUM"


class TestClassifyRiskLow:
    def test_headache_only_returns_low(self) -> None:
        assert classify_risk_level(["headache"]) == "LOW"

    def test_runny_nose_returns_low(self) -> None:
        assert classify_risk_level(["runny nose", "sneezing"]) == "LOW"

    def test_empty_symptoms_returns_low(self) -> None:
        assert classify_risk_level([]) == "LOW"

    def test_unknown_symptoms_return_low(self) -> None:
        assert classify_risk_level(["some vague feeling"]) == "LOW"


class TestClassifyRiskEdgeCases:
    def test_single_space_symptom(self) -> None:
        assert classify_risk_level([" "]) == "LOW"

    def test_mixed_case_symptoms(self) -> None:
        assert classify_risk_level(["Chest Pain"]) == "HIGH"
        assert classify_risk_level(["FEVER"]) == "MEDIUM"

    def test_whitespace_only_symptoms(self) -> None:
        assert classify_risk_level(["   ", "\t", "\n"]) == "LOW"
