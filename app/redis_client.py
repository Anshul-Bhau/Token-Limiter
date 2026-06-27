import redis.asyncio as aioredis
from pathlib import Path
from app.config import settings


# Initialized at startup
redis : aioredis = None

LUA_SCRIPTS = {}

async def init_redis():
    """Called from FastAPI lifespan on startup"""
    global redis
    redis = await aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_response=True,
        max_connections=50,
    )
    await load_lua_scripts()


async def close_redis():
    """Called from FastAPI Lifespan on shutdown"""
    if redis:
        await redis.aclose()
    

async def load_lua_scripts():
    """
    Load Lua scripts into Redis using SCRIPT LOAD.
    Returns SHA hash 
    """
    script_dir = Path("scripts/lua")
    for script_file in script_dir.glob("*.lua"):
        script_text = script_file.read_text()
        sha = await redis.script_load(script_text)
        LUA_SCRIPTS[script_file.stem] = sha
        print(f"Loaded Lua script: {script_file.stem} → {sha[:8]}...")

def get_redis() -> aioredis.Redis:
    """FastAPI dependency - returns the shared Redis client"""
    return redis