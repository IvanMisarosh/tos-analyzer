from limits import RateLimitItemPerMinute
from limits.strategies import MovingWindowRateLimiter
from limits.storage import RedisStorage
from app.config import settings

REDIS_URL = settings.REDIS_URL

storage = RedisStorage(REDIS_URL)
limiter = MovingWindowRateLimiter(storage)

RATE_LIMIT = RateLimitItemPerMinute(settings.LLM_REQUESTS_PER_MINUTE)


def is_allowed(limit_key: str) -> bool:
    key = f"rate_limit:{limit_key}"
    return limiter.hit(RATE_LIMIT, key)
