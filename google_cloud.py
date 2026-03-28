"""
google_cloud.py
Google Cloud service integrations for IntentBridge AI.
Handles: Cloud Logging, Secret Manager, Maps Places API.
"""

import os
import logging
from typing import Optional

import google.cloud.logging
from google.cloud import secretmanager
import requests

logger = logging.getLogger(__name__)

_client_logging = None
_client_secret = None


def setup_cloud_logging() -> google.cloud.logging.Client:
    global _client_logging
    if _client_logging is None:
        try:
            _client_logging = google.cloud.logging.Client()
            _client_logging.setup_logging(log_level=logging.INFO)
            logger.info("Cloud Logging initialized successfully")
        except Exception as e:
            logger.warning(f"Cloud Logging not available: {e}")
            return None
    return _client_logging


def get_secret(secret_id: str, project_id: str) -> Optional[str]:
    global _client_secret
    try:
        if _client_secret is None:
            _client_secret = secretmanager.SecretManagerServiceClient()

        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = _client_secret.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.warning(f"Failed to retrieve secret '{secret_id}': {e}")
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
        return []

    base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    if lat and lng:
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

        if data.get("status") != "OK" and data.get("status") != "ZERO_RESULTS":
            logger.warning(f"Places API error: {data.get('status')}")
            return []

        hospitals = []
        for place in data.get("results", [])[:max_results]:
            hospitals.append(
                {
                    "name": place.get("name", "Unknown Hospital"),
                    "address": place.get(
                        "vicinity", place.get("formatted_address", "")
                    ),
                    "rating": place.get("rating"),
                    "place_id": place.get("place_id"),
                    "link": f"https://www.google.com/maps/place/?api=1&query=Google&query_place_id={place.get('place_id')}",
                    "open_now": place.get("opening_hours", {}).get("open_now"),
                }
            )

        return hospitals

    except Exception as e:
        logger.error(f"Error finding hospitals: {e}")
        return []
