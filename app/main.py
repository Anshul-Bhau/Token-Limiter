from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from app.redis_client import init_redis, close_redis
from app.database import engine
from app.models import Base
from app.routers import check, admin
from app.dashboard import routes as dashborad_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---STARTUP--------------
    print("[startup] Connecting to Redis...")
    await init_redis()

    print("[startup] Running DB migrations...")
    # Create tables directly (dev). In prod: run alembic upgrade head as pre-start
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("[startup] Ready")
    yield

    # ---SHUTDOWN-------------
    print("[shutdown] Closing Redis...")
    await close_redis()


app = FastAPI(
    title="Token Bucket Rate Limiter",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(check.router, tags=["Rate Limit"])
app.include_router(admin.router, tags=["Admin"])
app.include_router(dashborad_routes.router, tags=["Dashboard"])

@app.get("/")
async def health():
    return {"status" : "ok", 
            "service": "rate-limiter"}
