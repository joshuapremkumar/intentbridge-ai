"""
tests/test_app.py
Integration tests for the FastAPI /analyze endpoint.
Uses TestClient (no real Gemini calls — Gemini is mocked).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

# Set a dummy key so gemini_service module-level init doesn't raise
os.environ.setdefault("GEMINI_API_KEY", "test-key-placeholder")

from app import app

client = TestClient(app)

# ── Helpers ───────────────────────────────────────────────────────────────────
MOCK_GEMINI_HIGH = {
    "symptoms": ["chest pain", "shortness of breath"],
    "condition": "possible cardiac event",
    "error": None,
}

MOCK_GEMINI_LOW = {
    "symptoms": ["mild headache", "tiredness"],
    "condition": "common cold",
    "error": None,
}

MOCK_GEMINI_ERROR = {
    "symptoms": [],
    "condition": "",
    "error": "Gemini API timeout",
}


# ── Health check tests ────────────────────────────────────────────────────────
class TestHealthCheck:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "IntentBridge AI"

    def test_health_returns_version(self):
        response = client.get("/health")
        assert "version" in response.json()


# ── /analyze endpoint tests ───────────────────────────────────────────────────
class TestAnalyzeEndpoint:
    @patch("app.call_gemini", return_value=MOCK_GEMINI_HIGH)
    def test_high_risk_response(self, mock_gemini):
        response = client.post("/analyze", json={"input": "I have chest pain and can't breathe"})
        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"] == "HIGH"
        assert "chest pain" in data["extracted_data"]["symptoms"]
        assert data["extracted_data"]["condition"] == "possible cardiac event"

    @patch("app.call_gemini", return_value=MOCK_GEMINI_LOW)
    def test_low_risk_response(self, mock_gemini):
        response = client.post("/analyze", json={"input": "I have a mild headache and feel tired"})
        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"] == "LOW"
        assert isinstance(data["extracted_data"]["symptoms"], list)

    @patch("app.call_gemini", return_value=MOCK_GEMINI_ERROR)
    def test_gemini_error_returns_502(self, mock_gemini):
        response = client.post("/analyze", json={"input": "some health concern"})
        assert response.status_code == 502

    def test_missing_input_field_returns_422(self):
        response = client.post("/analyze", json={})
        assert response.status_code == 422

    def test_empty_string_input_returns_422(self):
        response = client.post("/analyze", json={"input": ""})
        assert response.status_code == 422

    def test_input_too_short_returns_422(self):
        response = client.post("/analyze", json={"input": "ab"})
        assert response.status_code == 422

    def test_input_too_long_returns_422(self):
        response = client.post("/analyze", json={"input": "x" * 2001})
        assert response.status_code == 422

    @patch("app.call_gemini", return_value=MOCK_GEMINI_LOW)
    def test_response_schema_shape(self, mock_gemini):
        response = client.post("/analyze", json={"input": "I feel dizzy and have a runny nose"})
        assert response.status_code == 200
        data = response.json()
        assert "extracted_data" in data
        assert "symptoms" in data["extracted_data"]
        assert "condition" in data["extracted_data"]
        assert "risk_level" in data
        assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH")
