# neeeds performance changes

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.redis_client import get_redis
import redis

router = APIRouter()

@router.get("/stats")
async def stats():
    r = get_redis()
    cursor = 0
    while True:
        cursor, keys = await redis.scan(
            cursor,
            match="stats:*:total"
        )
    result = []

    for key in keys:
        client_key = key.split(":")[1]
        total   = await r.get(f"stats:{client_key}:total")   or 0
        allowed = await r.get(f"stats:{client_key}:allowed") or 0
        denied  = await r.get(f"stats:{client_key}:denied")  or 0
        tokens  = await r.get(f"bucket:{client_key}:tokens") or "?"

        result.append({
            "client_key": client_key,
            "total":      int(total),
            "allowed":    int(allowed),
            "denied":     int(denied),
            "tokens":     tokens,
        })

    result.sort(key=lambda x: x["total"], reverse=True)
    return JSONResponse(result)


@router.get("/dashboard")
async def dashboard():
    # Simple redirect to /stats for now
    # Replace with TemplateResponse once you add dashboard.html
    return JSONResponse({"message": "hit /stats for live data"})