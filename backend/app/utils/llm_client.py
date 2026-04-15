"""
Google Gemini API client (synchronous).

Used exclusively from Celery workers (which run in a separate sync process).
For async usage from FastAPI, call this in a thread-pool executor.
"""
import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def call_llm(system_prompt: str, user_prompt: str) -> list:
    """
    Calls the Gemini API and returns a parsed JSON list.

    Args:
        system_prompt: Instructions for the model (role, output format).
        user_prompt:   The actual content to evaluate.

    Returns:
        A Python list parsed from the model's JSON response.

    Raises:
        httpx.HTTPStatusError: If Gemini returns a non-200 status.
        json.JSONDecodeError:  If the response is not valid JSON.
        ValueError:            If the response structure is unexpected.
    """
    # Use the model from settings — never hardcode so we can swap models via .env
    model = settings.LLM_MODEL.strip()
    api_key = settings.LLM_API_KEY.strip().strip('"').strip("'")
    url = f"{_GEMINI_BASE}/{model}:generateContent?key={api_key}"

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            # Force the API to return raw JSON (no markdown fences)
            "responseMimeType": "application/json",
        },
    }

    with httpx.Client(timeout=45.0) as client:
        response = client.post(url, json=payload)

        if response.status_code != 200:
            if response.status_code == 429:
                logger.warning("Gemini API quota exceeded (429)")
            else:
                logger.error("Gemini API error %d: %s", response.status_code, response.text)
            response.raise_for_status()

        data = response.json()

    # Navigate the response structure
    try:
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise ValueError(f"Unexpected Gemini response structure: {exc}") from exc

    # Strip accidental markdown code fences (some models still add them)
    raw_text = raw_text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]

    parsed = json.loads(raw_text.strip())

    # The model sometimes wraps the array in a top-level dict key
    if isinstance(parsed, dict):
        for value in parsed.values():
            if isinstance(value, list):
                return value
        raise ValueError("LLM returned a dict without a list value")

    if not isinstance(parsed, list):
        raise ValueError(f"Expected a JSON array from LLM, got: {type(parsed)}")

    return parsed
