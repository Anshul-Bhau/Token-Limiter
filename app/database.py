from sqlalchemy.ext.asyncio import (
    create_async_engine, 
    AsyncSession,
    async_sessionmaker,
)

from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Create async engine
# pool_pre_pings = True : test connections before use (handles MySQL timeouts)
engine = create_async_engine(
    settings.MYSQL_URL,
    echo=settings.APP_ENV == "development", # Log SQL in dev only
    pool_pre_ping = True,
    pool_size = 10,
    max_overflow = 20,
)

# Session
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, 
)

# Base class
class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

