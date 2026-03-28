"""
app.py
IntentBridge AI — FastAPI entry point (Version 1 baseline).
"""

import logging
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from gemini_service import call_gemini
from utils.validators import sanitize_input, validate_input_length, is_meaningful_input

# ── Logging setup ─────────────────────────────────────────────────────────────
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


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="IntentBridge AI",
    description=(
        "Gemini-powered symptom extraction and risk triage API.\n\n"
        "**Version 1 baseline** — Enhancements will be added using Google Antigravity."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Schemas ───────────────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    input: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Unstructured user text describing symptoms or health concerns.",
        examples=["I have had a headache and fever for two days and feel very tired."],
    )


class ExtractedData(BaseModel):
    symptoms: list[str]
    condition: str


class AnalyzeResponse(BaseModel):
    extracted_data: ExtractedData
    risk: str
    maps_link: Optional[str] = None


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def health_check():
    """Service health check."""
    return {
        "status": "ok",
        "service": "IntentBridge AI",
        "version": "1.0.0",
    }


@app.post("/analyze", response_model=AnalyzeResponse, tags=["Triage"])
def analyze(payload: AnalyzeRequest):
    """
    Analyze unstructured user text using Gemini.

    Returns extracted symptoms, a possible condition, and a risk level
    (LOW / MEDIUM / HIGH) determined by keyword-based rule logic.
    """
    # ── Input sanitization & validation ──────────────────────────────────────
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

    # ── Gemini extraction ─────────────────────────────────────────────────────
    gemini_result = call_gemini(clean_input)

    if gemini_result["error"]:
        logger.error("Gemini error: %s", gemini_result["error"])
        raise HTTPException(
            status_code=502,
            detail="Failed to process input with Gemini. Please try again.",
        )

    symptoms: list[str] = gemini_result["symptoms"]
    condition: str = gemini_result["condition"]

    # ── Risk classification ───────────────────────────────────────────────────
    risk = gemini_result.get("risk_level", "LOW")

    maps_link = "https://www.google.com/maps/search/hospitals+near+me" if risk == "HIGH" else None

    # ── Structured request log ────────────────────────────────────────────────
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input": clean_input,
        "symptoms": symptoms,
        "condition": condition,
        "risk": risk,
    }
    with open(LOG_DIR / "requests.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    logger.info("Analysis complete — risk=%s, symptoms=%d", risk, len(symptoms))

    return AnalyzeResponse(
        extracted_data=ExtractedData(symptoms=symptoms, condition=condition),
        risk=risk,
        maps_link=maps_link,
    )
