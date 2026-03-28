"""
google_cloud.py
Google Cloud service integrations for IntentBridge AI.
Handles: Cloud Logging, Secret Manager, Maps Places API.
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_client_logging: Optional["google.cloud.logging.Client"] = None
_client_secret: Optional["google.cloud.secretmanager.SecretManagerServiceClient"] = None


def setup_cloud_logging() -> Optional["google.cloud.logging.Client"]:
    global _client_logging
    if _client_logging is not None:
        return _client_logging

    try:
        import google.cloud.logging

        _client_logging = google.cloud.logging.Client()
        _client_logging.setup_logging(log_level=logging.INFO)
        logger.info("Cloud Logging initialized successfully")
        return _client_logging
    except Exception as e:
        logger.warning("Cloud Logging not available: %s", e)
        return None


def get_secret(secret_id: str, project_id: str) -> Optional[str]:
    global _client_secret
    try:
        from google.cloud import secretmanager

        if _client_secret is None:
            _client_secret = secretmanager.SecretManagerServiceClient()

        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = _client_secret.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.warning("Failed to retrieve secret '%s': %s", secret_id, e)
        return None


def get_gemini_api_key(project_id: str) -> Optional[str]:
    api_key = get_secret("GEMINI_API_KEY", project_id)
    if api_key:
        logger.info("GEMINI_API_KEY retrieved from Secret Manager")
    return api_key


def get_places_api_key(project_id: str) -> Optional[str]:
    api_key = get_secret("PLACES_API_KEY", project_id)
    if api_key:
        logger.info("PLACES_API_KEY retrieved from Secret Manager")
    return api_key


@dataclass
class HospitalResult:
    name: str
    address: str
    rating: Optional[float]
    place_id: Optional[str]
    link: str
    open_now: Optional[bool]


def find_nearby_hospitals(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    api_key: Optional[str] = None,
    location: str = "current location",
    max_results: int = 3,
) -> list[dict]:
    """
    Find nearby hospitals using Google Places API.

    Args:
        lat: Latitude (optional, uses location if not provided)
        lng: Longitude
        api_key: Google Maps API key
        location: Human-readable location name
        max_results: Max number of hospitals to return

    Returns:
        List of hospital dicts with name, address, rating, link
    """
    if not api_key:
        logger.debug("No Places API key provided, skipping hospital search")
        return []

    base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    if lat is not None and lng is not None:
        params = {
            "location": f"{lat},{lng}",
            "radius": 10000,
            "type": "hospital",
            "key": api_key,
        }
    else:
        params = {
            "query": "hospitals",
            "location": location,
            "radius": 10000,
            "key": api_key,
        }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()

        status = data.get("status", "UNKNOWN")
        if status not in ("OK", "ZERO_RESULTS"):
            logger.warning("Places API error: %s", status)
            return []

        hospitals = []
        for place in data.get("results", [])[:max_results]:
            place_id = place.get("place_id", "")
            hospitals.append(
                {
                    "name": place.get("name", "Unknown Hospital"),
                    "address": place.get("vicinity")
                    or place.get("formatted_address", ""),
                    "rating": place.get("rating"),
                    "link": f"https://www.google.com/maps/place/?api=1&query_place_id={place_id}",
                    "open_now": place.get("opening_hours", {}).get("open_now"),
                }
            )

        return hospitals

    except requests.RequestException as e:
        logger.error("Network error finding hospitals: %s", e)
        return []
    except Exception as e:
        logger.error("Error finding hospitals: %s", e)
        return []
