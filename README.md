# IntentBridge AI

A minimal, production-ready FastAPI backend powered by Google Gemini.
Converts unstructured user text into structured health insights and a risk classification.

> **Note:** This is Version 1 baseline. Enhancements will be added using Google Antigravity.

---

## Project Structure

```
intentbridge-ai/
├── app.py                  # FastAPI entry point & /analyze endpoint
├── gemini_service.py       # Google Gemini API client & prompt logic
├── decision_engine.py      # Keyword-based risk classification (LOW/MEDIUM/HIGH)
├── utils/
│   ├── __init__.py
│   └── validators.py       # Input sanitization & validation helpers
├── tests/
│   ├── __init__.py
│   ├── test_decision_engine.py
│   └── test_app.py
├── logs/                   # Runtime & request logs (auto-created, git-ignored)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Prerequisites

- Python 3.10+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)

---

## Setup & Run Locally

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd intentbridge-ai

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Open .env and set your GEMINI_API_KEY

# 5. Start the server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

---

## API Reference

### `GET /`
Health check.

**Response:**
```json
{ "status": "ok", "service": "IntentBridge AI", "version": "1.0.0" }
```

---

### `POST /analyze`

Analyze unstructured user text and return extracted health insights + risk level.

**Request:**
```json
{
  "input": "I've had a bad headache and fever for two days and can't keep food down."
}
```

**Response:**
```json
{
  "extracted_data": {
    "symptoms": ["headache", "fever", "nausea"],
    "condition": "possible gastroenteritis"
  },
  "risk_level": "MEDIUM"
}
```

**Risk Levels:**

| Value  | Meaning                              |
|--------|--------------------------------------|
| LOW    | Mild or non-urgent symptoms          |
| MEDIUM | Moderate symptoms, monitoring needed |
| HIGH   | Urgent — seek medical care promptly  |

**Validation:**
- `input` must be 3–2000 characters
- `input` must contain at least one meaningful word

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Interactive API Docs

Once the server is running:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:**       `http://localhost:8000/redoc`

---

## Environment Variables

| Variable        | Required | Description                   |
|-----------------|----------|-------------------------------|
| `GEMINI_API_KEY` | ✅ Yes  | Your Google Gemini API key    |

---

## Notes

- All requests are logged to `logs/requests.jsonl` (JSON Lines format).
- No database, no frontend, no heavy dependencies.
- Version 1 baseline — intentionally minimal and readable.
