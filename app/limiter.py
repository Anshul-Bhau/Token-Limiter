import time
import uuid

from app.redis_client import redis, LUA_SCRIPTS
from app.config import settings

async def get_client_config(client_key: str) -> dict:
    """Redis cache and MySQL fallback"""
    cache_key = f"config_cache:{client_key}"
    import json

    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # MySQL fallback
    from app.database import AsyncSessionLocal
    from app.models import ClientConfig
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ClientConfig).where(ClientConfig.client_key == client_key))
    row = result.scalar_one_or_none()

    if row:
        config = {
            "max_tokens" : row.max_tokens,
            "refill_rate" : row.refill_rate,
            "window_size" : row.window_size,
            "algorithm" : row.algorithm,
        }
    else:
        onfig = {
            "max_tokens" : settings.DEFAULT_MAX_TOKENS,
            "refill_rate" : settings.DEFAULT_REFILL_RATE,
            "window_size" : settings.DEFAULT_WINDOW_SIZE,
            "algorithm" : settings.DEFAULT_ALGORITHM,
        }
    
    await redis.setex(cache_key, 
                    settings.CONFIG_CACHE_TTL,
                    json.dumps(config))
    
    return config

async def check_rate_limit(client_key: str) -> tuple[bool, float]:
    """Returns (allowed, tokens_remaining)"""
    config = await get_client_config(client_key)

    if config["algorithm"] == "token_bucket":
        token_keys = f"bucket:{client_key}:tokens"
        last_refill_key = f"bucket:{client_key}:last_refill"
        now = time.time()

        result = await redis.evalsha(
            LUA_SCRIPTS["token_bucket"],
            2,
            token_keys,
            last_refill_key,
            str(now),
            str(config["max_tokens"]),
            str(config["refill_rate"]),
        )
        allowed = bool(int(result[0]))
        remaining = float(result[1])
    
    else: # sliding window
        key = f"slidingwindow:{client_key}"
        now = time.time()

        result = await redis.evalsha(
            LUA_SCRIPTS["sliding_window"],
            1,
            key,
            str(now),
            str(config["window_size"]),
            str(config["max_tokens"]),
            str(uuid.uuid4)
        )
        allowed = bool(int(result[0]))
        remaining = float(result[1])

    await _increment_stats(client_key, allowed)
    return allowed, remaining

async def _increment_stats(client_key: str, allowed: bool):
    pipe = redis.pipeline()
    pipe.incr(f"stats:{client_key}:total")
    if allowed:
        pipe.incr(f"stats{client_key}:allowed")
    else:
        pipe.incr(f"stats{client_key}:denied")
    await pipe.execute()
    



# evalsha format - 
# redis.evalsha(
#     sha,
#     numkeys,
#     key1,
#     key2,
#     ...,
#     arg1,
#     arg2,
#     ...
# )