"""
tests/test_app.py
Integration tests for the FastAPI /analyze endpoint.
Uses TestClient (no real Gemini calls — Gemini is mocked).
"""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("GEMINI_API_KEY", "test-key-placeholder")

from app import app

client = TestClient(app)


MOCK_GEMINI_HIGH = {
    "symptoms": ["chest pain", "shortness of breath"],
    "condition": "possible cardiac event",
    "risk_level": "HIGH",
    "error": None,
}

MOCK_GEMINI_LOW = {
    "symptoms": ["mild headache", "tiredness"],
    "condition": "common cold",
    "risk_level": "LOW",
    "error": None,
}

MOCK_GEMINI_ERROR = {
    "symptoms": [],
    "condition": "",
    "risk_level": "LOW",
    "error": "Gemini API timeout",
}


class TestHealthCheck:
    def test_health_returns_ok(self) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "IntentBridge AI"

    def test_health_returns_version(self) -> None:
        response = client.get("/health")
        assert "version" in response.json()


class TestAnalyzeEndpoint:
    @patch("app.call_gemini", return_value=MOCK_GEMINI_HIGH)
    def test_high_risk_response(self, mock_gemini: patch) -> None:
        response = client.post(
            "/analyze", json={"input": "I have chest pain and can't breathe"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"] == "HIGH"
        assert "chest pain" in data["extracted_data"]["symptoms"]
        assert data["extracted_data"]["condition"] == "possible cardiac event"

    @patch("app.call_gemini", return_value=MOCK_GEMINI_LOW)
    def test_low_risk_response(self, mock_gemini: patch) -> None:
        response = client.post(
            "/analyze", json={"input": "I have a mild headache and feel tired"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"] == "LOW"
        assert isinstance(data["extracted_data"]["symptoms"], list)

    @patch("app.call_gemini", return_value=MOCK_GEMINI_ERROR)
    def test_gemini_error_returns_502(self, mock_gemini: patch) -> None:
        response = client.post("/analyze", json={"input": "some health concern"})
        assert response.status_code == 502

    def test_missing_input_field_returns_422(self) -> None:
        response = client.post("/analyze", json={})
        assert response.status_code == 422

    def test_empty_string_input_returns_422(self) -> None:
        response = client.post("/analyze", json={"input": ""})
        assert response.status_code == 422

    def test_input_too_short_returns_422(self) -> None:
        response = client.post("/analyze", json={"input": "ab"})
        assert response.status_code == 422

    def test_input_too_long_returns_422(self) -> None:
        response = client.post("/analyze", json={"input": "x" * 2001})
        assert response.status_code == 422

    @patch("app.call_gemini", return_value=MOCK_GEMINI_LOW)
    def test_response_schema_shape(self, mock_gemini: patch) -> None:
        response = client.post(
            "/analyze", json={"input": "I feel dizzy and have a runny nose"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "extracted_data" in data
        assert "symptoms" in data["extracted_data"]
        assert "condition" in data["extracted_data"]
        assert "risk_level" in data
        assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH")

    @patch("app.call_gemini", return_value=MOCK_GEMINI_LOW)
    def test_ui_endpoint_returns_html(self, mock_gemini: patch) -> None:
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestHospitalsEndpoint:
    @patch("app.find_nearby_hospitals", return_value=[])
    def test_hospitals_returns_empty_list(self, mock_hospitals: patch) -> None:
        response = client.get("/hospitals")
        assert response.status_code == 200
        assert response.json() == []

    @patch(
        "app.find_nearby_hospitals",
        return_value=[
            {
                "name": "Test Hospital",
                "address": "123 Test St",
                "rating": 4.5,
                "link": "https://maps.google.com/test",
                "open_now": True,
            }
        ],
    )
    def test_hospitals_returns_results(self, mock_hospitals: patch) -> None:
        response = client.get("/hospitals", params={"location": "New York"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Hospital"
        assert data[0]["rating"] == 4.5

    @patch(
        "app.find_nearby_hospitals",
        return_value=[
            {
                "name": "Hospital A",
                "address": "A",
                "rating": None,
                "link": "",
                "open_now": None,
            },
            {
                "name": "Hospital B",
                "address": "B",
                "rating": None,
                "link": "",
                "open_now": None,
            },
        ],
    )
    def test_hospitals_with_coordinates(self, mock_hospitals: patch) -> None:
        response = client.get("/hospitals", params={"lat": 40.7128, "lng": -74.0060})
        assert response.status_code == 200
        assert len(response.json()) == 2
