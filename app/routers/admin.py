from fastapi import APIRouter, Header, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.mysql import insert
from app.schemas import AdminRequest, AdminResponse
from app.database import get_db
from app.models import ClientConfig
from app.redis_client import get_redis
from app.config import settings

router = APIRouter()

@router.post("/admin/limits", response_model=AdminResponse)
async def set_limits(
    request: AdminRequest,
    x_admin_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    if x_admin_key != settings.ADMIN_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key")
    
    # Upsert into MySQL
    stmt = insert(ClientConfig).values(
        client_key  = request.client_key,
        max_tokens  = request.max_tokens,
        refill_rate = request.refill_rate,
        window_size = request.window_size,
        algorithm   = request.algorithm,
    ).on_duplicate_key_update(
        max_tokens  = request.max_tokens,
        refill_rate = request.refill_rate,
        window_size = request.window_size,
        algorithm   = request.algorithm,
    )
    await db.execute(stmt)
    await db.commit()

    # INvalidate Redis Cache
    r = get_redis()
    await r.delete(f"config_cache:{request.client_key}")
    await r.delete(f"bucket:{request.client_key}:tokens")
    await r.delete(f"bucket:{request.client_key}:last_refill")

    return AdminResponse(status="updated", client_key=request.client_key)