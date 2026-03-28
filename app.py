"""
app.py
IntentBridge AI — FastAPI entry point with Google Cloud integration.
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from starlette.requests import Request

from gemini_service import call_gemini
from google_cloud import (
    find_nearby_hospitals,
    get_places_api_key,
    setup_cloud_logging,
)
from utils.validators import is_meaningful_input, sanitize_input, validate_input_length

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_cloud_logging()
    logger.info("IntentBridge AI started")
    yield
    logger.info("IntentBridge AI shutdown")


app = FastAPI(
    title="IntentBridge AI",
    description=(
        "Gemini-powered symptom extraction and risk triage API.\n\n"
        "**Version 1 baseline** — Enhancements will be added using Google Antigravity."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


class ExtractedData(BaseModel):
    symptoms: list[str]
    condition: str


class HospitalInfo(BaseModel):
    name: str
    address: str
    rating: Optional[float] = None
    link: str
    open_now: Optional[bool] = None


class AnalyzeRequest(BaseModel):
    input: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Unstructured user text describing symptoms or health concerns.",
        examples=["I have had a headache and fever for two days and feel very tired."],
    )


class AnalyzeResponse(BaseModel):
    extracted_data: ExtractedData
    risk_level: str
    maps_link: Optional[str] = None
    hospitals: Optional[list[HospitalInfo]] = None


@app.get("/", tags=["UI"])
def serve_ui() -> HTMLResponse:
    """Serves the main application frontend interface."""
    html_path = Path(__file__).parent / "templates" / "index.html"
    if not html_path.exists():
        return JSONResponse(
            status_code=404, content={"error": "UI template not found."}
        )
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"), status_code=200)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, Any]:
    """Service health check."""
    return {
        "status": "ok",
        "service": "IntentBridge AI",
        "version": "1.0.0",
    }


@app.post("/analyze", response_model=AnalyzeResponse, tags=["Triage"])
def analyze(payload: AnalyzeRequest) -> JSONResponse | AnalyzeResponse:
    """
    Analyze unstructured user text using Gemini.

    Returns extracted symptoms, a possible condition, and a risk level
    (LOW / MEDIUM / HIGH) determined by keyword-based rule logic.
    """
    try:
        clean_input = sanitize_input(payload.input)

        length_error = validate_input_length(clean_input)
        if length_error:
            raise HTTPException(status_code=422, detail=length_error)

        if not is_meaningful_input(clean_input):
            raise HTTPException(
                status_code=422,
                detail="Input must contain at least one meaningful word.",
            )

        logger.info("Processing /analyze request.")

        gemini_result = call_gemini(clean_input)

        if gemini_result.get("error"):
            logger.error("Gemini error: %s", gemini_result["error"])
            return JSONResponse(status_code=502, content=gemini_result)

        symptoms: list[str] = gemini_result["symptoms"]
        condition: str = gemini_result["condition"]
        risk_level: str = gemini_result.get("risk_level", "LOW")

        maps_link: Optional[str] = None
        hospitals: Optional[list[HospitalInfo]] = None

        if risk_level in ("MEDIUM", "HIGH"):
            maps_link = "https://www.google.com/maps/search/hospitals+near+me"
            places_api_key = os.getenv("PLACES_API_KEY")
            if not places_api_key and PROJECT_ID:
                places_api_key = get_places_api_key(PROJECT_ID)

            nearby = find_nearby_hospitals(api_key=places_api_key, max_results=3)
            if nearby:
                hospitals = [HospitalInfo(**h) for h in nearby]

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input": clean_input,
            "symptoms": symptoms,
            "condition": condition,
            "risk_level": risk_level,
        }
        with open(LOG_DIR / "requests.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

        logger.info(
            "Analysis complete — risk_level=%s, symptoms=%d", risk_level, len(symptoms)
        )

        return AnalyzeResponse(
            extracted_data=ExtractedData(symptoms=symptoms, condition=condition),
            risk_level=risk_level,
            maps_link=maps_link,
            hospitals=hospitals,
        )

    except HTTPException:
        raise
    except (ValueError, RuntimeError) as exc:
        logger.error("Expected error in /analyze endpoint: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "symptoms": [],
                "condition": "Unknown",
                "risk_level": "LOW",
                "error": "Internal Server Error",
            },
        )


@app.get("/hospitals", response_model=list[HospitalInfo], tags=["Maps"])
def get_hospitals(
    lat: Optional[float] = Query(None, description="Latitude"),
    lng: Optional[float] = Query(None, description="Longitude"),
    location: Optional[str] = Query(
        None, description="Location name (e.g., 'New York')"
    ),
) -> list[HospitalInfo]:
    """
    Find nearby hospitals using Google Places API.

    Provide either lat/lng coordinates or a location name.
    """
    places_api_key = os.getenv("PLACES_API_KEY")
    if not places_api_key and PROJECT_ID:
        places_api_key = get_places_api_key(PROJECT_ID)

    search_location = location or "current location"
    hospitals = find_nearby_hospitals(
        lat=lat,
        lng=lng,
        api_key=places_api_key,
        location=search_location,
        max_results=5,
    )

    return [HospitalInfo(**h) for h in hospitals]


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
