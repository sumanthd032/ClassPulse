"""LLM integration — prompt building, API call, response parsing, Redis caching.

Architecture:
  - We use OpenAI's chat completions API (or Gemini as a drop-in alternative).
  - The LLM receives a structured prompt with: rubric criteria + level descriptors + student submission.
  - It must return a JSON array — one object per criterion.
  - We cache responses in Redis by SHA-256(content + rubric_id) to avoid duplicate calls.
  - Rate limiting: max 5 LLM calls per student per hour (checked via Redis).

Why JSON output?
  LLMs are good at generating structured JSON when instructed clearly.
  We parse the JSON and store each criterion's feedback separately so the UI can display
  criterion-by-criterion feedback aligned with the rubric.
"""

import hashlib
import json
import uuid
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

SYSTEM_PROMPT = """You are an academic feedback assistant. You evaluate student submissions against a rubric.
For each criterion, provide:
1. An estimated_score (integer, between 0 and max_marks)
2. strengths: what the student did well (1-2 sentences, encouraging tone)
3. improvements: specific, actionable steps to improve (1-3 sentences)
4. suggested_level: "excellent" | "good" | "average" | "poor"

Rules:
- Never say "wrong" — say "to improve, add X" instead.
- Be specific — reference the student's actual content.
- Output ONLY valid JSON. No explanation before or after.

Output format (JSON array, one object per criterion):
[
  {
    "criterion_id": "<uuid>",
    "estimated_score": <int>,
    "strengths": "<string>",
    "improvements": "<string>",
    "suggested_level": "<excellent|good|average|poor>"
  }
]"""


def _build_user_prompt(criteria: list[dict], submission_content: str) -> str:
    """Construct the user message that the LLM evaluates."""
    rubric_text = "\n".join([
        f"Criterion {i+1}: {c['name']} (max {c['max_marks']} marks)\n"
        f"  criterion_id: {c['id']}\n"
        f"  Excellent: {c['levels'].get('excellent', '')}\n"
        f"  Good: {c['levels'].get('good', '')}\n"
        f"  Average: {c['levels'].get('average', '')}\n"
        f"  Poor: {c['levels'].get('poor', '')}"
        for i, c in enumerate(criteria)
    ])
    return f"RUBRIC:\n{rubric_text}\n\nSTUDENT SUBMISSION:\n{submission_content}"


def _cache_key(content: str, rubric_id: str) -> str:
    """SHA-256 cache key — if content + rubric are identical, return cached feedback."""
    return "llm_cache:" + hashlib.sha256(f"{rubric_id}:{content}".encode()).hexdigest()


async def check_rate_limit(redis_client: aioredis.Redis, student_id: str) -> bool:
    """
    Sliding window rate limit: max 5 LLM calls per student per hour.
    Uses Redis INCR + EXPIRE pattern (not perfectly atomic but sufficient for this use case).
    Returns True if the call is allowed.
    """
    key = f"llm_rate:{student_id}"
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, 3600)   # TTL resets only on first call in window
    return count <= settings.llm_max_calls_per_student_per_hour


async def generate_feedback(
    criteria: list[dict],
    submission_content: str,
    submission_id: str,
    rubric_id: str,
) -> list[dict[str, Any]]:
    """
    Call the LLM and return parsed feedback objects.

    This function is called from the Celery worker — NOT from the FastAPI request handler.
    That means: this can be slow (up to 30s) without affecting API latency.

    Returns a list of dicts matching the JSON schema above.
    """
    # Try cache first
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    cache_key = _cache_key(submission_content, rubric_id)
    cached = await redis_client.get(cache_key)
    if cached:
        await redis_client.aclose()
        return json.loads(cached)

    try:
        result = await _call_openai(criteria, submission_content)
    except Exception as exc:
        await redis_client.aclose()
        raise exc

    # Cache for 1 hour
    await redis_client.setex(cache_key, 3600, json.dumps(result))
    await redis_client.aclose()
    return result


async def _call_openai(criteria: list[dict], submission_content: str) -> list[dict]:
    """Make the actual OpenAI API call. Isolated for easy mocking in tests."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.llm_api_key)
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(criteria, submission_content)},
        ],
        temperature=0.3,       # low temperature = more consistent, less creative output
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    parsed = json.loads(raw)
    # Handle both {"feedback": [...]} and [...] response shapes
    if isinstance(parsed, dict):
        parsed = parsed.get("feedback") or list(parsed.values())[0]
    return parsed
