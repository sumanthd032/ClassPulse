"""
Async Redis client — used for:
  - Refresh token storage (auth)
  - LLM rate-limit counters per student
  - LLM response cache (content-hash keyed)
  - WebSocket notification fan-out (via Redis pub/sub in the WS manager)
"""
import redis.asyncio as aioredis

from app.config import settings

# A single shared async connection pool.
# decode_responses=True: all values come back as Python str, not bytes.
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_redis() -> aioredis.Redis:
    """FastAPI dependency: returns the shared Redis client."""
    return redis_client
